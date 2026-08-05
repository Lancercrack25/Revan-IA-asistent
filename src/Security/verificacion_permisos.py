
from __future__ import annotations
import os
import stat
from pathlib import Path
from src.Security.auditoria import NIVEL_ADVERTENCIA, NIVEL_INFO, registrar_evento

__all__ = ["verificar_archivos_sensibles"]

ARCHIVOS_SENSIBLES: tuple[str, ...] = (
    "config/credentials.json",
    "src/Database/.env",
    "src/Phone/.env",
)


def _permisos_demasiado_abiertos(ruta: Path) -> bool:
    """
    En sistemas tipo Unix, revisa si el archivo es legible/escribible por
    'otros' (no el dueño). En Windows esta comprobación no aplica de la
    misma forma -el permiso de archivo ahí se maneja por ACL, no por modo
    octal-, así que en Windows esta función siempre devuelve False y la
    verificación real que importa es la de 'vacío o no existe', abajo.
    """
    if os.name == "nt":
        return False
    try:
        modo = ruta.stat().st_mode
    except OSError:
        return False

    return bool(modo & stat.S_IROTH or modo & stat.S_IWOTH)


def _registrar_aviso(accion: str, mensaje: str) -> None:
    registrar_evento(
        modulo="verificacion_permisos",
        accion=accion,
        resultado=mensaje,
        nivel=NIVEL_ADVERTENCIA,
    )


def verificar_archivos_sensibles(directorio_base: str = ".") -> list[str]:
    """
    Revisa cada archivo sensible conocido y devuelve la lista de avisos
    encontrados. No lanza excepciones ni detiene nada -es informativo-.
    """
    base = Path(directorio_base)
    avisos: list[str] = []

    for ruta_relativa in ARCHIVOS_SENSIBLES:
        ruta = base / ruta_relativa

        if not ruta.exists():
            continue

        if ruta.stat().st_size == 0:
            aviso = (
                f"'{ruta_relativa}' existe pero está VACÍO (0 bytes) — cualquier código "
                f"que dependa de él va a fallar en silencio o caer a un valor por defecto."
            )
            avisos.append(aviso)
            _registrar_aviso(f"archivo_vacio({ruta_relativa})", aviso)
            continue

        if _permisos_demasiado_abiertos(ruta):
            aviso = (
                f"'{ruta_relativa}' tiene permisos demasiado abiertos "
                f"(legible/escribible por otros usuarios del sistema)."
            )
            avisos.append(aviso)
            _registrar_aviso(f"permisos_abiertos({ruta_relativa})", aviso)

    if not avisos:
        registrar_evento(
            modulo="verificacion_permisos",
            accion="chequeo_arranque",
            resultado="Todos los archivos sensibles presentes están OK.",
            nivel=NIVEL_INFO,
        )

    return avisos