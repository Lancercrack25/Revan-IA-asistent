import os
import json
import time
import re

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
    buscar_en_navegador_sistema,
    reproducir_video_brave,
    lanzar_aplicacion_usuario,
    lanzar_videojuego,
    desplegar_monitores_windows,
    ejecutar_aplicacion_office,
    crear_y_abrir_documento_word,
)
from src.Database.conexion import obtener_conexion_pool, liberar_conexion
from src.Phone.whats import abrir_chat_con_mensaje

HERRAMIENTAS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_en_navegador",
            "description": "Abre el navegador web de Windows y busca cualquier término en Google.",
            "parameters": {
                "type": "object",
                "properties": {
                    "consulta": {"type": "string", "description": "El término a buscar"}
                },
                "required": ["consulta"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reproducir_video",
            "description": "Abre YouTube en el navegador y reproduce el video solicitado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "busqueda": {"type": "string", "description": "Video a buscar en YouTube"}
                },
                "required": ["busqueda"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crear_documento_word",
            "description": "Crea un archivo de Word (.docx) redactando información sobre una temática solicitada y guardándolo en la carpeta indicada.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_archivo": {"type": "string", "description": "Nombre del archivo (ej. 'Minecraft_Info.docx')"},
                    "contenido_o_tema": {"type": "string", "description": "Resumen, información o texto que debe ir redactado DENTRO del archivo Word."},
                    "carpeta_destino": {"type": "string", "description": "Nombre de la carpeta donde se debe guardar (ej. 'pruebas')."}
                },
                "required": ["nombre_archivo", "contenido_o_tema"],
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "lanzar_videojuego",
            "description": "Lanza un videojuego o ejecutable desde la carpeta Juegos del usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_juego": {
                        "type": "string",
                        "description": "Nombre del videojuego a ejecutar (ej: Minecraft, GTA V)"
                    }
                },
                "required": ["nombre_juego"]
            },
        },
    },

    {
        "type": "function",
        "function": {
            "name": "abrir_aplicacion",
            "description": "Abre un programa instalado en Windows como la calculadora, bloc de notas, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre del programa a abrir"}
                },
                "required": ["nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crear_carpeta",
            "description": "Crea una nueva carpeta en el sistema de archivos del usuario.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre de la carpeta"},
                    "ruta": {
                        "type": "string",
                        "enum": ["actual", "escritorio", "documentos"],
                        "description": "Ubicación de creación. Por defecto 'escritorio'.",
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
            "description": "Abre una carpeta existente en el explorador de archivos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre de la carpeta"}
                },
                "required": ["nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "abrir_office",
            "description": "Abre la aplicación de Microsoft Word o Excel vacía.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app": {"type": "string", "enum": ["word", "excel"]}
                },
                "required": ["app"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "mostrar_monitor_recursos",
            "description": "Despliega el Administrador de tareas.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "diagnostico_hardware",
            "description": "Obtiene métricas de CPU, RAM y disco.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "limpiar_sistema",
            "description": "Elimina archivos temporales de Windows.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analizar_camara",
            "description": "Activa la cámara web y describe lo que ve.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "guardar_nota",
            "description": "Guarda una nota en la base de datos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "clave": {"type": "string", "description": "Clave del dato"},
                    "contenido": {"type": "string", "description": "Contenido a almacenar"}
                },
                "required": ["clave", "contenido"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "enviar_whatsapp",
            "description": "Abre un chat de WhatsApp Web con un mensaje preescrito.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destinatario": {"type": "string", "description": "Contacto o número"},
                    "mensaje": {"type": "string", "description": "Texto del mensaje"}
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
            raise ValueError("Falta la API key de NVIDIA NIM.")

        self.modelo = modelo
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key,
        )
        self.system_prompt = (
            "Eres REVAN, asistente de inteligencia artificial avanzado estilo JARVIS.\n"
            "COMPORTAMIENTO:\n"
            "1. Te diriges al usuario como 'Señor'. Responde de forma concisa (1 o 2 oraciones).\n"
            "2. Jamás menciones rutas de archivos largas. Di 'en su escritorio' o 'en la carpeta X'.\n"
            "3. OBLIGATORIO: Selecciona y ejecuta la herramienta adecuada para cada acción requerida.\n\n"
            "INSTRUCCIÓN CRÍTICA DE EJECUCIÓN:\n"
            "- Tienes herramientas (functions/tools) integradas para controlar la PC.\n"
            "- Cuando el usuario te pida abrir, lanzar o ejecutar un juego o aplicación (ej. 'Abre Minecraft', 'Abre Discord'), NUNCA le des instrucciones de cómo hacerlo él mismo.\n"
            "- DEBES invocar inmediatamente la herramienta correspondiente (lanzar_videojuego o lanzar_aplicacion_usuario por ejemplo).\n"
        )
        

        self.historial = [{"role": "system", "content": self.system_prompt}]

    def _limpiar_para_voz(self, texto: str) -> str:
        if not texto: return ""
        texto = re.sub(r'[A-Za-z]:\\[^ \n]+', 'su equipo', texto)
        texto = texto.replace("_", " ").replace("%", " por ciento")
        return texto.strip()

    def _guardar_nota(self, clave: str, contenido: str) -> str:
        if not clave or not contenido:
            return "Se requiere una clave y un contenido para registrar la nota."

        conn = obtener_conexion_pool()
        if not conn:
            return "Sin acceso a la base de datos en este momento."

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
            return f"Nota '{clave}' registrada en la base de datos."
        except Exception as e:
            conn.rollback()
            return f"Error guardando nota: {e}"
        finally:
            liberar_conexion(conn)

    def _ejecutar_herramienta(self, nombre: str, argumentos: dict) -> str:
        try:
            if nombre == "buscar_en_navegador":
                consulta = argumentos.get("consulta", "")
                resultado = buscar_en_navegador_sistema(consulta)
                registrar_accion_sistema(f"buscar_navegador({consulta})", resultado, "NAV_SEARCH")
                return resultado

            elif nombre == "reproducir_video":
                busqueda = argumentos.get("busqueda", "")
                resultado = reproducir_video_brave(busqueda)
                registrar_accion_sistema(f"video({busqueda})", resultado, "VIDEO")
                return resultado

            elif nombre == "crear_documento_word":
                nombre_doc = argumentos.get("nombre_archivo", "Documento.docx")
                tema = argumentos.get("contenido_o_tema", "Información general.")
                carpeta = argumentos.get("carpeta_destino", "")
                resultado = crear_y_abrir_documento_word(nombre_doc, tema, carpeta)
                registrar_accion_sistema(f"word({nombre_doc})", resultado, "WORD")
                return resultado

            elif nombre == "abrir_videojuego":
                juego_nombre = argumentos.get("nombre", "")
                resultado = lanzar_videojuego(juego_nombre)
                registrar_accion_sistema(f"juego({juego_nombre})", resultado, "JUEGO")
                return resultado

            elif nombre == "abrir_aplicacion":
                app_nombre = argumentos.get("nombre", "")
                resultado = lanzar_aplicacion_usuario(app_nombre)
                registrar_accion_sistema(f"app({app_nombre})", resultado, "APP")
                return resultado

            elif nombre == "crear_carpeta":
                nombre_c = (argumentos.get("nombre") or "Nueva_Carpeta").strip()
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
                ejecutar_aplicacion_office(app_tipo)
                resultado = f"Microsoft {app_tipo.capitalize()} abierto."
                registrar_accion_sistema(f"abrir_office({app_tipo})", resultado, "OFFICE")
                return resultado

            elif nombre == "mostrar_monitor_recursos":
                desplegar_monitores_windows()
                resultado = "Administrador de recursos abierto."
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

            elif nombre == "guardar_nota":
                return self._guardar_nota(argumentos.get("clave", ""), argumentos.get("contenido", ""))

            elif nombre == "enviar_whatsapp":
                destinatario = argumentos.get("destinatario", "")
                mensaje = argumentos.get("mensaje", "")
                resultado = abrir_chat_con_mensaje(destinatario, mensaje)
                registrar_accion_sistema(f"whatsapp({destinatario})", resultado, "WHATSAPP")
                return resultado

            else:
                return f"La herramienta '{nombre}' no está configurada."

        except Exception as e:
            return f"Error ejecutando '{nombre}': {e}"

    def generar_respuesta(self, orden_usuario: str, max_iteraciones: int = 4) -> str:
        self.historial.append({"role": "user", "content": orden_usuario})

        if len(self.historial) > 16:
            self.historial = [self.historial[0]] + self.historial[-15:]

        for _ in range(max_iteraciones):
            try:
                t0 = time.time()
                respuesta = self.client.chat.completions.create(
                    model=self.modelo,
                    messages=self.historial,
                    tools=HERRAMIENTAS,
                    tool_choice="auto",
                    temperature=0.2,
                    max_tokens=300,
                )
                print(f"[NIM] Tiempo de respuesta: {time.time() - t0:.2f}s")
            except Exception as e:
                print(f"Error crítico en el cliente NIM: {e}")
                return "Tuve un error al procesar la orden en mi núcleo."

            mensaje = respuesta.choices[0].message

            if mensaje.tool_calls:
                self.historial.append(mensaje)

                for tool_call in mensaje.tool_calls:
                    nombre_herramienta = tool_call.function.name
                    try:
                        argumentos = json.loads(tool_call.function.arguments or "{}")
                    except json.JSONDecodeError:
                        argumentos = {}

                    print(f"[NimClient] Ejecutando Herramienta -> {nombre_herramienta}({argumentos})")
                    resultado = self._ejecutar_herramienta(nombre_herramienta, argumentos)

                    self.historial.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": resultado,
                    })

                continue

            respuesta_final = self._limpiar_para_voz(mensaje.content or "A sus órdenes, Señor.")
            self.historial.append({"role": "assistant", "content": respuesta_final})
            return respuesta_final

        res_limite = "He completado la solicitud, Señor."
        self.historial.append({"role": "assistant", "content": res_limite})
        return res_limite