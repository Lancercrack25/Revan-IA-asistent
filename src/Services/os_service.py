import os
import sys
import shutil
import subprocess
import time
import base64
import psutil
import cv2

sys.dont_write_bytecode = True

# Cliente OpenAI para los endpoints de NVIDIA NIM
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Cliente de Gemini como respaldo opcional
try:
    from google import genai
except ImportError:
    genai = None

from src.Database.conexion import obtener_conexion_pool, liberar_conexion
from src.Core.Config_loader import cargar_credenciales


def obtener_ruta_escritorio() -> str:
    """Detecta de forma inteligente la ruta real del Escritorio, con o sin OneDrive."""
    ruta_normal = os.path.join(os.path.expanduser("~"), "Desktop")
    ruta_onedrive = os.path.join(os.path.expanduser("~"), "OneDrive", "Escritorio")
    ruta_onedrive_en = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
    
    if os.path.exists(ruta_onedrive):
        return ruta_onedrive
    elif os.path.exists(ruta_onedrive_en):
        return ruta_onedrive_en
    return ruta_normal


def normalizar_si_apunta_a_escritorio(ruta_absoluta: str) -> str:
    home = os.path.realpath(os.path.expanduser("~"))
    ruta_resuelta = os.path.realpath(ruta_absoluta)

    if not ruta_resuelta.startswith(home):
        return ruta_absoluta

    resto = ruta_resuelta[len(home):].lstrip(os.sep)
    partes = resto.split(os.sep) if resto else []

    if partes and partes[0].lower() in ("desktop", "escritorio"):
        subcarpetas_extra = partes[1:]
        if subcarpetas_extra:
            return os.path.join(obtener_ruta_escritorio(), *subcarpetas_extra)
        return obtener_ruta_escritorio()
    return ruta_absoluta

def registrar_accion_sistema(orden: str, respuesta: str, accion_tipo: str) -> bool:
    """Audita y registra las acciones ejecutadas sobre el sistema operativo."""
    if not orden.strip() or not respuesta.strip():
        return False

    conn = obtener_conexion_pool()
    if not conn:
        return False
    try:
        cur = conn.cursor()
        query = """
            INSERT INTO historial_interacciones (orden_usuario, respuesta_revan, accion_ejecutada)
            VALUES (%s, %s, %s);
        """
        cur.execute(query, (orden.strip(), respuesta.strip(), accion_tipo.upper()))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"Error en OS Log: {e}")
        conn.rollback()
        return False
    finally:
        liberar_conexion(conn)
# --- GESTIÓN DE ESTADO DE CARPETAS (CONTEXTO ACTIVO) ---
def guardar_ruta_actual(ruta_absoluta: str) -> bool:
    """Registra en PostgreSQL la última carpeta sobre la cual operó el usuario."""
    conn = obtener_conexion_pool()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        query = """
            INSERT INTO estado_sistema (clave, valor, actualizado_en)
            VALUES ('ultima_ruta', %s, CURRENT_TIMESTAMP)
            ON CONFLICT (clave) 
            DO UPDATE SET valor = EXCLUDED.valor, actualizado_en = CURRENT_TIMESTAMP;
        """
        cur.execute(query, (ruta_absoluta,))
        conn.commit()
        cur.close()
        print(f"[Estado]: Contexto de ruta actualizado -> {ruta_absoluta}")
        return True
    except Exception as e:
        print(f"Error al guardar la ruta activa en BD: {e}")
        conn.rollback()
        return False
    finally:
        liberar_conexion(conn)


def obtener_ruta_actual() -> str:
    """Obtiene la última carpeta activa desde PostgreSQL. Si no hay, retorna el Escritorio real."""
    ruta_defecto = obtener_ruta_escritorio()
    conn = obtener_conexion_pool()
    if not conn:
        return ruta_defecto

    try:
        cur = conn.cursor()
        cur.execute("SELECT valor FROM estado_sistema WHERE clave = 'ultima_ruta';")
        resultado = cur.fetchone()
        cur.close()

        if resultado and os.path.exists(resultado[0]):
            return resultado[0]
        return ruta_defecto
    except Exception as e:
        print(f"Error al consultar la ruta activa: {e}")
        return ruta_defecto
    finally:
        liberar_conexion(conn)


def abrir_carpeta_sistema(nombre_carpeta: str) -> str:
    escritorio = obtener_ruta_escritorio()
    ruta_objetivo = os.path.join(escritorio, nombre_carpeta)

    if not _es_ruta_base_segura(ruta_objetivo):
        return (
            f"Señor, no voy a abrir '{nombre_carpeta}' porque la ruta resultante "
            f"queda fuera de su carpeta de usuario."
        )

    # 1. Intento directo
    if os.path.exists(ruta_objetivo) and os.path.isdir(ruta_objetivo):
        os.startfile(ruta_objetivo)
        guardar_ruta_actual(ruta_objetivo)
        return f"Carpeta '{nombre_carpeta}' abierta exitosamente. Foco de trabajo actualizado."

    # 2. Búsqueda insensible a mayúsculas/minúsculas en el Escritorio
    try:
        for elemento in os.listdir(escritorio):
            if elemento.lower() == nombre_carpeta.lower():
                ruta_coincidencia = os.path.join(escritorio, elemento)
                if os.path.isdir(ruta_coincidencia) and _es_ruta_base_segura(ruta_coincidencia):
                    os.startfile(ruta_coincidencia)
                    guardar_ruta_actual(ruta_coincidencia)
                    return f"Carpeta '{elemento}' localizada y abierta exitosamente."
    except Exception as e:
        print(f"Error en búsqueda secundaria: {e}")
    return f"Negativo, Señor. No se localizó la carpeta '{nombre_carpeta}' en el Escritorio."

def _sanear_nombre_carpeta(nombre: str) -> str:
    """Quita caracteres inválidos en rutas de Windows para evitar que os.makedirs falle."""
    invalidos = '<>:"/\\|?*'
    limpio = "".join(c for c in nombre if c not in invalidos).strip()
    return limpio or "Contenedor_Táctico"

def _es_ruta_base_segura(ruta_absoluta: str) -> bool:
    """Delegado a src/Security/sanitizador.py -una sola fuente de verdad
    para 'qué ruta es segura para escribir archivos', reutilizada también
    por System_commands.py."""
    from src.Security.sanitizador import es_ruta_segura
    return es_ruta_segura(ruta_absoluta)

def crear_carpeta_sistema(nombre_nueva_carpeta: str, ruta_base: str = "actual") -> str:
    nombre_nueva_carpeta = _sanear_nombre_carpeta(nombre_nueva_carpeta)
    base = (ruta_base or "actual").lower().strip()
    if "escritorio" in base or "desktop" in base:
        ruta_padre = obtener_ruta_escritorio()
    elif "documento" in base:
        ruta_padre = os.path.join(os.path.expanduser("~"), "Documents")
    elif base in ("", "actual"):
        ruta_padre = obtener_ruta_actual()
    elif os.path.isabs(ruta_base):
        if not _es_ruta_base_segura(ruta_base):
            from src.Security.auditoria import registrar_evento, NIVEL_ADVERTENCIA
            registrar_evento(
                modulo="os_service",
                accion="crear_carpeta_sistema",
                resultado=f"Ruta rechazada por estar fuera del directorio del usuario: '{ruta_base}'",
                nivel=NIVEL_ADVERTENCIA,
            )
            return (
                f"Señor, no voy a crear nada en '{ruta_base}' porque está fuera de su "
                f"carpeta de usuario. Dígame que la cree en Escritorio, Documentos, o en "
                f"la carpeta actual."
            )
        ruta_padre = ruta_base
        ruta_padre = normalizar_si_apunta_a_escritorio(ruta_padre)
    else:
        ruta_padre = os.path.join(obtener_ruta_escritorio(), ruta_base)

    ruta_final = os.path.join(ruta_padre, nombre_nueva_carpeta)
    print(f"[CrearCarpeta] ruta recibida del modelo: {ruta_base!r} -> ruta final: {ruta_final}")

    try:
        os.makedirs(ruta_final, exist_ok=True)
        guardar_ruta_actual(ruta_final)
        return f"Hecho, Señor. Carpeta '{nombre_nueva_carpeta}' creada con éxito en: {ruta_final}"
    except Exception as e:
        return f"Error al intentar crear el directorio físico: {e}"


# --- HERRAMIENTAS DE MANTENIMIENTO Y TELEMETRÍA ---

def ejecutar_limpieza_sistema() -> str:
    """Limpia los archivos temporales de Windows para liberar caché."""
    ruta_temp = os.environ.get("TEMP")
    archivos_eliminados = 0

    if not ruta_temp or not os.path.exists(ruta_temp):
        return "No se pudo acceder a la ruta de archivos temporales."

    for elemento in os.listdir(ruta_temp):
        ruta_completa = os.path.join(ruta_temp, elemento)
        try:
            if os.path.isfile(ruta_completa) or os.path.islink(ruta_completa):
                os.unlink(ruta_completa)
                archivos_eliminados += 1
            elif os.path.isdir(ruta_completa):
                shutil.rmtree(ruta_completa)
        except Exception:
            continue

    return f"Purga de sistema completada. Se eliminaron {archivos_eliminados} elementos del directorio temporal."


def obtener_diagnostico_hardware() -> str:
    """Extrae consumo de CPU, Memoria RAM y espacio en Disco."""
    try:
        uso_cpu = psutil.cpu_percent(interval=0.5)
        uso_ram = psutil.virtual_memory().percent
        uso_disco = psutil.disk_usage('C:').percent
        return f"Diagnóstico físico: CPU al {uso_cpu}%, Memoria RAM al {uso_ram}% y Disco C ocupado al {uso_disco}%."
    except Exception as e:
        return f"Error al leer sensores de rendimiento: {e}"

# --- MÓDULO DE VISIÓN NATIVE API (NVIDIA NIM / GEMINI FALLBACK) ---
def _analizar_frame_con_llava(frame) -> str:
    try:
        creds = cargar_credenciales() or {}
        # Detectar la clave de NVIDIA considerando tu nombre en el config ("NVIDIA_NIM_API_KEY")
        nvidia_key = (
            creds.get("NVIDIA_NIM_API_KEY") 
            or creds.get("NVIDIA_API_KEY") 
            or os.getenv("NVIDIA_NIM_API_KEY") 
            or os.getenv("NVIDIA_API_KEY")
        )
        
        gemini_key = creds.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

        # 1. Codificar el frame a Base64 JPEG en memoria
        _, buffer = cv2.imencode('.jpg', frame)
        base64_image = base64.b64encode(buffer).decode('utf-8')
        
        prompt_texto = (
            "Estás viendo una imagen capturada por la webcam de una PC de escritorio. "
            "Describe en español, en una sola frase breve, ÚNICAMENTE lo que puedas "
            "confirmar con certeza que aparece en la imagen. "
            "Sé literal y conservador: si la imagen está oscura, borrosa, muestra solo una "
            "pared o un espacio vacío, o no puedes identificar el contenido con certeza, "
            "dilo explícitamente (por ejemplo: 'La imagen no muestra nada identificable con "
            "claridad'). No inventes personas, objetos, ni escenas que no estén realmente "
            "visibles. No asumas contexto externo: esta es la webcam de una computadora, no "
            "una cámara de seguridad exterior, así que no describas entradas, calles ni "
            "repartidores a menos que literalmente se vean en la imagen."
        )

        # INTENTO 1: NVIDIA NIM API (Llama 3.2 11B Vision)
        if nvidia_key and OpenAI:
            print(" [REVAN Vision]: Procesando análisis con NVIDIA NIM API (Llama 3.2 Vision)...")
            client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=nvidia_key
            )

            response = client.chat.completions.create(
                model="meta/llama-3.2-11b-vision-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_texto},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=150,
                temperature=0.2
            )
            analisis = response.choices[0].message.content.strip()
            print(f" [Análisis NVIDIA]: {analisis}")
            return f"Según mi sensor óptico: {analisis}"

        # INTENTO 2: GEMINI API (Fallback si falla NVIDIA)
        elif gemini_key and genai:
            print(" [REVAN Vision]: Procesando análisis con Gemini API...")
            client = genai.Client(api_key=gemini_key)
            imagen_data = {
                "mime_type": "image/jpeg",
                "data": buffer.tobytes()
            }
            respuesta = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[prompt_texto, imagen_data]
            )
            analisis = respuesta.text.strip()
            print(f" [Análisis Gemini]: {analisis}")
            return f"Según mi sensor óptico: {analisis}"

        else:
            return "No se detectaron claves válidas para NVIDIA_NIM_API_KEY o GEMINI_API_KEY en la configuración."

    except Exception as e:
        print(f" Error en el módulo de visión API: {e}")
        return f"Error al procesar la imagen con el servicio de visión: {e}"

def analizar_entorno_vision() -> str:
    from src.Camara.open_camera import revan_cam

    return revan_cam.capturar_y_analizar(duracion_segundos=3.0)