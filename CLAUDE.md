# CLAUDE.md

Instrucciones para trabajar en este repo con Claude Code (o cualquier otra IA de
programación del grupo). Leer también `mission.md` (el enunciado completo) y
`rubric.md` (cómo se corrige) antes de tocar código: casi todas las reglas de abajo
vienen de ahí, no son preferencias de estilo.

## Qué es este repo

Entrega de la misión "el prompt mínimo": una interfaz de chat propia sobre OpenRouter
(`chat.py`), usada para resolver el Juego de la Vida de Conway en el mínimo de prompts
posible, con auditoría completa de tokens y costo. Ver `SPEC.md` para el estado actual
de cada ejercicio.

## Reglas que no se negocian

- **`test_vida.py` no se toca.** Es el script de testing de la cátedra, se entrega tal
  cual se recibió. Si algo no pasa, el problema está en `vida.py` o en el prompt que lo
  generó, nunca en el test.
- **`vida.py` se genera por chat, no se edita a mano.** El contrato de la interfaz de
  `vida.py` (uso por CLI, formato de grilla, mundo finito, generación 0) está en
  `mission.md` § Ejercicio 2 y es no negociable porque los tests lo asumen literal.
  Si el script que sale del chat no pasa los 9 tests, la corrida se quema: conversación
  nueva, prompt reescrito, de vuelta. Nunca parchear el `.py` a mano — eso invalida
  todo el ejercicio 2 según la rúbrica (regla dura en `rubric.md`).
- **Cada corrida de chat necesita su log `.md`.** `chat.py` ya los genera solo; no
  editar los logs después de creados (los timestamps fuera de orden son una señal de
  alarma explícita en la rúbrica). Los intentos quemados del ejercicio 2 se guardan
  igual que el ganador, no se borran.
- **`.env` nunca se commitea.** La API key vive solo ahí o en la variable de entorno
  `OPENROUTER_API_KEY`. Si algo pide la key, va en `.env` (basado en `.env.example`),
  nunca hardcodeada en `chat.py` ni en un commit.
- **La rúbrica no puntúa que el chat sea lindo** (lo dice explícitamente `mission.md`).
  La UI web con estética J.A.R.V.I.S. (`static/`) es una decisión deliberada del grupo,
  un extra sobre el mínimo pedido — no gastar tiempo de más ahí a costa de los
  ejercicios 2 y 3, que sí puntúan. La lógica de negocio (modelos, usage, logs) vive en
  `core.py`, compartida y sin acoplar al frontend, para que pulir la UI nunca implique
  tocar cómo se llama a OpenRouter o cómo se escriben los logs.

## Cómo correr el chat

```bash
cp .env.example .env   # completar OPENROUTER_API_KEY, requiere credito cargado
pip3 install -r requirements.txt
python3 chat.py
```

Abre un server local en `http://127.0.0.1:5000`: elegir modelo (slot) arranca una
conversación nueva con su propio log; el toggle de reasoning effort ajusta
`low|medium|high|off` del modelo activo. La lógica de OpenRouter (modelos, llamadas,
usage, logs) está en `core.py`; `chat.py` es el server Flask que la expone.

## Cómo correr los tests de Conway

```bash
python3 test_vida.py ruta/a/vida.py
```

Los 9 tests tienen que pasar contra el `vida.py` que salió del chat, sin modificar.

## Convenciones de commits

Commits chicos y descriptivos por cambio real (una interfaz, un fix, un log agregado),
no un commit único "todo". La rúbrica evalúa la historia de commits como evidencia de
forma de trabajo (`rubric.md` § 4.3).

## Estado y próximos pasos

Ver `SPEC.md`. Resumen: ejercicio 1 completo (interfaz + logs de evidencia en `logs/`);
ejercicios 2 y 3 no iniciados. Próximo paso: prompt para generar `vida.py` por el slot 4
del chat.
