import os
import sys
import webbrowser
import subprocess

sys.dont_write_bytecode = True

# Importaciones relativas originales
try:
    from .system_actions import desplegar_monitores_windows
    from .office_actions import ejecutar_aplicacion_office
    from .browser_actions import reproducir_video_brave as _reproducir_original
    from .apps_actions import lanzar_aplicacion_usuario as _lanzar_app_original
    from .games_actions import lanzar_videojuego as _lanzar_juego_original
except ImportError:
    desplegar_monitores_windows = None
    ejecutar_aplicacion_office = None
    _reproducir_original = None
    _lanzar_app_original = None
    _lanzar_juego_original = None


def reproducir_video_brave(busqueda: str):
    """Abre el navegador con la búsqueda especificada (respaldo con el navegador predeterminado/Brave)."""
    try:
        if _reproducir_original:
            _reproducir_original(busqueda)
        else:
            url = f"https://www.youtube.com/results?search_query={busqueda}"
            webbrowser.open(url)
    except Exception as e:
        print(f"[Automation Error]: Falló método original de video, usando respaldo -> {e}")
        url = f"https://www.youtube.com/results?search_query={busqueda}"
        webbrowser.open(url)


def lanzar_aplicacion_usuario(nombre_app: str):
    """Lanza la aplicación o navegador solicitados por el usuario."""
    nombre = nombre_app.lower().strip()
    try:
        if _lanzar_app_original:
            _lanzar_app_original(nombre_app)
            return
    except Exception as e:
        print(f"[Automation Error]: Falló lanzamiento primario de app -> {e}")

    # RESPALDO DIRECTO DE COMANDOS DE WINDOWS
    if "brave" in nombre or "navegador" in nombre or "chrome" in nombre or "internet" in nombre:
        webbrowser.open("https://www.google.com")
    elif "calculator" in nombre or "calculadora" in nombre:
        subprocess.Popen("calc.exe")
    elif "bloc" in nombre or "notepad" in nombre:
        subprocess.Popen("notepad.exe")
    else:
        # Intenta ejecutar directamente el nombre proporcionado
        try:
            os.system(f"start {nombre_app}")
        except Exception as ex:
            print(f"No se pudo ejecutar {nombre_app}: {ex}")


def lanzar_videojuego(nombre_juego: str):
    """Lanza un videojuego o cliente de juegos."""
    try:
        if _lanzar_juego_original:
            _lanzar_juego_original(nombre_juego)
        else:
            os.system(f"start {nombre_juego}")
    except Exception as e:
        print(f"[Automation Error]: Fallo al lanzar juego -> {e}")
        os.system(f"start {nombre_juego}")


__all__ = [
    "desplegar_monitores_windows",
    "ejecutar_aplicacion_office",
    "reproducir_video_brave",
    "lanzar_aplicacion_usuario",
    "lanzar_videojuego",
]