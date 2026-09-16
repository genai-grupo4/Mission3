# Evidencia — Ejercicio 1, slot 2: bug de caching y costo de debugging no logueado

Este archivo no es un log de conversación con un modelo; es evidencia de auditoría de
un problema real encontrado durante el ejercicio 1, para que el costo extra que generó
quede documentado en vez de disuelto (o perdido) en el gasto total del proyecto (ver
`mission.md` § Ejercicio 3, criterio "gasto total contrastado contra el dashboard, y la
diferencia explicada si la hay").

## Qué pasó

Al generar la interfaz de chat (`chat.py`), el slot 2 (`anthropic/claude-haiku-4.5`)
tenía que demostrar un cache hit real (criterio de éxito del ejercicio 1, y 1.6 de
`rubric.md`). La primera versión de `chat.py` armaba el bloque cacheado del system
message solo con el texto de `mission.md` (~3400 tokens) marcado con
`cache_control: ephemeral`.

Claude Haiku 4.5+ exige un mínimo de **4096 tokens** para que un bloque sea cacheable.
Por debajo de ese piso, OpenRouter nunca escribe ni lee cache: `cached_tokens` y
`cache_write_tokens` quedan siempre en 0, sin importar cuántas veces se repita el
mismo contexto. Esa regla no está escrita en `mission.md` ni en `rubric.md` — es una
restricción del proveedor (Anthropic) que no se verificó antes de generar la primera
corrida, y llevó a producir una conversación de slot 2 completa que **no** cumplía el
criterio de éxito (nunca iba a mostrar `cached_tokens > 0` en un segundo turno, por
diseño).

## Diagnóstico y redo: costo real, llamada por llamada

Para diagnosticar el problema y confirmar el fix antes de tocar `chat.py`, se hicieron
llamadas directas a la API (fuera del loop de la interfaz) y varias conversaciones de
`chat.py` que se descartaron. Ninguna de esas quedó logueada en su momento — ni las
llamadas directas (nunca pasaron por `chat.py`, que es lo único que genera logs) ni las
3 conversaciones de `chat.py` que se descartaron (sus archivos se borraron al
reemplazarlas por el intento bueno; el ejercicio 1 no tenía la regla de "intentos
quemados se guardan" que sí aplica al ejercicio 2). Se reconstruyó el costo exacto de
cada una a partir del historial de la sesión que hizo el trabajo:

| # | Origen | Turno 1 | Turno 2 | Subtotal |
|---|---|---|---|---|
| 1 | Script de debug directo a la API (fuera de `chat.py`), contexto solo `mission.md` (~3400 tok), routing default | $0.00345 | $0.003469 | $0.006919 |
| 2 | Mismo script, repetido forzando `provider: {order: ["Anthropic"]}` para descartar que el routing fuera la causa | $0.00345 | $0.003469 | $0.006919 |
| 3 | Script de debug directo, contexto `mission.md`+`rubric.md` (~5500 tok) con delay de 2s, para confirmar que el fix funcionaba antes de tocar `chat.py` | $0.006849 | $0.000612 | $0.007461 |
| 4 | `chat.py` slot 2, intento #1 (contexto solo `mission.md`, sin delay entre turnos) — log borrado tras el intento | $0.003756 | $0.004057 | $0.007813 |
| 5 | `chat.py` slot 2, intento #2 (contexto ya con `rubric.md`, sin delay entre turnos → race condition, escribió cache dos veces en vez de leerlo) — log borrado | $0.00720775 | $0.00732475 | $0.0145325 |
| 6 | `chat.py` slot 2, intento #3 (con delay, pero heredó cache todavía vivo del intento #2 → primer turno ya mostraba `cached>0`, señal de alarma de `rubric.md`) — log borrado | $0.0008831 | $0.0011881 | $0.0020712 |
| | **Total reconstruido** | | | **$0.0457157** |

Más la corrida ganadora final que sí quedó logueada
(`logs/claude-haiku-4.5_20260915_105355.md`): $0.00719275 (turno 1, escritura de cache)
+ $0.0010871 (turno 2, cache hit) = **$0.00828 aprox.**

**Total real gastado en Claude Haiku 4.5 durante todo el ejercicio 1: $0.0457157 +
$0.00828 ≈ $0.054**, consistente con lo que muestra el dashboard de actividad de
OpenRouter para ese modelo. Contra los $0.00828 que suman los logs commiteados, la
diferencia ($0.04572) queda explicada por completo por la tabla de arriba.

## La causa raíz

Pasé por alto verificar el requisito de tamaño mínimo de bloque cacheable del
proveedor (Anthropic/Claude Haiku 4.5) antes de dar por completo el diseño de
`chat.py`. La lección: antes de generar evidencia contra una API real y paga, hay que
verificar no solo lo que pide `mission.md` explícitamente, sino también las
restricciones propias de cada proveedor que puedan bloquear silenciosamente un
criterio de éxito (acá, el piso de tokens para cachear). Segunda lección, aparte: el
ejercicio 1 debería tratar sus logs con la misma regla de "no se borran" que
`mission.md` exige para el ejercicio 2 — de haber existido esa regla acá, esta
reconstrucción no habría hecho falta.

## La corrección

`chat.py`, constante `CACHED_REFERENCE_TEXT` (commit `8550411`): el contexto estático
del slot 2 pasó a ser `mission.md` + `rubric.md` concatenados (~5500 tokens), bien por
encima del piso de 4096. Con eso, la corrida ganadora (`claude-haiku-4.5_20260915_105355.md`)
muestra `cached=0` genuino en el primer turno y `cached=5491` en el segundo.
