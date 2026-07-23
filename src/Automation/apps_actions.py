import os
import subprocess
from src.Services.os_service import obtener_ruta_escritorio
from src.Automation.games_actions import _normalizar, _listar_accesos, _buscar_mejor_coincidencia


# Apps que se abren mejor con el protocolo/comando propio de Windows en vez
# de buscar un acceso directo (más confiable para estas dos en particular).
APPS_PROTOCOLO_ESPECIAL = {
    "discord": "start discord",
    "whatsapp": "start whatsapp",
    "anydesk": "AnyDesk.exe", 
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
                    "launcher": "Minecraft Launcher.lnk"
}

def lanzar_aplicacion_usuario(nombre_app: str) -> str:
    """
    Escanea Escritorio/Plataformas/ en tiempo real y lanza la que mejor
    coincida con lo pedido. Ya NO requiere editar código para agregar
    plataformas nuevas: basta con poner el acceso directo en esa carpeta.
    Reutiliza el mismo motor de búsqueda tolerante que games_actions.py,
    para no duplicar la lógica de coincidencia en dos archivos.
    """
    app_normalizada = _normalizar(nombre_app)

    for clave, comando in APPS_PROTOCOLO_ESPECIAL.items():
        if clave in app_normalizada:
            try:
                subprocess.Popen(comando, shell=True)
                return f"Desplegando {nombre_app}, Señor."
            except Exception as e:
                return f"No se pudo abrir {nombre_app}: {str(e)}"

    carpeta_plataformas = os.path.join(obtener_ruta_escritorio(), "Plataformas")
    accesos = _listar_accesos(carpeta_plataformas)
    ruta_encontrada = _buscar_mejor_coincidencia(nombre_app, accesos) if accesos else None

    if ruta_encontrada:
        try:
            subprocess.Popen(f'start "" "{ruta_encontrada}"', shell=True)
            nombre_mostrado = os.path.splitext(os.path.basename(ruta_encontrada))[0]
            return f"Inicializando la plataforma {nombre_mostrado} desde su cuadrante, Señor."
        except Exception as e:
            return f"No se pudo inicializar {nombre_app}: {str(e)}"

    # Intento genérico de emergencia (por si Windows reconoce el nombre directo)
    try:
        subprocess.Popen(f"start {app_normalizada}", shell=True)
        return f"Intentando forzar la ejecución externa de {nombre_app}, Señor."
    except Exception as e:
        return f"No se pudo inicializar la aplicación debido a un error: {str(e)}"