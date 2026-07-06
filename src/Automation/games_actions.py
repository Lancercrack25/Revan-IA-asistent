import os
import subprocess

def lanzar_videojuego(nombre_juego):
    """Mapea y ejecuta tus videojuegos preferidos mediante rutas absolutas o de launcher."""
    try:
        juego = nombre_juego.lower().strip()
        
        if "minecraft" in juego:
            ruta_mc = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", ".minecraft", "launcher.exe")
            if os.path.exists(ruta_mc):
                subprocess.Popen(f'"{ruta_mc}"', shell=True)
                return "Iniciando el entorno de bloques de Minecraft, Señor. Prepárese."
            else:
                # Si usas el launcher oficial moderno de la tienda de Windows
                subprocess.Popen("start minecraft:", shell=True)
                return "Ejecutando protocolo para abrir Minecraft, Señor."
                
        elif "steam" in juego:
            subprocess.Popen(r'"C:\Program Files (x86)\Steam\Steam.exe"', shell=True)
            return "Abriendo la central táctica de Steam, Señor."
            
        elif "lol" in juego or "league" in juego:
            subprocess.Popen(r'"C:\Riot Games\Riot Client\RiotClientServices.exe"', shell=True)
            return "Desplegando cliente de Riot Games para League of Legends, Señor."
            
        else:
            return f"Señor, el juego '{nombre_juego}' no está mapeado en mi base de datos de combate."
    except Exception as e:
        return f"Fallo crítico al intentar abrir el juego: {str(e)}"