import os
import subprocess

def desplegar_monitores_windows():
    """
    Invoca las herramientas oficiales de diagnóstico y rendimiento de Windows
    de manera asíncrona para no congelar el script principal.
    """
    try:    
        subprocess.Popen("resmon.exe", shell=True)
        print("🖥️ Ecosistema nativo de Windows desplegado correctamente.")
        return "Ecosistema nativo de Windows desplegado correctamente, Señor."
    except Exception as win_err:
        print(f"⚠️ Error al invocar herramientas de Windows: {win_err}")
        return "Error al abrir los monitores de diagnóstico."

def ejecutar_limpieza_sistema():
    """Abre el liberador de espacio en disco de Windows."""
    try:
        subprocess.Popen("cleanmgr.exe", shell=True)
        return "Abriendo el liberador de espacio en disco, Señor."
    except:
        return "No se pudo inicializar la limpieza del sistema."

def crear_carpeta_tactica(ruta_base, nombre_carpeta):
    """Crea una carpeta en Escritorio o Documentos de forma dinámica."""
    try:
        if "escritorio" in ruta_base.lower() or "desktop" in ruta_base.lower():
            ruta_final = os.path.join(os.path.expanduser("~"), "Desktop", nombre_carpeta)
        elif "documentos" in ruta_base.lower():
            ruta_final = os.path.join(os.path.expanduser("~"), "Documents", nombre_carpeta)
        else:
            ruta_final = os.path.join(ruta_base, nombre_carpeta)

        if not os.path.exists(ruta_final):
            os.makedirs(ruta_final)
            return f"Hecho, Señor. Carpeta '{nombre_carpeta}' creada con éxito."
        else:
            return f"Señor, la carpeta '{nombre_carpeta}' ya existe en esa ubicación."
    except Exception as e:
        return f"Error al intentar crear la carpeta: {str(e)}"

def ejecutar_aplicacion_office(aplicacion):
    """Lanza Microsoft Word, Excel o PowerPoint nativamente."""
    try:
        app = aplicacion.lower()
        if "word" in app:
            subprocess.Popen("start winword", shell=True)
            return "Desplegando Microsoft Word en este momento, Señor."
        elif "excel" in app:
            subprocess.Popen("start excel", shell=True)
            return "Inicializando hojas de cálculo de Microsoft Excel, Señor."
        elif "powerpoint" in app or "power" in app:
            subprocess.Popen("start powerpnt", shell=True)
            return "Abriendo Microsoft PowerPoint, Señor."
        else:
            return "Aplicación de Office no identificada."
    except Exception as e:
        return f"No se pudo inicializar Office: {str(e)}"

def reproducir_video_brave(url_o_busqueda):
    """Abre una URL o busca un video en YouTube forzando el navegador Brave."""
    try:
        if not url_o_busqueda.startswith("http"):
            url_final = f"https://www.youtube.com/results?search_query={url_o_busqueda.replace(' ', '+')}"
        else:
            url_final = url_o_busqueda

        subprocess.Popen(f'start brave "{url_final}"', shell=True)
        return "Abriendo la transmisión solicitada en el navegador Brave, Señor."
    except Exception as e:
        return f"Error al abrir Brave: {str(e)}"