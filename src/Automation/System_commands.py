import subprocess

def desplegar_monitores_windows():
    """
    Invoca las herramientas oficiales de diagnóstico y rendimiento de Windows
    de manera asíncrona para no congelar el script principal.
    """
    try:    
        subprocess.Popen("resmon.exe", shell=True)
        
        print("🖥️ Ecosistema nativo de Windows desplegado correctamente.")
        return True
    except Exception as win_err:
        print(f"⚠️ Error al invocar herramientas de Windows: {win_err}")
        return False

def ejecutar_limpieza_sistema():
    """Ejemplo de otra tarea futura: Abre el liberador de espacio en disco."""
    try:
        subprocess.Popen("cleanmgr.exe", shell=True)
    except:
        pass