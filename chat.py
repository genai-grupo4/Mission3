#!/usr/bin/env python3
"""Interfaz de chat sobre OpenRouter: server web local (estilo J.A.R.V.I.S.) que
sirve 4 modelos, muestra usage y guarda logs .md. Logica de OpenRouter en core.py.
"""
import os
import sys

from flask import Flask, jsonify, request, send_from_directory

import core

app = Flask(__name__, static_folder="static", static_url_path="")

STATE = {"model": None, "history": [], "reasoning_effort": None, "log_path": None}


def model_public(model):
    return {
        "slot": next(k for k, v in core.MODELS.items() if v is model),
        "id": model["id"],
        "label": model["label"],
        "capability": model["capability"],
        "supports_effort": bool(model.get("supports_effort")),
    }


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/models")
def api_models():
    return jsonify([model_public(m) for m in core.MODELS.values()])


@app.route("/api/session", methods=["POST"])
def api_session():
    slot = (request.get_json(silent=True) or {}).get("slot")
    model = core.MODELS.get(slot)
    if not model:
        return jsonify({"error": "slot invalido"}), 400

    STATE["model"] = model
    STATE["history"] = []
    STATE["reasoning_effort"] = model.get("default_effort") if model.get("supports_effort") else None
    STATE["log_path"] = core.new_log(model)

    return jsonify(
        {
            "model": model_public(model),
            "reasoning_effort": STATE["reasoning_effort"],
            "log_path": str(STATE["log_path"].relative_to(core.ROOT)),
        }
    )


@app.route("/api/history")
def api_history():
    return jsonify(core.list_logs())


@app.route("/api/history/load", methods=["POST"])
def api_history_load():
    filename = (request.get_json(silent=True) or {}).get("file", "")
    result = core.load_log(filename)
    if not result:
        return jsonify({"error": "log no encontrado"}), 404

    path, history = result
    slug = path.stem.rsplit("_", 2)[0]
    model = next((m for m in core.MODELS.values() if m["slug"] == slug), None)
    if not model:
        return jsonify({"error": "modelo no reconocido para este log"}), 400

    STATE["model"] = model
    STATE["history"] = [{"role": h["role"], "content": h["content"]} for h in history]
    STATE["reasoning_effort"] = model.get("default_effort") if model.get("supports_effort") else None
    STATE["log_path"] = path

    return jsonify(
        {
            "model": model_public(model),
            "reasoning_effort": STATE["reasoning_effort"],
            "log_path": str(path.relative_to(core.ROOT)),
            "history": history,
        }
    )


@app.route("/api/reasoning", methods=["POST"])
def api_reasoning():
    effort = (request.get_json(silent=True) or {}).get("effort")
    if effort not in ("low", "medium", "high", "off"):
        return jsonify({"error": "effort invalido"}), 400
    if not STATE["model"]:
        return jsonify({"error": "no hay sesion activa"}), 400
    STATE["reasoning_effort"] = effort
    return jsonify({"reasoning_effort": effort})


@app.route("/api/message", methods=["POST"])
def api_message():
    if not STATE["model"]:
        return jsonify({"error": "no hay sesion activa, elegi un modelo primero"}), 400

    text = (request.get_json(silent=True) or {}).get("text", "").strip()
    if not text:
        return jsonify({"error": "mensaje vacio"}), 400

    api_key = core.load_api_key()
    if not api_key:
        return jsonify({"error": "Falta OPENROUTER_API_KEY (ver .env.example)"}), 500

    model = STATE["model"]
    STATE["history"].append({"role": "user", "content": text})
    core.append_log(STATE["log_path"], "user", text)

    messages = core.build_messages(model, STATE["history"], STATE["reasoning_effort"])
    try:
        data = core.call_openrouter(
            api_key,
            model["id"],
            messages,
            reasoning_effort=STATE["reasoning_effort"],
            structured=model.get("structured_output", False),
        )
    except Exception as e:
        STATE["history"].pop()
        return jsonify({"error": f"Error llamando a OpenRouter: {e}"}), 502

    choice = data["choices"][0]["message"]
    assistant_text = choice.get("content") or ""
    usage_line, usage = core.format_usage(data.get("usage"))

    STATE["history"].append({"role": "assistant", "content": assistant_text})
    core.append_log(STATE["log_path"], "assistant", assistant_text, usage_line)

    return jsonify({"text": assistant_text, "usage": usage, "usage_line": usage_line})


def main():
    if not core.load_api_key():
        print(
            "Falta OPENROUTER_API_KEY. Definila como variable de entorno o en un "
            "archivo .env (ver .env.example). El server arranca igual, pero /api/message "
            "va a fallar hasta que la definas.",
            file=sys.stderr,
        )
    port = int(os.environ.get("PORT", 5000))
    print(f"=== J.A.R.V.I.S. — Mision 3 ===\nAbri http://127.0.0.1:{port} en el navegador.")
    app.run(host="127.0.0.1", port=port, debug=False)


if __name__ == "__main__":
    main()
