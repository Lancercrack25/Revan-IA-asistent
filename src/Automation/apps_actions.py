import os
import subprocess
from src.Services.os_service import obtener_ruta_escritorio

def lanzar_aplicacion_usuario(nombre_app):
    """Busca y ejecuta las plataformas o apps usando los accesos directos de tu Escritorio."""
    try:
        app = nombre_app.lower().strip()
        
        # Ruta base a tu carpeta física de 'Plataformas' en el Escritorio
        ruta_plataformas = os.path.join(obtener_ruta_escritorio(), "Plataformas")
        
        # Mapeo exacto basado en tu captura de pantalla
        mapeo_apps = {
            "anydesk": "AnyDesk.exe", # Este se ve como aplicación directa
            "battle net": "Battle.net.lnk",
            "curseforge": "CurseForge.lnk",
            "ea": "EA.lnk",
            "epic games": "Epic Games Launcher.lnk",
            "epic": "Epic Games Launcher.lnk",
            "netmarble": "Netmarble Launcher.lnk",
            "geforce now": "NVIDIA GeForce NOW.lnk",
            "nvidia": "NVIDIA.lnk",
            "steam": "Steam.lnk",
            "thunderstore": "Thunderstore Mod Manager.lnk",
            "unity": "Unity Hub.lnk",
            "xbox": "Xbox.lnk",
            "zerotier": "ZeroTier.lnk",
            "launcher": "Minecraft Launcher"
        }
        
        # Apps globales estándar que Windows abre directo
        if "discord" in app:
            subprocess.Popen("start discord", shell=True)
            return "Desplegando Discord y conectando a los canales de voz, Señor."
        elif "whatsapp" in app:
            subprocess.Popen("start whatsapp", shell=True)
            return "Abriendo la interfaz de mensajería de WhatsApp, Señor."
        # Intentar buscar en tu carpeta de Plataformas
        if app in mapeo_apps:
            archivo_final = os.path.join(ruta_plataformas, mapeo_apps[app])
            if os.path.exists(archivo_final):
                subprocess.Popen(f'start "" "{archivo_final}"', shell=True)
                return f"Inicializando la plataforma {nombre_app} desde su cuadrante, Señor."
            else:
                return f"Señor, el acceso directo de {nombre_app} no se encuentra en la carpeta Plataformas."
                
        # Intento genérico de emergencia
        subprocess.Popen(f"start {app}", shell=True)
        return f"Intentando forzar la ejecución externa de {nombre_app}, Señor."
        
    except Exception as e:
        return f"No se pudo inicializar la aplicación debido a un error: {str(e)}"