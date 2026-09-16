# Ejercicio 3 — La cuenta final

Informe de costos y tokens de la misión. Ver también `exploracion.md` (trabajo previo
obligatorio: router, mapa de modelos, parámetros) y `SPEC.md` (estado general del repo).

## Intentos del ejercicio 2 (`vida.py`)

Un solo intento, ganador en el primer prompt — no hubo corridas quemadas que reportar.

| Intento | Log | Resultado |
|---|---|---|
| 1 (ganador) | `logs/deepseek-v4-flash-0731_20260915_185232.md` | 9/9 tests en verde, sin edición manual |

### Tokens y costo del intento ganador

| Métrica | Valor |
|---|---|
| Tokens de entrada | 1,145 |
| Tokens de salida | 29,418 |
| — de los cuales, razonamiento | 29,091 |
| Tokens cacheados (de entrada) | 1,065 |
| Costo | $0.00295565 |

El modelo (`deepseek/deepseek-v4-flash-0731`, slot 4) corrió con `reasoning.effort=high`.
Del total de salida, el **99% (29,091 de 29,418 tokens) fue razonamiento**, no la
respuesta final — el script en sí es una fracción chica del output facturado.

**Caching:** el prompt sí muestra `cached=1065` ya en este primer intento. No es un
cache hit *del propio ejercicio 2* (no hubo un segundo intento contra el cual comparar,
porque el primero salió correcto), sino un hit por **prefijo compartido con el mismo
modelo (slot 4) usado antes en el ejercicio 1** — DeepSeek cachea automáticamente por
prefijo repetido entre llamadas, no solo dentro de una misma conversación. Esto ya
satisface el requisito de "caching obligatorio" del enunciado sin necesitar quemar una
corrida extra solo para demostrarlo.

### Hallazgo: tokens de razonamiento y qué se factura

`mission.md` pide señalar si algún modelo razona sin devolver esos tokens en la
respuesta (caso típico de la serie o de OpenAI). En este caso **no aplica para ningún
modelo usado**: tanto DeepSeek (slot 4, el que generó `vida.py`, con
`reasoning=29091` en el intento ganador) como GPT-5.6 Luna (slot 1, con `reasoning=13`
al subir el effort a `high` en el log de evidencia del ejercicio 1) devuelven
`reasoning_tokens` explícitos en el `usage`, y ese razonamiento se factura al mismo
precio por token de salida que el resto — no hay tarifa separada para thinking en
ninguno de los dos. El hallazgo relevante acá es otro: en el intento ganador de
`vida.py`, el razonamiento domina el costo — de los $0.00295565 totales, la porción de
salida (dominada por razonamiento) es la que pesa, no la entrada ni el cache.

## Todos los logs del repo (ejercicios 1 + 2)

Tabla única con **todas** las llamadas documentadas en `logs/`, incluyendo
`ejercicio1-slot2-cache-bug-redo.md` (el debugging del bug de caching del slot 2,
reconstruido llamada por llamada por no haber quedado logueado en su momento — ver ese
archivo para el detalle de cada fila y su causa):

| Log | input | output | reasoning | cached | costo |
|---|---:|---:|---:|---:|---:|
| `gpt-5.6-luna_...103902.md` (turno 1, effort low) | 21 | 5 | 0 | 0 | $0.0000102 |
| `gpt-5.6-luna_...103902.md` (turno 2, effort high) | 47 | 20 | 13 | 0 | $0.0000334 |
| `claude-haiku-4.5_...105355.md` (turno 1, miss) | 5,515 | 61 | 0 | 0 | $0.00719275 |
| `claude-haiku-4.5_...105355.md` (turno 2, hit) | 5,599 | 86 | 0 | 5,491 | $0.0010871 |
| `gemini-3.7-flash_...104452.md` | 118 | 439 | 336 | 0 | $0.00173475 |
| `deepseek-v4-flash-0731_...104523.md` (slot 4, ej. 1) | 95 | 326 | 291 | 0 | $0.000330484 |
| `deepseek-v4-flash-0731_...185232.md` (slot 4, ej. 2, ganador) | 1,145 | 29,418 | 29,091 | 1,065 | $0.00295565 |
| `ejercicio1-slot2-cache-bug-redo.md`, fila 1 (debug directo, ctx. `mission.md`) | — | — | — | — | $0.006919 |
| `ejercicio1-slot2-cache-bug-redo.md`, fila 2 (debug directo, forzando provider) | — | — | — | — | $0.006919 |
| `ejercicio1-slot2-cache-bug-redo.md`, fila 3 (debug directo, ctx. `mission.md`+`rubric.md`) | — | — | — | — | $0.007461 |
| `ejercicio1-slot2-cache-bug-redo.md`, fila 4 (`chat.py` slot 2, intento #1, descartado) | — | — | — | — | $0.007813 |
| `ejercicio1-slot2-cache-bug-redo.md`, fila 5 (`chat.py` slot 2, intento #2, descartado) | — | — | — | — | $0.0145325 |
| `ejercicio1-slot2-cache-bug-redo.md`, fila 6 (`chat.py` slot 2, intento #3, descartado) | — | — | — | — | $0.0020712 |
| **Total (todas las filas)** | **12,540** | **30,355** | **29,731** | **6,556** | **$0.05905904** |

*(Las filas del redo no tienen desglose de tokens porque `logs/ejercicio1-slot2-cache-bug-redo.md`
reconstruyó el costo a partir del historial de la sesión que hizo el debugging, sin
guardar el `usage` completo turno a turno — solo el `cost` final de cada llamada.)*

Este total ($0.05905904) contrasta contra el uso real de la key (`$0.05906003`, ver
sección siguiente) con una diferencia de ~$0.000001, atribuible a redondeo.

### Ahorro por cache (slot 2, Claude Haiku 4.5)

El único cache hit "clásico" (mismo contexto, dentro de la misma conversación) es el
del ejercicio 1, slot 2: el segundo turno reusa el bloque estático (`mission.md` +
`rubric.md`, cache_control ephemeral) y el costo de esa respuesta cae de $0.00719275 a
$0.0010871 — **una baja del 85%** pese a que el segundo turno tiene *más* tokens de
entrada nominales (5,599 vs 5,515), porque 5,491 de esos tokens salieron a precio de
cache en vez de precio pleno.

## Contraste contra el gasto real de la cuenta

No usamos el dashboard web (la cátedra entregó una API key sin cuenta propia), así que
el "dashboard" en este caso es el endpoint `GET /api/v1/key`, que devuelve el uso
acumulado asociado a esa key directamente desde OpenRouter:

```bash
curl -s https://openrouter.ai/api/v1/key -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

```json
"usage": 0.059060034,
"usage_weekly": 0.059060034,
"usage_monthly": 0.059060034
```

| | Monto |
|---|---:|
| Suma de costos en la tabla de arriba (todas las filas) | $0.05905904 |
| Uso total acumulado de la key (`/api/v1/key`) | $0.05906003 |
| **Diferencia** | **≈ $0.000001 (redondeo)** |

Cierra. De ese total, $0.0457157 corresponde a 6 llamadas/conversaciones contra Claude
Haiku 4.5 (slot 2) que no generaron log en su momento — 3 llamadas de debug directas a
la API y 3 conversaciones de `chat.py` descartadas — hechas para diagnosticar por qué
el primer diseño del slot 2 nunca mostraba `cached_tokens > 0`: el bloque cacheado
mandaba solo `mission.md` (~3400 tokens), por debajo del piso de 4096 tokens que Claude
Haiku 4.5+ exige para que un bloque sea cacheable. El detalle completo, llamada por
llamada, y la causa raíz están en `logs/ejercicio1-slot2-cache-bug-redo.md`.

## Conclusión (qué cambiar para bajar costo sin perder "1 prompt")

Bajaríamos `reasoning.effort` de `high` a `medium` en el prompt del ejercicio 2: el
99% del output facturado fueron tokens de razonamiento (29,091 de 29,418), y el
contrato ya era una especificación completa con ejemplos few-shot — ese nivel de detalle
en el prompt reduce la necesidad de que el modelo "piense mucho" para no desviarse del
contrato, así que es probable que `medium` alcance para los 9 tests igual, a una
fracción del costo de razonamiento sin arriesgar el "1 prompt".
