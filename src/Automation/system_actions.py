import subprocess

def desplegar_monitores_windows():
    """Invoca las herramientas oficiales de diagnóstico y rendimiento de Windows."""
    try:    
        subprocess.Popen("resmon.exe", shell=True)
        print("🖥️ Ecosistema nativo de Windows desplegado correctamente.")
        return "Ecosistema nativo de Windows desplegado correctamente, Señor."
    except Exception as win_err:
        print(f"⚠️ Error al invocar herramientas de Windows: {win_err}")
        return "Error al abrir los monitores de diagnóstico."
