# Misión 3 — El prompt mínimo

Interfaz de chat propia sobre [OpenRouter](https://openrouter.ai) (`chat.py`), usada para
resolver el Juego de la Vida de Conway en el mínimo de prompts posible, con auditoría
completa de tokens y costo por respuesta. Enunciado completo en `mission.md`, criterios
de corrección en `rubric.md`.

## Estructura del repo

| Archivo / carpeta | Qué es |
|---|---|
| `chat.py` | Interfaz de chat CLI sobre OpenRouter (ejercicio 1) |
| `logs/` | Un log `.md` por conversación real con la interfaz, evidencia de auditoría |
| `vida.py` | Solución al Juego de la Vida de Conway, generada por chat (ejercicio 2, pendiente) |
| `test_vida.py` | Script de testing de la cátedra — no se toca |
| `mission.md` | Enunciado completo de la misión |
| `rubric.md` | Cómo se corrige |
| `SPEC.md` | Estado actual de cada ejercicio frente a lo pedido en `mission.md` |
| `CLAUDE.md` / `AGENTS.md` | Instrucciones para trabajar en este repo con una IA de programación |

## Cómo correr el chat

```bash
cp .env.example .env   # completar OPENROUTER_API_KEY, requiere credito cargado
pip3 install -r requirements.txt
python3 chat.py
```

Comandos dentro del chat:

- `/modelo` — elegir modelo (arranca una conversación nueva, con su propio log)
- `/reasoning <low|medium|high|off>` — ajustar el esfuerzo de razonamiento del modelo activo
- `/salir` — terminar

Sirve 4 modelos, cada uno pensado para ejercitar una capacidad distinta de la API (ver
`SPEC.md` para el detalle): reasoning effort, prompt caching, salidas estructuradas y un
modelo barato para comparar costo.

## Cómo correr los tests de Conway

```bash
python3 test_vida.py ruta/a/vida.py
```

## Estado

Ver `SPEC.md` para el detalle completo. Resumen: ejercicio 1 completo, con los 4 logs de
evidencia en `logs/`. Ejercicios 2 (`vida.py`) y 3 (informe) no iniciados.
