# AGENTS.md

Este archivo es para quien programe en este repo con una IA que no sea Claude Code
(Antigravity, Copilot, Codex, etc. — la misión permite cualquiera). Las instrucciones
reales están en `CLAUDE.md`; son las mismas para cualquier herramienta, así que léanlo
primero. Este archivo solo existe porque algunas herramientas buscan `AGENTS.md` por
convención en vez de `CLAUDE.md`.

Resumen rápido (ver `CLAUDE.md` para el detalle y el porqué de cada regla):

- No editar `test_vida.py`.
- No editar `vida.py` a mano: sale del chat, se regenera por prompt si falla.
- No commitear `.env` ni ninguna API key.
- Cada corrida de chat necesita su log `.md` generado por `chat.py`, sin edición manual posterior.
- Setup y comandos para correr el chat y los tests: ver `CLAUDE.md` § "Cómo correr...".
- Estado del proyecto y qué falta: ver `SPEC.md`.
