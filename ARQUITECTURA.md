# Arquitectura de REVAN

Documento técnico para entender cómo se conectan las piezas sin tener que leer el código completo. Si algo aquí y el código no coinciden, el código manda — este documento se puede desactualizar, así que si dudas, verifica.

## Vista general

```
┌─────────────────────────────────────────────────────────────┐
│                          main.py                             │
│   Orquestador principal. Un solo proceso, un solo hilo        │
│   principal + hilos daemon para: escucha continua, voz,       │
│   telemetría de rendimiento, servidor web.                    │
│                                                                │
│   Enrutamiento de comandos en dos capas:                      │
│   1. Router local por palabras clave (rápido, sin costo de    │
│      LLM) — atajos fijos, WhatsApp, correo, cámara, red...    │
│   2. Si nada coincide → NimClient (el LLM decide y ejecuta    │
│      la herramienta correspondiente vía function-calling)     │
└─────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌────────────────┐   ┌──────────────────┐
│  NimClient.py  │   │  servidor.py   │   │  Elevenlabs_      │
│  (el "cerebro")│   │  (FastAPI +    │   │  client.py        │
│  LLM vía NVIDIA│   │  WebSocket)    │   │  (voz: OmniVoice  │
│  NIM, function-│   │  Dashboard web │   │  o respaldo       │
│  calling sobre │   │  en :8000      │   │  Edge TTS)        │
│  ~15 herram.   │   └────────────────┘   └──────────────────┘
└───────────────┘
```

## Flujo de un comando por voz

1. `microphone_client.py` escucha de forma continua (bucle en `bucle_escucha_hilo`, dentro de `main.py`).
2. El texto reconocido pasa por `es_intencion_de_comando()` — un clasificador local por palabras clave (rápido, no gasta tokens de LLM) que decide si es una ORDEN o CONVERSACIÓN.
3. Si es una orden con un atajo conocido (WhatsApp, correo, cámara, red, apps de trabajo, etc.), `main.py` la resuelve directo, sin pasar por el LLM.
4. Si no hay atajo, se manda a `NimClient.generar_respuesta()`, que:
   - Revisa primero si hay una confirmación pendiente (WhatsApp, Coder, Electronics) y la prioriza.
   - Si no, arma el prompt (system prompt fijo + historial + la orden nueva) y llama a la API de NVIDIA NIM con las ~15 herramientas registradas (`tools=HERRAMIENTAS`).
   - Si el modelo decide usar una herramienta, `_ejecutar_herramienta()` la despacha (con rate limiting por categoría) y devuelve el resultado real.
5. La respuesta final pasa por `hablar_sincronizado()`, que coordina el color de la esfera 3D con el momento exacto en que el audio empieza a sonar (ver [Esfera y estados](#esfera-3d-y-estados)).

## Módulos por dominio

| Carpeta | Responsabilidad |
|---|---|
| `src/Core/` | LLM (`NimClient.py`), voz (`Elevenlabs_client.py`), memoria semántica, carga de credenciales, utilidades de texto |
| `src/Automation/` | Abrir apps, navegador, Office, videojuegos, apps de trabajo — todo vía `System_commands.py`/`work_apps_actions.py`/`games_actions.py` |
| `src/Coder_agent/` | Generación y ejecución de código con sandbox y detección de riesgo |
| `src/Creative_agent/` | Generación de imágenes (NVIDIA NIM, respaldo Pollinations AI) |
| `src/Electronics components/` | Comunicación serial con Arduino/ESP32, detección de placas por WMI |
| `src/Emails/` | IMAP/SMTP, redacción asistida, confirmación de envío |
| `src/Phone/` | WhatsApp — canal Android (ADB) con fallback a canal PC (protocolo `whatsapp://`) |
| `src/Network/` | Diagnóstico de red, velocidad, escaneo, detección de intrusos |
| `src/Camara/` | Visión puntual y vigilancia continua |
| `src/Database/` | Conexión a PostgreSQL, esquema, memoria de largo plazo |
| `src/Productividad/` | Snapshot de hardware/agentes/módulos para el dashboard de rendimiento |
| `src/Security/` | Sandbox, saneo de input, confirmación de dos pasos, rate limiting, auditoría |
| `src/Interfaces/` | Servidor FastAPI + WebSocket, todo el frontend web (`web/*.html`, `*.js`) |
| `skills/` | Playbooks en Markdown, inyectados condicionalmente al LLM (ver abajo) |

## Base de datos

PostgreSQL, 4 tablas (creadas automáticamente al arrancar por `src/Database/init.py` + `tablas.py`, no requiere migraciones manuales):

- **`historial_interacciones`** — cada orden del usuario + respuesta de REVAN + qué acción se ejecutó. Es la fuente real de las métricas de "uso por módulo" del dashboard.
- **`memoria_largo_plazo`** — pares clave/valor guardados explícitamente ("recuerda que mi cumpleaños es...").
- **`estado_sistema`** — foco actual (última carpeta usada), para que "crea una carpeta aquí" sepa dónde es "aquí".
- **`memoria_semantica`** — embeddings de conversación. **Nota**: esta tabla se llena, pero `buscar_memoria_semantica()` (la función que la leería para dar contexto al LLM) no está conectada a ningún flujo activo todavía — hoy es solo almacenamiento, no memoria consultable en conversación.

## Seguridad — cómo encajan las piezas

```
Usuario pide una acción irreversible (WhatsApp, correo, código riesgoso, comando serial)
        │
        ▼
GestorConfirmacion.solicitar(descripcion, callback_confirmar, callback_cancelar)
        │  (guarda el callback en memoria, con timestamp, TTL de 60s)
        ▼
Usuario responde algo corto (≤4 palabras) que coincide con FRASES_CONFIRMAR/CANCELAR
        │
        ▼
GestorConfirmacion.procesar_respuesta() → ejecuta el callback correspondiente
```

Cada uno de los 4 flujos que necesitan confirmación (WhatsApp, Correo, Coder, Electronics) tiene su **propia instancia** de `GestorConfirmacion` — no comparten estado entre sí, así que puedes tener, en teoría, una confirmación de WhatsApp y una de Electronics pendientes al mismo tiempo sin que se pisen.

El enrutador en `main.py` que decide si una respuesta corta es "confirma" o "cancela" tiene su **propio** filtro de palabras clave (más amplio que el interno) — ver `es_confirmacion`/`es_cancelacion` en `ejecutar_orden()`. Ambos filtros exigen que la respuesta sea corta (≤4 palabras) para evitar que palabras comunes como "dale" o "ejecuta" secuestren órdenes largas no relacionadas.

## Esfera 3D y estados

La esfera del dashboard (`src/Interfaces/web/esfera.js`) refleja 4 estados, sincronizados por WebSocket desde `main.py`:

| Estado | Color | Cuándo |
|---|---|---|
| `ESPERA` | Azul | Inactivo, sin hablar ni escuchar |
| `ESCUCHANDO` | Verde | Micrófono capturando activamente |
| `PROCESANDO` | Naranja | Generando la respuesta de voz (puede tardar varios segundos en silencio) |
| `HABLANDO` | Rojo | El audio está sonando de verdad — no antes |

La transición a `HABLANDO` ocurre en el instante exacto en que `pygame.mixer.music.play()` va a ejecutarse (vía el callback `avisar_reproduciendo` que `Elevenlabs_client.hablar()` expone), no desde que REVAN "decide" hablar — esto evita que la esfera se vea roja durante el tramo silencioso de generación de audio.

## Voz

`Elevenlabs_client.py` intenta primero un servidor de clonación de voz local compatible con la API de OpenAI (`http://127.0.0.1:3900/v1/audio/speech`, pensado para algo como OmniVoice Studio) y, si no responde en 1.5 segundos o la generación se pasa de `timeout_omnivoice` (40s), cae automáticamente a Microsoft Edge TTS como respaldo. Ambos caminos bloquean hasta que el audio termina de sonar (`pygame.mixer.music.get_busy()`), lo cual es intencional: así se garantiza que la esfera nunca vuelva a azul mientras el audio sigue sonando.

## Skills

`Core/skills_loader.py` lee `skills/*.md` una vez por proceso (con caché en memoria) y, en cada llamada a `NimClient.generar_respuesta()`, revisa si el texto del usuario coincide con las palabras clave del encabezado de algún skill. Si coincide, el contenido de ese `.md` se agrega como mensaje de sistema **extra, solo para esa llamada** — nunca se guarda en el historial persistente, así que no se acumula turno tras turno. Tope duro de 2 skills inyectados por turno.

Formato de un skill:
```markdown
---
nombre: mi_skill
palabras_clave: [palabra1, palabra2, frase con espacios]
---
Contenido en markdown normal, se manda tal cual como mensaje de sistema.
esta seccion de skills en un futuro sera implementada
```

## Dashboard web — flujo de datos en vivo

`servidor.py` mantiene un único WebSocket (`/ws`) al que se conectan todas las vistas (dashboard general, esfera, coder, creative, rendimiento). Los mensajes llevan un campo `"tipo"` que cada página filtra:

- `"chat"` / `"log"` — texto para el panel de telemetría.
- `"estado"` — color/estado de la esfera 3D.
- `"rendimiento_update"` — snapshot de `Productividad/rendimiento_general.py` (hardware, agentes, módulos), emitido cada 4 segundos por un hilo en `main.py` mientras el sistema está activo. **Hay un único emisor** — evita duplicar esta lógica en `servidor.py`, ya se intentó antes y causó datos inconsistentes entre dos formas distintas del mismo mensaje.

## Limitaciones conocidas (honestas, no listadas para quedar bien)

- **Sin tests automatizados.** `test/ominitest.py` es un script de debugging manual, no una suite real.
- **Logging por `print()`**, no por el módulo `logging` — sin niveles, sin rotación de archivos.
- **`main.py` es un router procedural** de `if`/`elif` por palabras clave para los atajos rápidos; conviven dos paradigmas de enrutamiento (ese router local + el tool-calling de `NimClient`).
- **Credenciales en JSON plano**, sin cifrado en reposo — asumido aceptable solo porque REVAN corre local, no en un servidor expuesto.
- **`memoria_semantica`** se guarda pero no se consulta — funcionalidad a medio conectar.
- Un modelo de function-calling relativamente chico (Llama 3.1 8B vía NVIDIA NIM) es notablemente menos confiable que uno grande generando JSON largo o estructurado — de ahí las capas defensivas en `NimClient._ejecutar_herramienta` (normalización de argumentos, detección de tool-calls mal formateados como texto plano).
