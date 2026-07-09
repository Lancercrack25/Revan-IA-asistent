import os
import subprocess
from src.Services.os_service import obtener_ruta_escritorio

def lanzar_videojuego(nombre_juego):
    """Ejecuta tus videojuegos favoritos llamando a los accesos directos de tu Escritorio."""
    try:
        juego = nombre_juego.lower().strip()
        
        # Ruta base a tu carpeta física de 'Juegos' en el Escritorio
        ruta_juegos = os.path.join(obtener_ruta_escritorio(), "Juegos")
        
        # Mapeo exacto basado en tu lista de la captura
        mapeo_juegos = {
            "among us": "Among Us.lnk",
            "among": "Among Us.lnk",
            "devil may cry": "Devil May Cry 5.lnk",
            "dmc": "Devil May Cry 5.lnk",
            "fortnite": "Fortnite.lnk",
            "little nightmares": "Little Nightmares II.lnk",
            "marvel rivals": "Marvel Rivals.lnk",
            "marvel": "Marvel Rivals.lnk",
            "overwatch": "Overwatch.lnk",
            "peak": "PEAK.lnk",
            "repo": "R.E.P.O..lnk",
            "secret neighbor": "Secret Neighbor.lnk",
            "star wars": "STAR WARS™ Battlefront™ II.lnk",
            "battlefront": "STAR WARS™ Battlefront™ II.lnk",
            "seven deadly sins": "The Seven Deadly Sins Grand Cross.lnk",
            "7ds": "The Seven Deadly Sins Grand Cross.lnk"
        }
        
        if "minecraft" in juego:
            # Control especial para Minecraft por si acaso
            ruta_mc = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", ".minecraft", "launcher.exe")
            if os.path.exists(ruta_mc):
                subprocess.Popen(f'"{ruta_mc}"', shell=True)
                return "Iniciando bloques de Minecraft, Señor."
            else:
                subprocess.Popen("start minecraft:", shell=True)
                return "Ejecutando protocolo base para abrir Minecraft, Señor."

        # Buscar el juego en el mapa táctico de tu carpeta
        if juego in mapeo_juegos:
            archivo_final = os.path.join(ruta_juegos, mapeo_juegos[juego])
            if os.path.exists(archivo_final):
                subprocess.Popen(f'start "" "{archivo_final}"', shell=True)
                return f"Desplegando el entorno de combate para {nombre_juego}. Prepárese, Señor."
            else:
                return f"Señor, no localicé el archivo de acceso para {nombre_juego} en la carpeta Juegos."
                
        return f"Señor, el juego '{nombre_juego}' no está registrado en mis archivos tácticos."
        
    except Exception as e:
        return f"Fallo crítico al intentar abrir el juego: {str(e)}"