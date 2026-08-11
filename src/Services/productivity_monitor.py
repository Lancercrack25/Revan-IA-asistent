import psutil
import time
from typing import Dict, Any

# Memoria local para cálculo de estadísticas rápidas
HISTORIAL_RENDIMIENTO = {
    "hardware": {"cpu": [], "ram": [], "gpu": []},
    "agentes": {"coder": 0, "creative": 0, "orchestrator": 0},
    "modulos": {} # Ej: {"whatsapp": {"llamadas": 10, "tiempo_avg": 0.4}}
}

def obtener_telemetria_hardware() -> Dict[str, Any]:
    """Captura el estado de CPU, RAM y latencia general."""
    cpu_percent = psutil.cpu_percent(interval=None)
    ram_percent = psutil.virtual_memory().percent
    
    return {
        "cpu_usage": cpu_percent,
        "ram_usage": ram_percent,
        "timestamp": time.strftime("%H:%M:%S")
    }

def obtener_rendimiento_agentes() -> Dict[str, Any]:
    """Retorna las estadísticas acumuladas del desempeño de los agentes."""
    # Aquí puedes conectar las llamadas reales de tus agentes
    return {
        "coder_agent_tasks": HISTORIAL_RENDIMIENTO["agentes"]["coder"],
        "creative_agent_tasks": HISTORIAL_RENDIMIENTO["agentes"]["creative"],
        "orchestrator_tasks": HISTORIAL_RENDIMIENTO["agentes"]["orchestrator"],
    }