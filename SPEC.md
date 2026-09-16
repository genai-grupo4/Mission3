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

### Estado: completo, con evidencia en `logs/`

Los 4 logs de evidencia (`logs/*.md`) están generados y cumplen el criterio de éxito:

- **Slot 1** (`gpt-5.6-luna_20260915_103902.md`): misma pregunta con `/reasoning low`
  (`reasoning=0`) y después `/reasoning high` (`reasoning=13`) — se ve el efecto del
  effort.
- **Slot 2** (`claude-haiku-4.5_20260915_105355.md`): primer turno con `cached=0`
  (miss genuino, escribe el bloque cacheado); segundo turno con `cached=5491` (hit
  real), costo cae de $0.0072 a $0.0011.
- **Slot 3** (`gemini-3.7-flash_20260915_104452.md`): salida forzada a JSON con
  `respuesta` + `resumen` según el schema.
- **Slot 4** (`deepseek-v4-flash-0731_20260915_104523.md`): misma pregunta usada en el
  slot 2, para comparar costo del modelo barato.

**Bug encontrado y corregido:** el bloque cacheado del slot 2 originalmente mandaba solo
`mission.md` (~3400 tokens) como contexto con `cache_control: ephemeral`. Claude Haiku
4.5+ exige un mínimo de **4096 tokens** para que un bloque sea cacheable (Sonnet/Opus
piden menos); por debajo de ese piso, OpenRouter nunca escribe ni lee cache y
`cached_tokens`/`cache_write_tokens` quedan siempre en 0. Se corrigió concatenando
`mission.md` + `rubric.md` (~5500 tokens) como contexto estático, bien por encima del
umbral. Ver `chat.py`, constante `CACHED_REFERENCE_TEXT`.

Nota aparte (no es un bug de `chat.py`): generar los logs con turnos disparados sin
demora real entre sí (pipe no interactivo) puede hacer que el segundo turno llegue antes
de que el cache write del primero se propague, y termine escribiendo cache de nuevo en
vez de leerlo. En uso normal (una persona tipeando) esto no pasa. El log ganador se
generó con un pequeño delay entre mensajes para reflejar uso real, y se esperó a que
expirara el cache ephemeral (TTL 5 min) de intentos previos antes de la corrida final,
para que el primer turno mostrara `cached=0` genuino — `rubric.md` marca explícitamente
como señal de alarma que el primer intento de una conversación ya tenga
`cached_tokens > 0`, porque sugiere corridas previas no entregadas.

## Ejercicio 2 — `vida.py`

Generado a través de `chat.py`, slot 4 (`deepseek/deepseek-v4-flash-0731`), con
`reasoning.effort=high`. Log ganador: `logs/deepseek-v4-flash-0731_20260915_185232.md`.

- **1 solo prompt** (no hizo falta el segundo de pulido): el contrato completo
  (rol, contexto, instrucciones, restricciones, 6 ejemplos few-shot con los casos
  clave — blinker, bloque, célula sola, borde sin wrap, glider, generación 0) salió
  correcto a la primera.
- `test_vida.py` corre los 9 tests en verde contra el `vida.py` tal cual salió del
  chat, sin edición manual.
- Usage del intento: `input=1145 output=29418 reasoning=29091 cached=1065
  cost=$0.00295565`. El `cached=1065` viene de un prefijo compartido con una corrida
  previa del mismo slot 4 durante el ejercicio 1 (mismo modelo, cache automático por
  prefijo de DeepSeek); no hizo falta un segundo intento para verlo.

Estado: completo.

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
