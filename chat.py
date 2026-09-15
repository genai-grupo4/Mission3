#!/usr/bin/env python3
"""Chat CLI sobre OpenRouter: sirve 4 modelos, muestra usage y guarda logs .md."""
import datetime
import json
import os
import pathlib
import sys

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
        "label": "GPT-5.6 Luna — effort configurable",
        "supports_effort": True,
        "default_effort": "medium",
    },
    "2": {
        "id": "anthropic/claude-haiku-4.5",
        "slug": "claude-haiku-4.5",
        "label": "Claude Haiku 4.5 — prompt caching",
        "static_context": True,
    },
    "3": {
        "id": "google/gemini-3.7-flash",
        "slug": "gemini-3.7-flash",
        "label": "Gemini 3.7 Flash — salidas estructuradas",
        "structured_output": True,
    },
    "4": {
        "id": "deepseek/deepseek-v4-flash-0731",
        "slug": "deepseek-v4-flash-0731",
        "label": "DeepSeek v4 Flash — el escalon barato",
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


def print_help():
    print(
        "Comandos: /modelo (cambiar de modelo, arranca conversacion nueva), "
        "/reasoning <low|medium|high|off> (ajustar esfuerzo de razonamiento), "
        "/salir (terminar)"
    )


def choose_model():
    print("\nElegi un modelo:")
    for key, m in MODELS.items():
        print(f"  {key}) {m['label']}  [{m['id']}]")
    while True:
        choice = input("> ").strip()
        if choice in MODELS:
            return MODELS[choice]
        print("Opcion invalida.")


def main():
    api_key = load_api_key()
    if not api_key:
        print(
            "Falta OPENROUTER_API_KEY. Definila como variable de entorno o en un "
            "archivo .env (ver .env.example)."
        )
        sys.exit(1)

    print("=== Chat OpenRouter - Mision: el prompt minimo ===")
    model = choose_model()
    reasoning_effort = model.get("default_effort") if model.get("supports_effort") else None
    history = []
    log_path = new_log(model)
    print(f"\nNueva conversacion iniciada. Log: {log_path}")
    print_help()

    while True:
        try:
            user_input = input("\nVos: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nChau.")
            break
        if not user_input:
            continue

        if user_input == "/salir":
            print("Chau.")
            break

        if user_input == "/modelo":
            model = choose_model()
            reasoning_effort = model.get("default_effort") if model.get("supports_effort") else None
            history = []
            log_path = new_log(model)
            print(f"\nNueva conversacion iniciada. Log: {log_path}")
            continue

        if user_input.startswith("/reasoning"):
            parts = user_input.split()
            if len(parts) == 2 and parts[1] in ("low", "medium", "high", "off"):
                reasoning_effort = parts[1]
                print(f"Reasoning effort ajustado a: {reasoning_effort}")
            else:
                print("Uso: /reasoning <low|medium|high|off>")
            continue

        history.append({"role": "user", "content": user_input})
        append_log(log_path, "user", user_input)

        messages = build_messages(model, history, reasoning_effort)
        try:
            data = call_openrouter(
                api_key,
                model["id"],
                messages,
                reasoning_effort=reasoning_effort,
                structured=model.get("structured_output", False),
            )
        except requests.exceptions.RequestException as e:
            print(f"Error llamando a OpenRouter: {e}")
            history.pop()
            continue

        choice = data["choices"][0]["message"]
        assistant_text = choice.get("content") or ""
        usage_line, _ = format_usage(data.get("usage"))

        print(f"\n{model['id']}: {assistant_text}")
        print(f"[usage] {usage_line}")

        history.append({"role": "assistant", "content": assistant_text})
        append_log(log_path, "assistant", assistant_text, usage_line)


if __name__ == "__main__":
    main()
