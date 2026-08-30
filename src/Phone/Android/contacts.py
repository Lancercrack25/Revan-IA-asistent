import unicodedata

def _normalizar(texto: str) -> str:
    """Elimina acentos, diacríticos y convierte a minúsculas para comparaciones limpias."""
    if not texto:
        return ""
    texto = texto.lower().strip()
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def buscar_contacto(nombre_buscado: str, lista_contactos: dict) -> list:
    """Busca contactos ignorando tildes, mayúsculas y diacríticos."""
    busqueda_clean = _normalizar(nombre_buscado)
    coincidencias = []

    for nombre_real, datos in lista_contactos.items():
        nombre_clean = _normalizar(nombre_real)
        if busqueda_clean in nombre_clean:
            coincidencias.append((nombre_real, datos))

    return coincidencias