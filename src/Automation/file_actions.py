import os

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