import sys
import os
import shutil
import subprocess
import psutil
import ollama  # Aseguramos que esté disponible para visión
from src.Camara.open_camera import capturar_pantallazo_camara  
from src.Database.conexion import obtener_conexion

sys.dont_write_bytecode = True  # Evita archivos .pyc

# --- FUNCIÓN DE LOGS EXISTENTE ---
def registrar_accion_sistema(orden: str, respuesta: str, accion_tipo: str):
    """Registra en PostgreSQL las acciones ejecutadas en el S.O."""
    if not orden.strip() or not respuesta.strip():
        return False
    conn = obtener_conexion()
    if not conn: return False
    try:
        cur = conn.cursor()
        query = "INSERT INTO historial_interacciones (orden_usuario, respuesta_revan, accion_ejecutada) VALUES (%s, %s, %s);"
        cur.execute(query, (orden.strip(), respuesta.strip(), accion_tipo.upper()))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"❌ Error en OS Log: {e}")
        return False
    finally:
        conn.close()

# --- 🔥 NUEVOS IMPLEMENTOS TÁCTICOS ---

def ejecutar_limpieza_sistema():
    """
    Purga la carpeta de archivos temporales de Windows para optimizar rendimiento.
    """
    ruta_temp = os.environ.get("TEMP")
    archivos_eliminados = 0
    carpetas_eliminadas = 0
    
    if not ruta_temp or not os.path.exists(ruta_temp):
        return "No se pudo localizar el sector de archivos temporales."

    for elemento in os.listdir(ruta_temp):
        ruta_completa = os.path.join(ruta_temp, elemento)
        try:
            if os.path.isfile(ruta_completa) or os.path.islink(ruta_completa):
                os.unlink(ruta_completa)
                archivos_eliminados += 1
            elif os.path.isdir(ruta_completa):
                shutil.rmtree(ruta_completa)
                carpetas_eliminadas += 1
        except Exception:
            # Muchos archivos temporales están bloqueados porque Windows los usa en vivo, se ignoran de forma segura
            continue
            
    return f"Mantenimiento completado, Señor. Se purgaron {archivos_eliminados} archivos y {carpetas_eliminadas} directorios corruptos de la memoria temporal."


def obtener_diagnostico_hardware():
    """
    Extrae los datos reales de carga de la CPU, RAM y espacio en disco duro.
    """
    try:
        uso_cpu = psutil.cpu_percent(interval=0.5)
        uso_ram = psutil.virtual_memory().percent
        disco = psutil.disk_usage('C:')
        uso_disco = disco.percent
        
        reporte = (
            f"Diagnóstico de hardware completado. Carga de CPU al {uso_cpu}%. "
            f"Consumo de memoria RAM al {uso_ram}%. "
            f"Almacenamiento del Disco Local C ocupado al {uso_disco}%."
        )
        return reporte
    except Exception as e:
        return f"Error al leer los sensores de telemetría física: {e}"


def buscar_archivo_en_escritorio(nombre_archivo: str):
    """
    Escanea el escritorio real buscando coincidencias con un archivo específico.
    """
    escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
    coincidencias = []
    
    if not os.path.exists(escritorio):
        return "No se pudo acceder al sector del escritorio."

    for raiz, _, archivos in os.walk(escritorio):
        for archivo in archivos:
            if nombre_archivo.lower() in archivo.lower():
                coincidencias.append(archivo)
                
    if coincidencias:
        lista_archivos = ", ".join(coincidencias[:3]) # Limitamos a mostrar los 3 primeros
        return f"Afirmativo, Señor. Encontré archivos que coinciden en el escritorio: {lista_archivos}."
    else:
        return f"Negativo, Señor. No localicé ningún archivo con el nombre '{nombre_archivo}' en el escritorio."

def analizar_entorno_vision():
    """
    Dispara la captura de la cámara y procesa la imagen de forma local 
    usando un modelo de visión eficiente en Ollama.
    """
    # 1. Tomamos la foto instantánea
    ruta_imagen = capturar_pantallazo_camara()
    if not ruta_imagen or not os.path.exists(ruta_imagen):
        return "Negativo, Señor. No se pudo inicializar el hardware óptico o capturar la imagen."
        
    print("👁️ [REVAN Visión]: Procesando matriz de pixeles con Ollama...")
    
    try:
        # 2. Le enviamos la imagen a Ollama. 
        # NOTA: Requiere tener instalado un modelo de visión como 'llava' o 'qwen2.5-vision'
        respuesta = ollama.chat(
            model='llava:7b', # Cambia al modelo de visión que descargues con 'ollama run llava'
            messages=[{
                'role': 'user',
                'content': '¿Qué estás viendo en esta imagen? Sé breve, directo y responde en español.',
                'images': [ruta_imagen]
            }]
        )
        
        descripcion = respuesta['message']['content'].strip()
        
        # 3. Limpieza: Borramos la foto del disco para no acumular basura en el proyecto
        if os.path.exists(ruta_imagen):
            os.remove(ruta_imagen)
            
        return f"Análisis óptico completado: {descripcion}"
        
    except Exception as e:
        print(f"❌ Error en análisis de visión: {e}")
        return "Error en el procesamiento síncronico de mi núcleo de visión local."