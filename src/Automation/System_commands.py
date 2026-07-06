# Importaciones relativas limpias desde la misma carpeta Automation
from src.Automation.system_actions import desplegar_monitores_windows, ejecutar_limpieza_sistema
from src.Automation.file_actions import crear_carpeta_tactica
from src.Automation.office_actions import ejecutar_aplicacion_office
from src.Automation.browser_actions import reproducir_video_brave
from src.Automation.apps_actions import lanzar_aplicacion_usuario
from src.Automation.games_actions import lanzar_videojuego

# Tabla limpia de mapeo masivo para el núcleo cognitivo de Ollama
__all__ = [
    "desplegar_monitores_windows",
    "ejecutar_limpieza_sistema",
    "crear_carpeta_tactica",
    "ejecutar_aplicacion_office",
    "reproducir_video_brave",
    "lanzar_aplicacion_usuario",
    "lanzar_videojuego"
]