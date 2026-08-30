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

# URLs completas (http/https) y direcciones IP:puerto sueltas
# (127.0.0.1:8000). Antes no existía este patrón -una URL como
# "http://127.0.0.1:8000/coder" se leía en voz alta casi completa,
# palabra por palabra, con "dos puntos", "barra", etc.-.
_PATRON_URL = re.compile(r'https?://[^\s,;]+', re.IGNORECASE)
_PATRON_IP_PUERTO = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}:\d{1,4}\b')


def limpiar_texto_para_voz(texto: str, permitir_urls: bool = False) -> str:
    if not texto:
        return ""

    if not permitir_urls:
        texto = _PATRON_URL.sub("la dirección correspondiente", texto)
        texto = _PATRON_IP_PUERTO.sub("la dirección correspondiente", texto)

    # 1. Rutas de archivo completas -> genérico
    texto = _PATRON_RUTA_WINDOWS.sub("su equipo", texto)
    texto = _PATRON_RUTA_UNIX.sub("su equipo", texto)
    # 2. Direcciones MAC -> se resumen, no se leen
    texto = _PATRON_MAC.sub("una dirección física", texto)
    # 3. Nombres de archivo con extensión -> genérico
    texto = _PATRON_ARCHIVO.sub("un archivo de reporte", texto)
    texto = _PATRON_IP.sub("una dirección IP", texto)
    # 5. Símbolos que ElevenLabs no maneja bien
    texto = texto.replace("_", " ")
    texto = texto.replace("%", " por ciento")
    texto = texto.replace("#", "")
    texto = re.sub(r'\s{2,}', ' ', texto)

    return texto.strip()