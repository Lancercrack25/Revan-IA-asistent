import os
import subprocess
from src.Services.os_service import obtener_ruta_escritorio
from src.Automation.games_actions import _normalizar, _listar_accesos, _buscar_mejor_coincidencia


# Protocolos o comandos nativos directos de Windows (UWP / URIs)
# No poner nombres de accesos directos (.lnk) aquí; esos los escanea la carpeta Plataformas.
APPS_PROTOCOLO_ESPECIAL = {
    "discord": "start discord:",
    "whatsapp": "start whatsapp:",
    "anydesk": "start anydesk",
    "unity": "start unity hub",
    "steam": "start steam",
    "xbox": "start xbox",
    "curse": "start curseforge"
}

def lanzar_aplicacion_usuario(nombre_app) -> str:
    """
    Escanea Escritorio/Plataformas/ en tiempo real y lanza la aplicación.
    Admite cadenas de texto normales o diccionarios JSON provenientes del LLM.
    """
    # 1. Desempaquetar si la IA envía un dict/JSON
    if isinstance(nombre_app, dict):
        nombre_real = str(nombre_app.get("nombre", nombre_app.get("app", nombre_app.get("aplicacion", ""))))
    else:
        nombre_real = str(nombre_app)

    app_normalizada = _normalizar(nombre_real)

    if not app_normalizada:
        return "Señor, no reconozco qué aplicación desea ejecutar."

    # 2. Primero buscar en la carpeta Escritorio/Plataformas/
    carpeta_plataformas = os.path.join(obtener_ruta_escritorio(), "Plataformas")
    accesos = _listar_accesos(carpeta_plataformas)
    ruta_encontrada = _buscar_mejor_coincidencia(nombre_real, accesos) if accesos else None

    if ruta_encontrada:
        try:
            os.startfile(ruta_encontrada)
            nombre_mostrado = os.path.splitext(os.path.basename(ruta_encontrada))[0]
            return f"Inicializando la plataforma {nombre_mostrado} desde su cuadrante, Señor."
        except Exception as e:
            return f"No se pudo inicializar {nombre_real}: {str(e)}"

    # 3. Si no está en la carpeta, probar protocolos nativos especiales
    for clave, comando in APPS_PROTOCOLO_ESPECIAL.items():
        if clave in app_normalizada:
            try:
                subprocess.Popen(comando, shell=True)
                return f"Desplegando {nombre_real}, Señor."
            except Exception as e:
                return f"No se pudo abrir {nombre_real}: {str(e)}"

    # 4. Intento genérico de emergencia mediante comando 'start' de Windows
    try:
        os.system(f'start "" "{app_normalizada}"')
        return f"Intentando forzar la ejecución externa de {nombre_real}, Señor."
    except Exception as e:
        return f"No se pudo inicializar la aplicación debido a un error: {str(e)}"