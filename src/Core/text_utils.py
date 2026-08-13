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
_PATRON_ARCHIVO = re.compile(
    r'\b[\w\-]+\.(txt|docx|pdf|csv|json|log|xlsx|png|jpg|jpeg)\b',
    re.IGNORECASE
)

_PATRON_RUTA_WINDOWS = re.compile(r'[A-Za-z]:\\[^\s,;]+')
_PATRON_RUTA_UNIX = re.compile(r'(?<!\w)/[\w\-./]+')
_PATRON_IP = re.compile(r'\b(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})\b')
_PATRON_MAC = re.compile(r'\b([0-9a-fA-F]{2}[:\-]){5}[0-9a-fA-F]{2}\b')


def limpiar_texto_para_voz(texto: str) -> str:
    if not texto:
        return ""
    texto = _PATRON_RUTA_WINDOWS.sub("su equipo", texto)
    texto = _PATRON_RUTA_UNIX.sub("su equipo", texto)
    texto = _PATRON_MAC.sub("una dirección física", texto)
    texto = _PATRON_ARCHIVO.sub("un archivo de reporte", texto)
    texto = _PATRON_IP.sub("una dirección IP", texto)
    texto = texto.replace("_", " ")
    texto = texto.replace("%", " por ciento")
    texto = texto.replace("#", "")
    texto = re.sub(r'\s{2,}', ' ', texto)
    return texto.strip()