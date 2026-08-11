"""
rendimiento_general.py — punto de entrada único que combina hardware,
agentes y módulos en un solo snapshot, listo para transmitir por
WebSocket al dashboard.
"""
import time
from src.Productividad.rendimiento_hardware import obtener_rendimiento_hardware
from src.Productividad.rendimiento_agentes import obtener_rendimiento_agentes
from src.Productividad.rendimiento_modulos import obtener_rendimiento_modulos

def obtener_snapshot_completo() -> dict:
    """
    Une las 3 fuentes en un solo dict. Cada sub-función ya maneja sus
    propios errores (devuelve dict vacío o valores en 0 en vez de
    lanzar excepción), así que esta función no necesita try/except
    adicional.
    """
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hardware": obtener_rendimiento_hardware(),
        "agentes": obtener_rendimiento_agentes(),
        "modulos": obtener_rendimiento_modulos(),
    }