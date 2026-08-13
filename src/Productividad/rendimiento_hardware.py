#este archivo se encargara de mostrar el rendimiento del hardware
"""
rendimiento_hardware.py — snapshot de recursos del sistema (CPU/RAM/disco).
Usa psutil, que ya es dependencia del proyecto (Network/analize_network.py
y otros ya lo usan).
"""
import psutil
def obtener_rendimiento_hardware() -> dict:
    memoria = psutil.virtual_memory()
    disco = psutil.disk_usage("/")

    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "cpu_nucleos": psutil.cpu_count(logical=True),
        "ram_percent": memoria.percent,
        "ram_usado_gb": round(memoria.used / (1024 ** 3), 2),
        "ram_total_gb": round(memoria.total / (1024 ** 3), 2),
        "disco_percent": disco.percent,
    }