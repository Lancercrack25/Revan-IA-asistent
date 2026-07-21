import os
import json
import time

try:
    from openai import OpenAI
except ImportError:
    print("Falta la librería 'openai'. Instálala con: pip install openai")
    raise

from src.Services.os_service import (
    analizar_entorno_vision,
    abrir_carpeta_sistema,
    crear_carpeta_sistema,
    obtener_ruta_actual,
    registrar_accion_sistema,
    ejecutar_limpieza_sistema,
    obtener_diagnostico_hardware,
)
from src.Automation.System_commands import (
    desplegar_monitores_windows,
    ejecutar_aplicacion_office,
    reproducir_video_brave,
    lanzar_aplicacion_usuario,
    lanzar_videojuego,
)
from src.Database.conexion import obtener_conexion_pool, liberar_conexion
from src.Phone.whats import abrir_chat_con_mensaje


# ─── DEFINICIÓN DE HERRAMIENTAS (formato estándar OpenAI-compatible) ──────
# Esto reemplaza el enfoque anterior de "describir el JSON en el prompt y
# parsear texto libre con regex". Ahora el modelo recibe estos schemas
# validados y devuelve argumentos ya estructurados garantizados (tool_calls),
# no texto que hay que adivinar cómo extraer. mistral-nemotron soporta esto
# de forma nativa (fue elegido justo por eso).
HERRAMIENTAS = [
    {
        "type": "function",
        "function": {
            "name": "crear_carpeta",
            "description": "Crea una carpeta nueva en el sistema de archivos del usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre de la carpeta a crear"},
                    "ruta": {
                        "type": "string",
                        "enum": ["actual", "escritorio", "documentos"],
                        "description": "Dónde crear la carpeta. Si el usuario NO menciona ubicación, usa 'escritorio' (es lo más predecible y fácil de encontrar). Usa 'actual' SOLO si el usuario claramente sigue trabajando en algo relacionado con una carpeta que se mencionó hace poco en esta misma conversación.",
                    },
                },
                "required": ["nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "abrir_carpeta",
            "description": "Abre una carpeta existente por nombre.",
            "parameters": {
                "type": "object",
                "properties": {"nombre": {"type": "string", "description": "Nombre de la carpeta a abrir"}},
                "required": ["nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "abrir_office",
            "description": "Abre Word o Excel, opcionalmente creando un documento nuevo con un nombre en una carpeta específica.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app": {"type": "string", "enum": ["word", "excel"]},
                    "nombre_archivo": {"type": "string", "description": "Nombre del archivo a crear"},
                    "destino": {"type": "string", "description": "'actual', o el nombre de una carpeta específica"},
                },
                "required": ["app"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reproducir_video",
            "description": "Busca y reproduce un video en el navegador (Brave).",
            "parameters": {
                "type": "object",
                "properties": {"busqueda": {"type": "string", "description": "Qué buscar y reproducir"}},
                "required": ["busqueda"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "abrir_aplicacion",
            "description": "Abre una aplicación instalada en la PC del usuario.",
            "parameters": {
                "type": "object",
                "properties": {"nombre": {"type": "string", "description": "Nombre de la aplicación"}},
                "required": ["nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "abrir_videojuego",
            "description": "Abre un videojuego instalado en la PC del usuario.",
            "parameters": {
                "type": "object",
                "properties": {"nombre": {"type": "string", "description": "Nombre del videojuego"}},
                "required": ["nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mostrar_monitor_recursos",
            "description": "Despliega los monitores nativos de recursos del sistema de Windows (CPU, RAM, red, disco).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "diagnostico_hardware",
            "description": "Da un reporte rápido de uso actual de CPU, RAM y disco, hablado (no abre ninguna ventana).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "limpiar_sistema",
            "description": "Borra archivos temporales de Windows para liberar espacio. Es una acción destructiva (elimina archivos), solo debe usarse si el usuario lo pide explícitamente.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analizar_camara",
            "description": "Enciende la cámara y describe brevemente qué hay frente a ella en este momento.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_informacion",
            "description": "Busca información sobre un tema en fuentes confiables de internet (Wikipedia y respaldo en DuckDuckGo) y devuelve un resumen. Úsala cuando el usuario pida investigar, saber qué es algo, o quién es alguien.",
            "parameters": {
                "type": "object",
                "properties": {"tema": {"type": "string", "description": "El tema a investigar"}},
                "required": ["tema"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "guardar_nota",
            "description": "Guarda un dato o nota en la memoria permanente de REVAN, para poder recordarlo después bajo una clave concreta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "clave": {"type": "string", "description": "Palabra o frase corta para identificar la nota (ej. 'cumpleaños de mamá')"},
                    "contenido": {"type": "string", "description": "El contenido a recordar"},
                },
                "required": ["clave", "contenido"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "enviar_whatsapp",
            "description": "Abre WhatsApp en el chat de un contacto (buscado por nombre en la agenda del teléfono, o con un número directo) con un mensaje ya escrito. NO lo envía automáticamente por seguridad: el usuario confirma el envío tocando el botón en su teléfono.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinatario": {"type": "string", "description": "Nombre del contacto (tal como está en la agenda) o número de teléfono"},
                    "mensaje": {"type": "string", "description": "El mensaje a escribir"},
                },
                "required": ["destinatario", "mensaje"],
            },
        },
    },
]


class NimClient:
    def __init__(self, api_key: str = None, modelo: str = "mistralai/mistral-nemotron"):
        self.api_key = api_key or os.getenv("NVIDIA_NIM_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "Falta la API key de NVIDIA NIM. Pásala como argumento o "
                "define la variable de entorno NVIDIA_NIM_API_KEY."
            )

        self.modelo = modelo
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key,
        )

        self.system_prompt = (
            "Eres REVAN, asistente tipo Jarvis para el sistema operativo del usuario.\n"
            "Tienes herramientas reales para ejecutar acciones físicas (crear carpetas, "
            "abrir apps, investigar temas, guardar notas, etc.). Cuando el usuario pida "
            "algo que corresponda a una herramienta, ÚSALA en vez de solo describir qué "
            "harías. Puedes usar varias herramientas en secuencia si la tarea lo requiere "
            "(por ejemplo: investigar un tema Y LUEGO guardar el resultado como nota).\n"
            "Si es conversación ordinaria sin ninguna acción física de por medio, responde "
            "en texto plano, máximo 1 o 2 frases cortas (menos de 25 palabras)."
        )

    # ─── EJECUCIÓN DE HERRAMIENTAS ─────────────────────────────────────────

    def _guardar_nota(self, clave: str, contenido: str) -> str:
        if not clave or not contenido:
            return "Necesito una clave y un contenido para guardar la nota, Señor."

        conn = obtener_conexion_pool()
        if not conn:
            return "No pude guardar la nota, sin conexión a la base de datos."

        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO memoria_largo_plazo (clave, valor)
                VALUES (%s, %s)
                ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor, fecha_guardado = CURRENT_TIMESTAMP;
                """,
                (clave, contenido),
            )
            conn.commit()
            cur.close()
            return f"Guardado, Señor. Recordaré '{clave}'."
        except Exception as e:
            conn.rollback()
            return f"Error al guardar la nota: {e}"
        finally:
            liberar_conexion(conn)

    def _ejecutar_herramienta(self, nombre: str, argumentos: dict) -> str:
        """Ejecuta la herramienta pedida por el modelo y devuelve el resultado
        como texto (que se le reenvía al modelo como 'resultado de la herramienta')."""
        try:
            if nombre == "crear_carpeta":
                nombre_c = (argumentos.get("nombre") or "Contenedor_Táctico").strip() or "Contenedor_Táctico"
                ruta_c = argumentos.get("ruta", "escritorio")
                resultado = crear_carpeta_sistema(nombre_c, ruta_c)
                registrar_accion_sistema(f"crear_carpeta({nombre_c})", resultado, "CREAR_CARPETA")
                return resultado

            elif nombre == "abrir_carpeta":
                resultado = abrir_carpeta_sistema(argumentos.get("nombre", ""))
                registrar_accion_sistema(f"abrir_carpeta({argumentos.get('nombre','')})", resultado, "ABRIR_CARPETA")
                return resultado

            elif nombre == "abrir_office":
                app_tipo = argumentos.get("app", "word")
                nombre_doc = argumentos.get("nombre_archivo", "Documento_Táctico")
                carpeta_destino = argumentos.get("destino", "")

                if carpeta_destino and carpeta_destino.lower() != "actual":
                    escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
                    ruta_final = os.path.join(escritorio, carpeta_destino)
                else:
                    ruta_final = obtener_ruta_actual()

                os.makedirs(ruta_final, exist_ok=True)
                ejecutar_aplicacion_office(app_tipo)
                nombre_directorio_actual = os.path.basename(ruta_final)
                resultado = f"¡Listo, Señor! Abriendo {app_tipo.capitalize()} para el documento en '{nombre_directorio_actual}'."
                registrar_accion_sistema(f"abrir_office({app_tipo})", resultado, "OFFICE")
                return resultado

            elif nombre == "reproducir_video":
                busqueda = argumentos.get("busqueda", "")
                reproducir_video_brave(busqueda)
                resultado = f"Reproduciendo contenido sobre '{busqueda}' en Brave."
                registrar_accion_sistema(f"video({busqueda})", resultado, "VIDEO")
                return resultado

            elif nombre == "abrir_aplicacion":
                app_nombre = argumentos.get("nombre", "")
                lanzar_aplicacion_usuario(app_nombre)
                resultado = f"Ejecutando aplicación {app_nombre}."
                registrar_accion_sistema(f"app({app_nombre})", resultado, "APP")
                return resultado

            elif nombre == "abrir_videojuego":
                juego_nombre = argumentos.get("nombre", "")
                lanzar_videojuego(juego_nombre)
                resultado = f"Iniciando {juego_nombre}, Señor."
                registrar_accion_sistema(f"juego({juego_nombre})", resultado, "JUEGO")
                return resultado

            elif nombre == "mostrar_monitor_recursos":
                desplegar_monitores_windows()
                resultado = "Monitores tácticos del sistema desplegados, Señor."
                registrar_accion_sistema("monitor", resultado, "MONITOR")
                return resultado

            elif nombre == "diagnostico_hardware":
                resultado = obtener_diagnostico_hardware()
                registrar_accion_sistema("diagnostico_hardware", resultado, "DIAGNOSTICO")
                return resultado

            elif nombre == "limpiar_sistema":
                resultado = ejecutar_limpieza_sistema()
                registrar_accion_sistema("limpiar_sistema", resultado, "LIMPIEZA")
                return resultado

            elif nombre == "analizar_camara":
                resultado = analizar_entorno_vision()
                registrar_accion_sistema("camara", resultado, "VISION")
                return resultado

            elif nombre == "buscar_informacion":
                from src.Services.research_service import buscar_y_resumir_tema
                tema = argumentos.get("tema", "")
                resultado = buscar_y_resumir_tema(tema)
                registrar_accion_sistema(f"investigar({tema})", resultado, "RESEARCH_TASK")
                return resultado

            elif nombre == "guardar_nota":
                return self._guardar_nota(argumentos.get("clave", ""), argumentos.get("contenido", ""))

            elif nombre == "enviar_whatsapp":
                destinatario = argumentos.get("destinatario", "")
                mensaje = argumentos.get("mensaje", "")
                resultado = abrir_chat_con_mensaje(destinatario, mensaje)
                registrar_accion_sistema(f"whatsapp({destinatario})", resultado, "WHATSAPP")
                return resultado

            else:
                return f"Herramienta '{nombre}' no reconocida."

        except Exception as e:
            return f"Error al ejecutar '{nombre}': {e}"

    # ─── LOOP AGÉNTICO ──────────────────────────────────────────────────────
    def generar_respuesta(self, orden_usuario: str, max_iteraciones: int = 4) -> str:
        mensajes = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": orden_usuario},
        ]

        for _ in range(max_iteraciones):
            try:
                t0 = time.time()
                respuesta = self.client.chat.completions.create(
                    model=self.modelo,
                    messages=mensajes,
                    tools=HERRAMIENTAS,
                    tool_choice="auto",
                    temperature=0.3,
                    max_tokens=400,
                )
                print(f"[NIM] Tiempo: {time.time() - t0:.2f}s")
            except Exception as e:
                print(f"Error crítico en el Core de NIM: {e}")
                return "Error de comunicación con mi núcleo cognitivo en la nube."

            mensaje = respuesta.choices[0].message

            if mensaje.tool_calls:
                # El propio SDK espera que el mensaje del asistente con las
                # tool_calls se agregue tal cual al historial antes de las
                # respuestas de las herramientas.
                mensajes.append(mensaje)

                for tool_call in mensaje.tool_calls:
                    nombre_herramienta = tool_call.function.name
                    try:
                        argumentos = json.loads(tool_call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        argumentos = {}

                    print(f"[NimClient]: Ejecutando herramienta -> {nombre_herramienta}({argumentos})")
                    resultado_herramienta = self._ejecutar_herramienta(nombre_herramienta, argumentos)

                    mensajes.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": resultado_herramienta,
                    })
                    
                continue
            # No pidió más herramientas: esta es la respuesta final.
            return mensaje.content or "Listo, Señor."

        return "No pude completar la tarea en el número de pasos permitido, Señor. ¿Puede intentarlo de nuevo o dividirlo en pasos más simples?"

if __name__ == "__main__":
    cliente = NimClient()
    pruebas = [
        "crea una carpeta llamada Prueba en el escritorio",
        "investiga sobre los agujeros negros y guárdalo en tu memoria",
        "hola como estas",
    ]
    for p in pruebas:
        print(f"\n--- Orden: {p} ---")
        print(cliente.generar_respuesta(p))