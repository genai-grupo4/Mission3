# SPEC — Misión: el prompt mínimo

Describe lo que existe en este repo hoy y cómo encaja con lo pedido en `mission.md`
(rúbrica en `rubric.md`).

## Ejercicio 1 — Interfaz de chat (`chat.py`)

CLI en Python (stdlib + `requests`) que habla con OpenRouter (`/api/v1/chat/completions`).
No tiene UI gráfica: es un loop de input/output por terminal, deliberadamente simple
(la misión no puntúa estética).

### Modelos servidos

| Slot | Comando | Modelo | Capacidad que ejercita |
|---|---|---|---|
| 1 | elegir `1` | `openai/gpt-5.6-luna` | `reasoning.effort` configurable con `/reasoning <low\|medium\|high\|off>` |
| 2 | elegir `2` | `anthropic/claude-haiku-4.5` | Prompt caching explícito: el system message manda el texto completo de `mission.md` como bloque `cache_control: ephemeral` |
| 3 | elegir `3` | `google/gemini-3.7-flash` | Salidas estructuradas: toda respuesta se fuerza a JSON Schema (`respuesta` + `resumen`) vía `response_format` |
| 4 | elegir `4` | `deepseek/deepseek-v4-flash-0731` | El modelo barato; reasoning opcional con `/reasoning` |

### Comportamiento

- Al arrancar, pide elegir modelo y abre un log nuevo.
- `/modelo`: vuelve a pedir modelo y **arranca conversación nueva** (nuevo log, historial vacío). Nunca mezcla modelos en un mismo log.
- `/reasoning <low|medium|high|off>`: setea `reasoning.effort` en el request. Aplica al modelo activo; no todos los proveedores lo soportan, pero la interfaz no lo restringe (documentar en el informe si un modelo lo ignora).
- `/salir`: termina el programa.
- Cada request manda `"usage": {"include": true}` para asegurar que la respuesta traiga `usage` completo (incluye `cost`).
- Después de cada respuesta se imprime en consola: `input`, `output`, `reasoning`, `cached`, `cost`, `cache_discount` (si viene).
- Cada turno (user y assistant) se agrega al archivo de log de la conversación activa, con timestamp real al momento de la llamada y, para el assistant, la línea de usage.

### Logs

Formato: `logs/<slug-del-modelo>_<YYYYMMDD_HHMMSS>.md`, uno por conversación. Contenido:

```
# Conversacion — <model id>

Inicio: <ISO timestamp>

## user (<ISO timestamp>)

<mensaje>

## assistant (<ISO timestamp>)

<respuesta>

**Usage:** input=... output=... reasoning=... cached=... cost=$...
```

Los logs son la evidencia de auditoría (ver `rubric.md`, regla de admisibilidad): sin log,
la corrida no cuenta.

### Configuración

- La API key va en `OPENROUTER_API_KEY`, leída de entorno o de un archivo `.env` local
  (ver `.env.example`). `.env` está en `.gitignore`: nunca se commitea.
- Dependencia externa única: `requests` (`requirements.txt`).

## Ejercicio 2 — `vida.py` (pendiente)

Se genera **a través de `chat.py`, slot 4** (`deepseek/deepseek-v4-flash-0731`), con
reasoning activado (`/reasoning`). Reglas completas en `mission.md` § Ejercicio 2:
contrato de CLI fijo, máximo 2 prompts por conversación ganadora, prohibido parchear a
mano, caching obligatorio (la parte estática del prompt va primero e idéntica en todos
los intentos). Todos los intentos —incluidos los quemados— quedan como logs en el repo.

Estado: no iniciado.

## Ejercicio 3 — Informe (pendiente)

Informe de costos y tokens de todos los intentos del ejercicio 2, más las tres respuestas
del "trabajo previo obligatorio" de `mission.md` (qué es un router, mapa de modelos,
comparación de parámetros). Sin esto el ejercicio 3 no puede superar 15/20 (ver
`rubric.md`).

Estado: no iniciado.

## Fuera de alcance

- UI gráfica o web para el chat: no la pide la misión.
- Persistencia en base de datos: los logs `.md` son la única persistencia requerida.
- Streaming de respuestas: no aporta a los criterios de la rúbrica.
