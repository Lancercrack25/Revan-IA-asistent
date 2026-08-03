"""
Validación y saneamiento de entradas que, aunque vengan de un LLM (no
directamente tecleadas por el usuario), terminan siendo usadas para
interactuar con el sistema operativo: nombres de aplicación, argumentos de
comandos, nombres de archivo, etc.

Esta es la primera línea de defensa: incluso si en algún módulo se comete
el error de interpolar una de estas cadenas en un comando, esta validación
debería rechazarla antes de que llegue tan lejos. No reemplaza usar
subprocess sin shell=True (eso sigue siendo obligatorio); es una capa
adicional, no la única.
"""

# Caracteres sin motivo legítimo en un nombre de aplicación/archivo, y que
# SÍ tienen significado especial para shells y parsers de línea de comandos
# (cmd.exe, PowerShell, bash): encadenar comandos, redirección, sustitución.
import os

from src.Security.auditoria import registrar_evento, NIVEL_ADVERTENCIA

# Caracteres sin motivo legítimo en un nombre de aplicación/archivo, y que
# SÍ tienen significado especial para shells y parsers de línea de comandos
# (cmd.exe, PowerShell, bash): encadenar comandos, redirección, sustitución.
_CARACTERES_PELIGROSOS = set('&|;`$()<>^\n\r"\'')

_LONGITUD_MAXIMA = 120


class EntradaNoSeguraError(ValueError):
    """
    Se lanza cuando una entrada destinada al sistema operativo contiene
    caracteres potencialmente peligrosos o excede límites razonables.
    """
    pass


def es_entrada_segura(texto: str) -> bool:
    """Chequeo booleano rápido, sin lanzar excepción."""
    if not texto or not isinstance(texto, str):
        return False
    if len(texto) > _LONGITUD_MAXIMA:
        return False
    if any(c in _CARACTERES_PELIGROSOS for c in texto):
        return False
    return True


def sanitizar_o_rechazar(texto: str, contexto: str = "entrada") -> str:
    """
    Devuelve el texto limpio (sin espacios en los extremos) si es seguro, o
    lanza EntradaNoSeguraError si no lo es.

    Úsalo justo antes de pasar cualquier dato de origen LLM/usuario a
    os.startfile, subprocess, rutas de archivo, etc.
    """
    if texto is None:
        raise EntradaNoSeguraError(f"{contexto}: valor vacío.")

    texto = str(texto).strip()

    if not texto:
        raise EntradaNoSeguraError(f"{contexto}: valor vacío tras limpiar espacios.")

    if not es_entrada_segura(texto):
        fragmento = texto[:50]
        # Todo rechazo queda en el log de auditoría: un intento repetido de
        # colar caracteres peligrosos es justo el tipo de patrón que quieres
        # poder revisar después.
        registrar_evento(
            modulo="sanitizador",
            accion=f"rechazo({contexto})",
            resultado=f"Entrada rechazada por caracteres no permitidos o longitud excesiva: '{fragmento}'",
            nivel=NIVEL_ADVERTENCIA,
        )
        raise EntradaNoSeguraError(
            f"{contexto}: '{fragmento}' contiene caracteres no permitidos "
            f"o excede el largo máximo de {_LONGITUD_MAXIMA} caracteres."
        )

    return texto


def es_ruta_segura(ruta_absoluta: str) -> bool:
    """
    Solo considera segura una ruta absoluta que quede DENTRO del directorio
    del usuario (~). Se resuelve la ruta real (sin '..' ni symlinks
    engañosos) antes de comparar.

    Esta función es compartida por cualquier módulo que escriba archivos a
    partir de una ruta que decide el LLM (crear_carpeta_sistema en
    os_service.py, crear_y_abrir_documento_word / crear_y_abrir_hoja_excel
    en System_commands.py) -antes cada uno tenía o no tenía esta
    validación por separado; ahora es una sola fuente de verdad.
    """
    try:
        home = os.path.realpath(os.path.expanduser("~"))
        destino = os.path.realpath(ruta_absoluta)
        return os.path.commonpath([destino, home]) == home
    except Exception:
        return False