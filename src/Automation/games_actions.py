import os
import re
import difflib
import unicodedata
import subprocess
import webbrowser
from src.Services.os_service import obtener_ruta_escritorio


# ALIAS EN MINÚSCULAS:
# Cuando digas "minecraft", REVAN sabrá que en tu carpeta se llama "minecraft for windows"
ALIAS_JUEGOS = {
    "dmc": "devil may cry",
    "7ds": "seven deadly sins",
    "minecraft": "minecraft for windows",
}


def _normalizar(texto: str) -> str:
    """Minúsculas, sin acentos, sin símbolos raros — para comparar nombres de forma tolerante."""
    texto = (texto or "").lower().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    return texto.strip()


def _listar_accesos(carpeta: str) -> dict:
    """Escanea la carpeta de Juegos y devuelve {nombre_normalizado: ruta_completa}."""
    accesos = {}
    if not os.path.isdir(carpeta):
        return accesos

    for archivo in os.listdir(carpeta):
        if archivo.lower().endswith((".lnk", ".exe", ".url")):
            nombre_sin_ext = os.path.splitext(archivo)[0]
            clave = _normalizar(nombre_sin_ext)
            if clave:
                accesos[clave] = os.path.join(carpeta, archivo)

    return accesos


def _buscar_mejor_coincidencia(nombre_buscado: str, accesos: dict, umbral: float = 0.5):
    """Encuentra el acceso directo por substring, alias o similitud aproximada."""
    nombre_normalizado = _normalizar(nombre_buscado)
    if not nombre_normalizado or not accesos:
        return None

    # Si la palabra dicha está en los Alias, la reemplazamos por el nombre real en tu PC
    if nombre_normalizado in ALIAS_JUEGOS:
        nombre_normalizado = _normalizar(ALIAS_JUEGOS[nombre_normalizado])

    for clave, ruta in accesos.items():
        if nombre_normalizado in clave or clave in nombre_normalizado:
            return ruta

    coincidencias = difflib.get_close_matches(nombre_normalizado, accesos.keys(), n=1, cutoff=umbral)
    if coincidencias:
        return accesos[coincidencias[0]]

    return None


def lanzar_videojuego(nombre_juego) -> str:
    """
    Escanea Escritorio/Juegos/ en tiempo real y lanza el acceso directo.
    Soporta cadenas simples o diccionarios JSON enviados por la IA.
    """
    try:
        # 1. Extraer el texto si la IA envió un objeto JSON/dict
        if isinstance(nombre_juego, dict):
            nombre_real = str(nombre_juego.get("nombre", nombre_juego.get("juego", nombre_juego.get("nombre_juego", ""))))
        else:
            nombre_real = str(nombre_juego)

        nombre_norm = _normalizar(nombre_real)

        if not nombre_norm:
            return "Señor, no reconozco el nombre del juego solicitado."

        # 2. Escaneo en la carpeta Escritorio/Juegos/
        carpeta_juegos = os.path.join(obtener_ruta_escritorio(), "Juegos")
        accesos = _listar_accesos(carpeta_juegos)
        ruta_encontrada = _buscar_mejor_coincidencia(nombre_real, accesos) if accesos else None

        # 3. Si se encuentra el acceso directo en la carpeta "Juegos", abrirlo directamente
        if ruta_encontrada:
            os.startfile(ruta_encontrada)
            nombre_mostrado = os.path.splitext(os.path.basename(ruta_encontrada))[0]
            return f"Desplegando el entorno de combate para {nombre_mostrado}. Prepárese, Señor."

        # 4. Respaldo de emergencia solo si no existiera el archivo en la carpeta Juegos
        if "minecraft" in nombre_norm:
            webbrowser.open("minecraft:")
            return "Desplegando el entorno de combate para Minecraft. Prepárese, Señor."

        # 5. Si no se encuentra el juego
        if accesos:
            disponibles = ", ".join(
                os.path.splitext(os.path.basename(r))[0] for r in list(accesos.values())[:8]
            )
            return f"Señor, no encontré '{nombre_real}' en la carpeta 'Juegos'. Los disponibles son: {disponibles}."

        return f"Señor, no encontré la carpeta 'Juegos' en el escritorio ni el juego '{nombre_real}'."

    except Exception as e:
        return f"Fallo crítico al intentar abrir el juego: {str(e)}"