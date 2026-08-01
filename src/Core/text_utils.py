"""
Utilidades de limpieza de texto para conversión a voz (TTS).

Antes esta limpieza vivía escondida dentro de NimClient (_limpiar_para_voz)
y SOLO se aplicaba a las respuestas que pasaban por ese cliente. Módulos
como Network (busqueda_intrusos, velocidad_latencia) devuelven texto con
IPs, nombres de archivo con guiones bajos y timestamps que ElevenLabs
pronuncia mal si se le pasan tal cual. Ahora este limpiador se aplica de
forma centralizada, justo antes de mandar CUALQUIER texto a voz_ia.hablar(),
sin importar de qué módulo venga la respuesta.
"""

import re

# Nombres de archivo con extensión típica (reportes, docs, logs, etc.)
_PATRON_ARCHIVO = re.compile(
    r'\b[\w\-]+\.(txt|docx|pdf|csv|json|log|xlsx|png|jpg|jpeg)\b',
    re.IGNORECASE
)

# Rutas de Windows (C:\Users\...) y Unix (/home/user/...)
_PATRON_RUTA_WINDOWS = re.compile(r'[A-Za-z]:\\[^\s,;]+')
_PATRON_RUTA_UNIX = re.compile(r'(?<!\w)/[\w\-./]+')

# Direcciones IPv4 -> se separan en grupos para que el TTS las lea
# número por número en vez de intentar leerlas como un numeral gigante.
_PATRON_IP = re.compile(r'\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b')

# Direcciones MAC (aa:bb:cc:dd:ee:ff) — casi nunca deben leerse en voz alta.
_PATRON_MAC = re.compile(r'\b([0-9a-fA-F]{2}[:\-]){5}[0-9a-fA-F]{2}\b')


def limpiar_texto_para_voz(texto: str) -> str:
    """
    Recibe cualquier texto que REVAN vaya a decir en voz alta y lo deja
    apto para TTS: sin rutas, sin nombres de archivo crudos, sin MACs,
    e IPs formateadas para que se lean grupo por grupo.

    IMPORTANTE: esto NO debe aplicarse al texto que se muestra en el
    dashboard (sincronizar_chat_dashboard), solo al que se le pasa a
    voz_ia.hablar(). El usuario sí quiere ver la IP completa o el nombre
    del archivo en el chat; solo no queremos que la voz los lea crudos.
    """
    if not texto:
        return ""

    # 1. Rutas de archivo completas -> genérico
    texto = _PATRON_RUTA_WINDOWS.sub("su equipo", texto)
    texto = _PATRON_RUTA_UNIX.sub("su equipo", texto)

    # 2. Direcciones MAC -> se resumen, no se leen
    texto = _PATRON_MAC.sub("una dirección física", texto)

    # 3. Nombres de archivo con extensión -> genérico
    texto = _PATRON_ARCHIVO.sub("un archivo de reporte", texto)

    # 4. IPs -> lectura grupo por grupo
    texto = _PATRON_IP.sub(lambda m: " punto ".join(m.groups()), texto)

    # 5. Símbolos que ElevenLabs no maneja bien
    texto = texto.replace("_", " ")
    texto = texto.replace("%", " por ciento")
    texto = texto.replace("#", "")
    texto = re.sub(r'\s{2,}', ' ', texto)

    return texto.strip()