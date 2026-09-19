"""Logica de OpenRouter compartida: modelos, llamadas a la API, usage y logs .md.

Extraido de la version CLI original de chat.py para que tanto un backend web
como un script de linea de comandos puedan reusar la misma logica de negocio.
"""
import datetime
import json
import os
import pathlib
import re

import requests

ROOT = pathlib.Path(__file__).parent
LOGS_DIR = ROOT / "logs"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

MISSION_TEXT = (ROOT / "mission.md").read_text(encoding="utf-8")
RUBRIC_TEXT = (ROOT / "rubric.md").read_text(encoding="utf-8")
# Claude Haiku 4.5+ solo cachea bloques de >= 4096 tokens; mission.md solo no
# alcanza (~3400 tokens), asi que se suma rubric.md para superar el piso.
CACHED_REFERENCE_TEXT = MISSION_TEXT + "\n\n" + RUBRIC_TEXT

MODELS = {
    "1": {
        "id": "openai/gpt-5.6-luna",
        "slug": "gpt-5.6-luna",
        "label": "GPT-5.6 Luna",
        "capability": "Effort configurable",
        "supports_effort": True,
        "default_effort": "medium",
    },
    "2": {
        "id": "anthropic/claude-haiku-4.5",
        "slug": "claude-haiku-4.5",
        "label": "Claude Haiku 4.5",
        "capability": "Prompt caching",
        "static_context": True,
    },
    "3": {
        "id": "google/gemini-3.7-flash",
        "slug": "gemini-3.7-flash",
        "label": "Gemini 3.7 Flash",
        "capability": "Salidas estructuradas",
        "structured_output": True,
    },
    "4": {
        "id": "deepseek/deepseek-v4-flash-0731",
        "slug": "deepseek-v4-flash-0731",
        "label": "DeepSeek v4 Flash",
        "capability": "El escalon barato",
    },
}

JSON_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "respuesta_estructurada",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "respuesta": {
                    "type": "string",
                    "description": "La respuesta completa a lo que pidio el usuario",
                },
                "resumen": {
                    "type": "string",
                    "description": "Un resumen de una linea de la respuesta",
                },
            },
            "required": ["respuesta", "resumen"],
            "additionalProperties": False,
        },
    },
}


def load_api_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            if k.strip() == "OPENROUTER_API_KEY":
                return v.strip().strip('"').strip("'")
    return None


def call_openrouter(api_key, model_id, messages, reasoning_effort=None, structured=False):
    body = {"model": model_id, "messages": messages, "usage": {"include": True}}
    if reasoning_effort and reasoning_effort != "off":
        body["reasoning"] = {"effort": reasoning_effort}
    if structured:
        body["response_format"] = JSON_SCHEMA
    resp = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": "Mision3 - chat minimo",
        },
        data=json.dumps(body),
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def format_usage(usage):
    usage = usage or {}
    prompt_details = usage.get("prompt_tokens_details") or {}
    completion_details = usage.get("completion_tokens_details") or {}
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)
    reasoning_tokens = completion_details.get("reasoning_tokens", 0)
    cached_tokens = prompt_details.get("cached_tokens", 0)
    cost = usage.get("cost", 0)
    cache_discount = usage.get("cache_discount")
    line = (
        f"input={prompt_tokens} output={completion_tokens} "
        f"reasoning={reasoning_tokens} cached={cached_tokens} cost=${cost}"
    )
    if cache_discount is not None:
        line += f" cache_discount={cache_discount}"
    return line, {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "reasoning_tokens": reasoning_tokens,
        "cached_tokens": cached_tokens,
        "cost": cost,
        "cache_discount": cache_discount,
    }


def new_log(model):
    LOGS_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = LOGS_DIR / f"{model['slug']}_{ts}.md"
    header = (
        f"# Conversacion — {model['id']}\n\n"
        f"Inicio: {datetime.datetime.now().isoformat()}\n"
    )
    path.write_text(header, encoding="utf-8")
    return path


def append_log(path, role, content, usage_line=None):
    ts = datetime.datetime.now().isoformat()
    with path.open("a", encoding="utf-8") as f:
        f.write(f"\n## {role} ({ts})\n\n{content}\n")
        if usage_line:
            f.write(f"\n**Usage:** {usage_line}\n")


LOG_NAME_RE = re.compile(r"^(?P<slug>.+)_(?P<ts>\d{8}_\d{6})\.md$")
TURN_RE = re.compile(r"## (user|assistant) \([^)]*\)\n\n(.*?)(?=\n## |\Z)", re.S)
USAGE_RE = re.compile(
    r"input=(\d+) output=(\d+) reasoning=(\d+) cached=(\d+) cost=\$([0-9.eE+-]+)"
)


def list_logs():
    """Conversaciones guardadas en logs/, agrupadas por slot de modelo."""
    LOGS_DIR.mkdir(exist_ok=True)
    slug_to_slot = {m["slug"]: slot for slot, m in MODELS.items()}
    by_slot = {slot: [] for slot in MODELS}
    for path in LOGS_DIR.glob("*.md"):
        match = LOG_NAME_RE.match(path.name)
        if not match:
            continue
        slot = slug_to_slot.get(match["slug"])
        if not slot:
            continue
        by_slot[slot].append(
            {"file": path.name, "started_at": match["ts"], "preview": _log_preview(path)}
        )
    for entries in by_slot.values():
        entries.sort(key=lambda e: e["started_at"], reverse=True)
    return by_slot


def _log_preview(path):
    text = path.read_text(encoding="utf-8")
    match = TURN_RE.search(text)
    if not match:
        return "(vacio)"
    line = match.group(2).strip().splitlines()[0]
    return (line[:60] + "…") if len(line) > 60 else line


def load_log(filename):
    """Reconstruye una conversacion guardada para poder seguir chateando."""
    path = LOGS_DIR / pathlib.Path(filename).name
    if not path.is_file():
        return None

    text = path.read_text(encoding="utf-8")
    history = []
    for turn in TURN_RE.finditer(text):
        role, raw = turn.group(1), turn.group(2)
        content = raw.split("\n**Usage:**")[0].strip()
        entry = {"role": role, "content": content}
        usage_match = USAGE_RE.search(raw)
        if usage_match:
            entry["usage"] = {
                "prompt_tokens": int(usage_match[1]),
                "completion_tokens": int(usage_match[2]),
                "reasoning_tokens": int(usage_match[3]),
                "cached_tokens": int(usage_match[4]),
                "cost": float(usage_match[5]),
            }
        history.append(entry)
    return path, history


def build_messages(model, history, reasoning_effort):
    if model.get("static_context"):
        system = {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Sos un asistente util. A continuacion tenes como contexto "
                        "de referencia el enunciado completo de la mision y su rubrica "
                        "de correccion, para poder responder preguntas sobre ellos si "
                        "te las hacen:\n\n" + CACHED_REFERENCE_TEXT
                    ),
                    "cache_control": {"type": "ephemeral"},
                }
            ],
        }
        return [system] + history
    return history
