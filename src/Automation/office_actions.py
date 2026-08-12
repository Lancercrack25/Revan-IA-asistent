import subprocess

def ejecutar_aplicacion_office(aplicacion):
    """Lanza Microsoft Word, Excel o PowerPoint nativamente."""
    try:
        app = aplicacion.lower()
        if "word" in app:
            subprocess.Popen(["cmd", "/c", "start", "winword"], shell=False)
            return "Desplegando Microsoft Word en este momento, Señor."
        elif "excel" in app:
            subprocess.Popen(["cmd", "/c", "start", "excel"], shell=False)
            return "Inicializando hojas de cálculo de Microsoft Excel, Señor."
        elif "powerpoint" in app or "power" in app:
            subprocess.Popen(["cmd", "/c", "start", "powerpnt"], shell=False)
            return "Abriendo Microsoft PowerPoint, Señor."
        else:
            return "Aplicación de Office no identificada."
    except Exception as e:
        return f"No se pudo inicializar Office: {str(e)}"