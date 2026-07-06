import subprocess

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