# SPEC — Misión: el prompt mínimo

Describe lo que existe en este repo hoy y cómo encaja con lo pedido en `mission.md`
(rúbrica en `rubric.md`).

## Ejercicio 1 — Interfaz de chat (`chat.py` + `core.py` + `static/`)

Server web local (Flask) que habla con OpenRouter (`/api/v1/chat/completions`), con un
frontend propio (HTML/CSS/JS en `static/`) de estética J.A.R.V.I.S. La lógica de
OpenRouter (modelos, llamadas a la API, usage, logs `.md`) vive en `core.py`, separada
del transporte (`chat.py`, server Flask) para que la UI se pueda pulir sin tocar cómo
se arma cada request ni cómo se audita el gasto. La rúbrica no puntúa que la interfaz
sea linda — esta versión es un extra deliberado del grupo sobre el mínimo pedido, no un
requisito de la misión.

La CLI original (loop de input/output por terminal) queda documentada acá como
antecedente: mismo contrato de OpenRouter, mismos logs, solo cambió el transporte
(terminal → HTTP + navegador).

### Modelos servidos

| Slot | Comando | Modelo | Capacidad que ejercita |
|---|---|---|---|
| 1 | elegir `1` | `openai/gpt-5.6-luna` | `reasoning.effort` configurable con `/reasoning <low\|medium\|high\|off>` |
| 2 | elegir `2` | `anthropic/claude-haiku-4.5` | Prompt caching explícito: el system message manda el texto completo de `mission.md` como bloque `cache_control: ephemeral` |
| 3 | elegir `3` | `google/gemini-3.7-flash` | Salidas estructuradas: toda respuesta se fuerza a JSON Schema (`respuesta` + `resumen`) vía `response_format` |
| 4 | elegir `4` | `deepseek/deepseek-v4-flash-0731` | El modelo barato; reasoning opcional con `/reasoning` |

### Comportamiento

- `python3 chat.py` levanta un server Flask en `http://127.0.0.1:5000`; la interfaz vive en el navegador.
- Elegir un slot (botón de modelo en la UI): **arranca conversación nueva** (nuevo log, historial vacío). Nunca mezcla modelos en un mismo log — endpoint `POST /api/session`.
- Toggle de `REASONING EFFORT` (`low|medium|high|off`): setea `reasoning.effort` en el request — endpoint `POST /api/reasoning`. Aplica al modelo activo; no todos los proveedores lo soportan, pero la interfaz no lo restringe (documentar en el informe si un modelo lo ignora).
- Enviar un mensaje: `POST /api/message`.
- Cada request a OpenRouter manda `"usage": {"include": true}` para asegurar que la respuesta traiga `usage` completo (incluye `cost`).
- Después de cada respuesta se muestra en la UI (chips de telemetría bajo el mensaje): `input`, `output`, `reasoning`, `cached`, `cost`.
- Cada turno (user y assistant) se agrega al archivo de log de la conversación activa, con timestamp real al momento de la llamada y, para el assistant, la línea de usage — misma función `append_log` de siempre, ahora en `core.py`.

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
umbral. Ver `chat.py`, constante `CACHED_REFERENCE_TEXT`. El costo real de diagnosticar
este bug (llamadas de debug fuera de `chat.py` + conversaciones descartadas) queda
reconstruido llamada por llamada en `logs/ejercicio1-slot2-cache-bug-redo.md`, para que
el informe del ejercicio 3 pueda cerrar contra el dashboard de OpenRouter sin un gasto
sin explicar.

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

## Ejercicio 3 — Informe

Informe completo en `informe_ejercicio3.md`. Resumen:

- **Trabajo previo obligatorio**: `exploracion.md`. Datos de precios/contexto/parámetros
  sacados de `GET /api/v1/models` (fuente reproducible); benchmarks (Artificial
  Analysis: Intelligence/Coding/Agentic) para los 4 modelos del ejercicio 1, sacados
  por captura de la vista comparativa (se renderizan con JS, no están en la API).
- **Costos del ejercicio 2**: un solo intento (ganador en 1 prompt, sin corridas
  quemadas). Usage: `input=1145 output=29418 reasoning=29091 cached=1065
  cost=$0.00295565`. El 99% del output facturado es razonamiento.
- **Contraste contra gasto real**: no hay cuenta/dashboard web (la cátedra dio una API
  key suelta), así que se usó `GET /api/v1/key` para leer el uso acumulado real de la
  key ($0.05906003). La tabla del informe suma **todos** los logs, incluyendo
  `logs/ejercicio1-slot2-cache-bug-redo.md` (6 llamadas de debug del bug de caching del
  slot 2, reconstruidas llamada por llamada por no haber quedado logueadas en su
  momento): total $0.05905904, cierra contra la key con ~$0.000001 de diferencia
  (redondeo).
- **Conclusión**: bajar `reasoning.effort` a `medium` en el prompt de `vida.py` — el
  contrato ya es lo bastante completo como para no depender de razonamiento `high`.

Estado: completo.

## Fuera de alcance

- UI gráfica o web para el chat: no la pide la misión.
- Persistencia en base de datos: los logs `.md` son la única persistencia requerida.
- Streaming de respuestas: no aporta a los criterios de la rúbrica.
