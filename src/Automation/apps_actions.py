import subprocess

def lanzar_aplicacion_usuario(nombre_app):
    """Lanza aplicaciones cotidianas instaladas en el sistema."""
    try:
        app = nombre_app.lower().strip()
        if "discord" in app:
            subprocess.Popen("start discord", shell=True)
            return "Abriendo Discord y conectando a los servidores de voz, Señor."
        elif "whatsapp" in app:
            subprocess.Popen("start whatsapp", shell=True)
            return "Desplegando entorno de mensajería de WhatsApp, Señor."
        elif "spotify" in app:
            subprocess.Popen("start spotify", shell=True)
            return "Inicializando flujo de frecuencias musicales en Spotify, Señor."
        else:
            # Intento genérico si el software está registrado en la consola de Windows
            subprocess.Popen(f"start {app}", shell=True)
            return f"Intentando forzar la ejecución de {nombre_app}, Señor."
    except Exception as e:
        return f"No se pudo inicializar la aplicación: {str(e)}"