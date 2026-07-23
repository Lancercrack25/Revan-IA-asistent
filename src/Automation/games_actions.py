import os
import re
import difflib
import unicodedata
import subprocess
from src.Services.os_service import obtener_ruta_escritorio


# Apodos/abreviaciones que NO se parecen lo suficiente al nombre real como
# para que el escaneo tolerante (substring + difflib) los encuentre solo.
# Esto es opcional y pequeño a propósito: solo agrega aquí los casos que
# de verdad lo necesiten (como "dmc"), no cada juego nuevo — esos ya los
# encuentra el escaneo automático de la carpeta sin tocar este archivo.
ALIAS_JUEGOS = {
    "dmc": "devil may cry",
    "7ds": "seven deadly sins",
}


def _normalizar(texto: str) -> str:
    """Minúsculas, sin acentos, sin símbolos raros — para comparar nombres de forma tolerante."""
    texto = (texto or "").lower().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    return texto.strip()


def _listar_accesos(carpeta: str) -> dict:
    """
    Escanea una carpeta y devuelve {nombre_normalizado: ruta_completa} para
    cada acceso directo (.lnk) o ejecutable (.exe) que encuentre. Se llama
    en tiempo real cada vez, así que si agregas un juego/app nuevo a la
    carpeta, REVAN lo reconoce de inmediato sin tocar código.
    """
    accesos = {}
    if not os.path.isdir(carpeta):
        return accesos

    for archivo in os.listdir(carpeta):
        if archivo.lower().endswith((".lnk", ".exe")):
            nombre_sin_ext = os.path.splitext(archivo)[0]
            clave = _normalizar(nombre_sin_ext)
            if clave:
                accesos[clave] = os.path.join(carpeta, archivo)

    return accesos


def _buscar_mejor_coincidencia(nombre_buscado: str, accesos: dict, umbral: float = 0.5):
    """
    Encuentra el acceso directo que mejor coincida con lo pedido:
      1. Substring directo en cualquier dirección (más confiable,
         "minecraft" encuentra "Minecraft for Windows").
      2. Si no hay substring, similitud aproximada con difflib (tolera
         errores de transcripción del reconocimiento de voz, ej.
         "amon as" en vez de "among us").
    """
    nombre_normalizado = _normalizar(nombre_buscado)
    if not nombre_normalizado or not accesos:
        return None

    # 0. ¿Es un apodo conocido? Si sí, buscar con el nombre real en su lugar.
    if nombre_normalizado in ALIAS_JUEGOS:
        nombre_normalizado = _normalizar(ALIAS_JUEGOS[nombre_normalizado])

    for clave, ruta in accesos.items():
        if nombre_normalizado in clave or clave in nombre_normalizado:
            return ruta

    coincidencias = difflib.get_close_matches(nombre_normalizado, accesos.keys(), n=1, cutoff=umbral)
    if coincidencias:
        return accesos[coincidencias[0]]

    return None


def lanzar_videojuego(nombre_juego: str) -> str:
    """
    Escanea Escritorio/Juegos/ en tiempo real y lanza el acceso directo que
    mejor coincida. Ya NO requiere editar código para agregar juegos
    nuevos: basta con poner el .lnk (o .exe) en esa carpeta.
    """
    carpeta_juegos = os.path.join(obtener_ruta_escritorio(), "Juegos")
    accesos = _listar_accesos(carpeta_juegos)

    if not accesos:
        return "Señor, no encontré ningún juego en la carpeta 'Juegos' del escritorio."

    ruta_encontrada = _buscar_mejor_coincidencia(nombre_juego, accesos)

    if not ruta_encontrada:
        disponibles = ", ".join(
            os.path.splitext(os.path.basename(r))[0] for r in list(accesos.values())[:8]
        )
        return f"Señor, no encontré '{nombre_juego}' entre sus juegos. Los que tiene disponibles incluyen: {disponibles}."

    try:
        subprocess.Popen(f'start "" "{ruta_encontrada}"', shell=True)
        nombre_mostrado = os.path.splitext(os.path.basename(ruta_encontrada))[0]
        return f"Desplegando el entorno de combate para {nombre_mostrado}. Prepárese, Señor."
    except Exception as e:
        return f"Fallo crítico al intentar abrir el juego: {str(e)}"