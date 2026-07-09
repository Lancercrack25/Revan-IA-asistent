import os
import sys
import shutil
import subprocess
import psutil
import cv2

# Prevenir la generación de archivos .pyc
sys.dont_write_bytecode = True

try:
    import ollama
except ImportError:
    print("⚠️ La librería 'ollama' no está instalada. Ejecuta: pip install ollama")

from src.Database.conexion import obtener_conexion_pool, liberar_conexion


# --- DETECCIÓN DINÁMICA DE RUTA DEL ESCRITORIO ---

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


# --- AUDITORÍA Y REGISTRO ---

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
        print(f"❌ Error en OS Log: {e}")
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
        print(f"📁 [Estado]: Contexto de ruta actualizado -> {ruta_absoluta}")
        return True
    except Exception as e:
        print(f"❌ Error al guardar la ruta activa en BD: {e}")
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
        print(f"❌ Error al consultar la ruta activa: {e}")
        return ruta_defecto
    finally:
        liberar_conexion(conn)


# --- ACCIONES DE AUTOMATIZACIÓN DE CARPETAS ---

def abrir_carpeta_sistema(nombre_carpeta: str) -> str:
    """
    Busca la carpeta en el Escritorio (tolerante a mayúsculas/minúsculas),
    la abre en Windows Explorer y actualiza la ruta activa en PostgreSQL.
    """
    escritorio = obtener_ruta_escritorio()
    ruta_objetivo = os.path.join(escritorio, nombre_carpeta)

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
                if os.path.isdir(ruta_coincidencia):
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


def crear_carpeta_sistema(nombre_nueva_carpeta: str, ruta_base: str = "actual") -> str:
    """
    Crea una carpeta física.
    ruta_base admite:
      - "actual"    -> dentro del foco de trabajo activo (última ruta usada, en PostgreSQL)
      - "escritorio" / "desktop" -> directo en el Escritorio
      - "documentos" -> directo en Documentos
      - cualquier otra ruta absoluta -> se usa tal cual
    """
    nombre_nueva_carpeta = _sanear_nombre_carpeta(nombre_nueva_carpeta)
    base = (ruta_base or "actual").lower().strip()

    if base in ("", "actual"):
        ruta_padre = obtener_ruta_actual()
    elif base in ("escritorio", "desktop"):
        ruta_padre = obtener_ruta_escritorio()
    elif "documento" in base:
        ruta_padre = os.path.join(os.path.expanduser("~"), "Documents")
    elif os.path.isabs(ruta_base):
        ruta_padre = ruta_base
    else:
        # Ruta relativa desconocida: la tratamos como subcarpeta del Escritorio
        ruta_padre = os.path.join(obtener_ruta_escritorio(), ruta_base)

    ruta_final = os.path.join(ruta_padre, nombre_nueva_carpeta)

    try:
        os.makedirs(ruta_final, exist_ok=True)
        guardar_ruta_actual(ruta_final)

        nombre_padre = os.path.basename(ruta_padre) or ruta_padre
        return f"Hecho, Señor. Carpeta '{nombre_nueva_carpeta}' creada con éxito dentro de '{nombre_padre}'."
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


def analizar_entorno_vision() -> str:
    """Captura un fotograma de la webcam y lo analiza con el modelo LLaVA en Ollama."""
    print("📷 [REVAN Vision]: Activando sensor óptico...")
    
    # Usar CAP_DSHOW en Windows para apertura instantánea del driver
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) if os.name == 'nt' else cv2.VideoCapture(0)
    
    if not cap.isOpened():
        return "No pude acceder a la cámara, Señor. Verifique que no esté siendo usada por otra aplicación."

    ret, frame = cap.read()
    cap.release() # Liberar el dispositivo inmediatamente

    if not ret or frame is None:
        return "Error al capturar la imagen de la cámara."

    ruta_foto_temp = "temp_vision.jpg"
    cv2.imwrite(ruta_foto_temp, frame)

    try:
        print("🧠 [REVAN Vision]: Procesando análisis visual con LLaVA...")
        
        respuesta = ollama.chat(
            model='llava',
            messages=[{
                'role': 'user',
                'content': 'Describe brevemente en español y en una sola frase qué ves en esta imagen frente a la cámara.',
                'images': [ruta_foto_temp]
            }]
        )

        if os.path.exists(ruta_foto_temp):
            os.remove(ruta_foto_temp)

        analisis = respuesta['message']['content'].strip()
        print(f"👁️ [Análisis]: {analisis}")
        return f"Según mi sensor óptico: {analisis}"

    except Exception as e:
        if os.path.exists(ruta_foto_temp):
            os.remove(ruta_foto_temp)
        print(f"❌ Error en el módulo de visión: {e}")
        return "Tuve un problema al procesar la visión. Asegúrate de tener instalado el modelo 'llava' en Ollama ejecutando: ollama run llava"