#este archivo se hara cargoi de mostrar el rendimiento de los agentes de manera mas detallada y con graficas, para poder ver el rendimiento de cada agente y poder compararlos entre si, ademas de poder ver el rendimiento de cada agente en diferentes momentos del dia, para poder ver si hay algun agente que este teniendo un rendimiento bajo en algun momento del dia y poder tomar medidas al respecto.
"""
rendimiento_agentes.py — estadísticas reales de uso de los agentes
(Coder_agent, Creative_agent, Electronics) a partir del log de auditoría
de seguridad que YA se está escribiendo (src/Security/auditoria.py).

No se instrumenta nada nuevo en los agentes: cada llamada a
registrar_evento(modulo=..., nivel=...) que ya hacen coder_agent.py,
creative_agent.py y conexion_creaciones.py queda en
logs/security_audit.log, y aquí solo se lee y resume ese log.
"""

from collections import defaultdict

from src.Security.auditoria import leer_eventos_recientes
_AGENTES_MONITOREADOS = ["coder_agent", "creative_agent", "electronics", "social_discord"]

_ETIQUETAS_LEGIBLES = {
    "coder_agent": "Coder Agent",
    "creative_agent": "Creative Agent",
    "electronics": "Electronics",
    "social_discord": "Social (Discord)",
}

def obtener_rendimiento_agentes(ventana_eventos: int = 300) -> dict:
    """
    Resume, por agente, cuántos eventos tuvo, cuántos fueron advertencia/
    error, y el timestamp del último evento -sobre los últimos
    'ventana_eventos' registros del log de auditoría (no filtra por
    tiempo, sino por cantidad de líneas recientes, que es más barato de
    leer que parsear todas las fechas)-.
    """
    eventos = leer_eventos_recientes(ventana_eventos)

    resumen = {
        etiqueta: {"eventos": 0, "advertencias": 0, "criticos": 0, "ultimo_evento": None}
        for etiqueta in [_ETIQUETAS_LEGIBLES[m] for m in _AGENTES_MONITOREADOS]
    }

    for ev in eventos:
        modulo = ev.get("modulo", "")
        if modulo not in _AGENTES_MONITOREADOS:
            continue

        etiqueta = _ETIQUETAS_LEGIBLES[modulo]
        nivel = ev.get("nivel", "INFO")

        resumen[etiqueta]["eventos"] += 1
        if nivel == "ADVERTENCIA":
            resumen[etiqueta]["advertencias"] += 1
        elif nivel == "CRITICO":
            resumen[etiqueta]["criticos"] += 1
        resumen[etiqueta]["ultimo_evento"] = ev.get("timestamp")

    return resumen