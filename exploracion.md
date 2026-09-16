# Exploración previa — OpenRouter

Respuestas al "Antes de todo (obligatorio)" de `mission.md`. Datos verificados contra
`GET https://openrouter.ai/api/v1/models` (catálogo completo, 2026-09-16) salvo donde
se indica que vienen de la ficha web.

## 1. Qué es un router

Un router de modelos es un endpoint que no representa un modelo fijo sino una política
de selección: recibe el mismo request de chat completions y decide, en cada llamada,
a qué modelo/proveedor real reenviarlo. El **Auto Router** de OpenRouter
(`openrouter/auto`) resuelve el problema de "no sé de antemano qué modelo conviene para
este prompt": en vez de que el desarrollador elija manualmente un id fijo, el router
observa qué modelo tuvo mejor desempeño en la demanda del mercado de OpenRouter para
tareas parecidas en los últimos 7 días y enruta ahí. Sirve también como fallback
automático entre proveedores cuando uno se cae o se satura, sin que el cliente tenga
que manejar esa lógica.

*(Nota: la API pública de modelos y la ficha web no exponen el algoritmo exacto de
selección — solo el comportamiento declarado en la documentación de producto.)*

## 2. Mapa de modelos — el más avanzado de cada proveedor

Criterio: dentro de cada proveedor, se tomó el modelo con `created` (timestamp de alta
en el catálogo) más reciente al 2026-09-16, como proxy de "más avanzado" — la API de
modelos no expone ranking de benchmarks; ese dato solo vive en el frontend con JS y no
se pudo extraer de forma confiable (ver nota al pie).

| Proveedor | Modelo más avanzado (id) | Precio entrada ($/M tok) | Precio salida ($/M tok) | Contexto |
|---|---|---:|---:|---:|
| OpenAI | `openai/gpt-6-astra-pro` | $10.00 | $50.00 | 1,050,000 |
| Anthropic | `anthropic/claude-fable-5.1` | $10.00 | $50.00 | 1,000,000 |
| xAI (Grok) | `x-ai/grok-4.6` | $2.00 | $6.00 | 500,000 |
| Google (Gemini) | `google/gemini-3.8-flash` | $0.75 | $3.75 | 1,048,576 |
| DeepSeek | `deepseek/deepseek-v4.1-flash` | $0.15 | $0.60 | 1,048,576 |
| Qwen | `qwen/qwen3.8-max-0902` | $2.00 | $6.00 | 1,000,000 |
| Kimi (Moonshot) | `moonshotai/kimi-k3` | $2.65 | $13.28 | 1,048,576 |

Benchmarks: la ficha web de cada modelo (`openrouter.ai/<proveedor>/<modelo>`) muestra
gráficos de posición en benchmarks (Artificial Analysis, etc.) que son renderizados por
JS del lado del cliente y no se pudieron extraer vía fetch de texto plano — se completó
a mano con captura de pantalla solo para los 4 modelos del ejercicio 1 (ver abajo); para
los otros 3 proveedores del mapa completo, mismo procedimiento si hace falta.

### Benchmarks — los 4 modelos del ejercicio 1 (Artificial Analysis, vía vista comparativa)

Fuente: `openrouter.ai/compare/openai/gpt-5.6-luna/anthropic/claude-haiku-4.5/google/gemini-3.7-flash/deepseek/deepseek-v4-flash-0731`,
capturado el 2026-09-16. Variants usadas por la página: GPT-5.6 Luna (max),
Claude 4.5 Haiku (Reasoning), Gemini 3.7 Flash (medium), DeepSeek V4 Flash 0731
(Reasoning, max).

| Modelo (slot) | Intelligence | Coding | Agentic |
|---|---:|---:|---:|
| GPT-5.6 Luna (slot 1) | 38 | 71 | 43 |
| Claude Haiku 4.5 (slot 2) | 18 | 44 | 10 |
| Gemini 3.7 Flash (slot 3) | sin dato* | — | sin dato* |
| DeepSeek V4 Flash 0731 (slot 4) | 35 | 69 | 42 |

\* La página marca explícitamente "Gemini 3.7 Flash (medium) has no intelligence data" y
"...has no agentic data" — no está en el gráfico de Coding tampoco (no aparece esa barra
en la captura), así que Artificial Analysis no tiene benchmark cargado para esta variant
en ninguna de las tres categorías.

Lectura: dentro de estos 4, **GPT-5.6 Luna** lidera intelligence y agentic; en coding
**GPT-5.6 Luna (71)** y **DeepSeek V4 Flash (69)** quedan muy cerca, con Claude Haiku 4.5
bien por debajo en las tres categorías (18/44/10) — coherente con ser el modelo elegido
para el ejercicio de *caching* y no para razonamiento pesado, y con que el slot 4
(DeepSeek, el "escalón barato" según mission.md) rinda casi a la par del más caro del
grupo en coding pese a costar una fracción del precio (ver tabla de precios arriba).

Nota de contexto: `gpt-5.6-luna` (slot 1 de esta misión) ya no es el modelo más nuevo de
OpenAI en catálogo — apareció `gpt-6-astra`/`gpt-6-astra-pro` después. Se documenta acá
por ser lo pedido en el punto 2 del enunciado (el "más avanzado de cada proveedor" a la
fecha de esta exploración), sin que esto invalide el slot 1 de `chat.py`, que usa el id
fijado por la cátedra.

## 3. Parámetros comunes — comparación entre proveedores

`supported_parameters` tal cual los devuelve `GET /api/v1/models`, para los mismos 7
modelos de arriba:

| Proveedor | reasoning/effort | structured_outputs | temperature/sampling | Otros propios |
|---|---|---|---|---|
| OpenAI (`gpt-6-astra-pro`) | sí (`reasoning`, `reasoning_effort`, `include_reasoning`) | sí | no (no aparece `temperature`/`top_p`) | `seed` |
| Anthropic (`claude-fable-5.1`) | sí | sí | no (no aparece `temperature`) | `verbosity`, `stop` |
| xAI (`grok-4.6`) | sí | sí | sí (`temperature`, `top_p`, `top_k`) | `logprobs`, `seed` |
| Google (`gemini-3.8-flash`) | sí | sí | sí (`temperature`, `top_p`) | `seed` |
| DeepSeek (`deepseek-v4.1-flash`) | sí | sí | sí (`temperature`, `top_p`, `top_k`, `min_p`) | `frequency_penalty`, `presence_penalty`, `repetition_penalty`, `logit_bias` |
| Qwen (`qwen3.8-max-0902`) | sí | sí | sí (`temperature`, `top_p`, `top_k`) | `frequency_penalty`, `presence_penalty` |
| Kimi (`kimi-k3`) | sí | sí | sí (`temperature`, `top_p`, `top_k`, `min_p`) | `frequency_penalty`, `presence_penalty`, `repetition_penalty`, `logit_bias` |

Lectura: los 7 aceptan el parámetro unificado `reasoning` (con `effort` o `max_tokens`
según el proveedor, como ya documenta `mission.md` §Ejercicio 1) y `response_format`
para salidas estructuradas — coherente con lo usado en slots 1, 2 y 3 de `chat.py`.
Donde sí difieren es en las perillas de sampling: OpenAI y Anthropic **no** exponen
`temperature`/`top_p`/`top_k` en sus modelos más nuevos (limitan el control de
muestreo), mientras que xAI, Google, DeepSeek, Qwen y Kimi sí los aceptan, y los tres
últimos además suman penalizaciones de frecuencia/repetición típicas de la familia
GPT-3-style que OpenAI/Anthropic no exponen en sus modelos de última generación.

## Fuente y reproducibilidad

```bash
curl -s https://openrouter.ai/api/v1/models -o models.json
python3 -c "import json; d=json.load(open('models.json')); print(d['total_count'])"
```

Catálogo consultado: 2026-09-16. Los ids y precios cambian con el tiempo (OpenRouter
lista snapshots nuevos seguido); si se re-corre esta exploración más adelante, los
"más avanzados" pueden diferir.
