#este archivo apoyara mucho a este modulo
import os
import json
import time
import threading

_LOCK = threading.Lock()

_DIR_LOGS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
_RUTA_LOG = os.path.join(_DIR_LOGS, "security_audit.log")

NIVEL_INFO = "INFO"
NIVEL_ADVERTENCIA = "ADVERTENCIA"
NIVEL_CRITICO = "CRITICO"

def _asegurar_directorio():
    try:
        os.makedirs(_DIR_LOGS, exist_ok=True)
    except Exception as e:
        print(f"[Auditoría]: No se pudo crear el directorio de logs: {e}")

def registrar_evento(modulo: str, accion: str, resultado: str,
                      nivel: str = NIVEL_INFO, detalles: dict = None) -> None:
    evento = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "nivel": nivel,
        "modulo": modulo,
        "accion": accion,
        "resultado": resultado,
        "detalles": detalles or {},
    }

    try:
        _asegurar_directorio()
        linea = json.dumps(evento, ensure_ascii=False)
        with _LOCK:
            with open(_RUTA_LOG, "a", encoding="utf-8") as f:
                f.write(linea + "\n")
    except Exception as e:
        print(f"[Auditoría]: No se pudo escribir el evento de seguridad: {e}")

    # Los eventos críticos también se imprimen en consola en tiempo real,
    # para que sean visibles de inmediato y no solo al revisar el log después.
    if nivel == NIVEL_CRITICO:
        print(f"[Auditoría CRÍTICA] {modulo} -> {accion}: {resultado}")


def leer_eventos_recientes(cantidad: int = 50) -> list:
    """Devuelve los últimos 'cantidad' eventos registrados (los más recientes al final)."""
    if not os.path.exists(_RUTA_LOG):
        return []

    try:
        with _LOCK:
            with open(_RUTA_LOG, "r", encoding="utf-8") as f:
                lineas = f.readlines()
    except Exception as e:
        print(f"[Auditoría]: No se pudo leer el log de seguridad: {e}")
        return []

    eventos = []
    for linea in lineas[-cantidad:]:
        try:
            eventos.append(json.loads(linea))
        except json.JSONDecodeError:
            continue
    return eventos