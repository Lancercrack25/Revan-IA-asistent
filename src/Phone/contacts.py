#este archivo se encarga de leer y buscar contactos de la agenda del telefono via ADB
import re
from src.Phone.phone_conection import _ejecutar_adb, dispositivo_conectado

_cache_contactos = None  # se llena en el primer uso, para no consultar el teléfono cada vez


def _parsear_linea_contacto(linea: str):
    """
    Parsea una línea de salida de 'content query' sobre contactos, con
    formato tipo:
      Row: 0 display_name=Juan Perez, number=5512345678
    Devuelve (nombre, numero) o None si la línea no trae ambos datos.
    """
    match_nombre = re.search(r"display_name=([^,]+)", linea)
    match_numero = re.search(r"number=([^,]+)", linea)

    if not match_nombre or not match_numero:
        return None

    nombre = match_nombre.group(1).strip()
    numero = re.sub(r"[^\d+]", "", match_numero.group(1).strip())  # solo dígitos y '+'

    if not nombre or not numero:
        return None

    return nombre, numero

def obtener_contactos(forzar_actualizacion: bool = False):
    """
    Lee todos los contactos con número telefónico del dispositivo conectado.
    Los cachea en memoria (dura mientras REVAN esté corriendo) para no
    tener que volver a consultar el teléfono en cada búsqueda.
    Devuelve una lista de tuplas (nombre, numero).
    """
    global _cache_contactos

    if _cache_contactos is not None and not forzar_actualizacion:
        return _cache_contactos

    if not dispositivo_conectado():
        return []

    exito, salida = _ejecutar_adb(
        "shell", "content", "query",
        "--uri", "content://com.android.contacts/data/phones",
        "--projection", "display_name:number",
        timeout=15,
    )

    if not exito:
        print(f"[Contactos]: Error al leer la agenda: {salida}")
        return []

    contactos = []
    for linea in salida.splitlines():
        resultado = _parsear_linea_contacto(linea)
        if resultado:
            contactos.append(resultado)
    vistos = set()
    contactos_unicos = []
    for nombre, numero in contactos:
        clave = nombre.lower()
        if clave not in vistos:
            vistos.add(clave)
            contactos_unicos.append((nombre, numero))

    _cache_contactos = contactos_unicos
    return _cache_contactos


def buscar_contacto(nombre_buscado: str):
    """
    Busca un contacto por nombre (coincidencia parcial, sin importar
    mayúsculas/acentos exactos). Devuelve (nombre_real, numero) o None si
    no se encuentra o hay más de una coincidencia ambigua.
    """
    nombre_buscado = nombre_buscado.lower().strip()
    contactos = obtener_contactos()

    coincidencias = [
        (nombre, numero) for nombre, numero in contactos
        if nombre_buscado in nombre.lower()
    ]

    if len(coincidencias) == 1:
        return coincidencias[0]

    return None  # ninguna coincidencia, o ambigua (varias posibles)

def listar_coincidencias(nombre_buscado: str):
    nombre_buscado = nombre_buscado.lower().strip()
    contactos = obtener_contactos()
    return [nombre for nombre, _ in contactos if nombre_buscado in nombre.lower()]

if __name__ == "__main__":
    contactos = obtener_contactos()
    print(f"Contactos encontrados: {len(contactos)}")
    for nombre, numero in contactos[:10]:
        print(f"  {nombre}: {numero}")