# 🔄 Importaciones relativas reales (punto de anclaje en la misma carpeta Automation)
from .system_actions import desplegar_monitores_windows
from .file_actions import crear_carpeta_tactica, abrir_carpeta_sistema  # 🎯 Integrada la función faltante
from .office_actions import ejecutar_aplicacion_office
from .browser_actions import reproducir_video_brave
from .apps_actions import lanzar_aplicacion_usuario
from .games_actions import lanzar_videojuego

# 🗂️ Tabla limpia de mapeo masivo para el núcleo cognitivo de Ollama
__all__ = [
    "desplegar_monitores_windows",
    "crear_carpeta_tactica",
    "abrir_carpeta_sistema",  # 🎯 Expuesta correctamente para OllamaClient
    "ejecutar_aplicacion_office",
    "reproducir_video_brave",
    "lanzar_aplicacion_usuario",
    "lanzar_videojuego"
]