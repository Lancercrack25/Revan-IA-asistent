import os
import subprocess

def obtener_ruta_escritorio():
    """Detecta de forma inteligente la ruta real del Escritorio, con o sin OneDrive."""
    ruta_normal = os.path.join(os.path.expanduser("~"), "Desktop")
    ruta_onedrive = os.path.join(os.path.expanduser("~"), "OneDrive", "Escritorio")
    ruta_onedrive_en = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
    
    if os.path.exists(ruta_onedrive):
        return ruta_onedrive
    elif os.path.exists(ruta_onedrive_en):
        return ruta_onedrive_en
    return ruta_normal

def abrir_carpeta_sistema(nombre_carpeta):
    """Busca y abre tus carpetas de trabajo y proyectos directamente en el Explorador de Windows."""
    try:
        carpeta = nombre_carpeta.lower().strip()
        escritorio = obtener_ruta_escritorio()
        
        # Mapeo exacto de las carpetas que tienes en tu Escritorio
        mapeo_carpetas = {
            "codigos": "Codigos programacion",
            "codigos programacion": "Codigos programacion",
            "programacion": "Codigos programacion",
            "portafolio": "Portafolio Trabajo",
            "portafolio trabajo": "Portafolio Trabajo",
            "proyectos": "Proyectos Uni y Personales",
            "universidad": "Proyectos Uni y Personales",
            "proyectos laboriosos": "Proyectos laboriosos",
            "juegos": "Juegos",
            "plataformas": "Plataformas"
        }
        
        if carpeta in mapeo_carpetas:
            ruta_final = os.path.join(escritorio, mapeo_carpetas[carpeta])
            
            if os.path.exists(ruta_final):
                # 'explorer' abre la carpeta nativamente en una ventana de Windows
                subprocess.Popen(f'explorer "{ruta_final}"', shell=True)
                return f"Abriendo la carpeta '{mapeo_carpetas[carpeta]}' en el explorador, Señor."
            else:
                return f"Señor, la ruta '{ruta_final}' no parece existir en el almacenamiento actual."
        
        return f"Señor, la carpeta '{nombre_carpeta}' no está mapeada en mis registros de archivos."
        
    except Exception as e:
        return f"Error al intentar desplegar el explorador de archivos: {str(e)}"

def crear_carpeta_tactica(ruta_base, nombre_carpeta):
    """Crea una carpeta en Escritorio o Documentos de forma dinámica e inteligente."""
    try:
        escritorio = obtener_ruta_escritorio()
        
        if "escritorio" in ruta_base.lower() or "desktop" in ruta_base.lower():
            ruta_final = os.path.join(escritorio, nombre_carpeta)
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