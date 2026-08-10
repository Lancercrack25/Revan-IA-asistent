"""
Rate limiting para acciones sensibles.

Si el LLM entra en un ciclo raro (alucina y decide llamar la misma tool
repetidamente, o algo externo -como un correo manipulado- lo empuja a
intentar varias acciones seguidas), esto pone un techo duro por categoría
y por ventana de tiempo.

Deliberadamente simple: sin backoff exponencial ni nada elaborado. Un
límite fijo es más fácil de razonar, depurar, y ajustar que un algoritmo
sofisticado, y para este caso de uso (evitar loops descontrolados, no
proteger una API pública de miles de usuarios) es más que suficiente.
"""

import time
import threading
from collections import defaultdict

from src.Security.auditoria import registrar_evento, NIVEL_ADVERTENCIA

_lock = threading.Lock()
_registro_llamadas = defaultdict(list)  # categoria -> lista de timestamps

# (límite de acciones, ventana en segundos) por categoría.
LIMITES_POR_DEFECTO = {
    "whatsapp": (5, 60),
    "correo": (5, 60),
    "camara": (10, 60),
    "carpeta": (10, 60),
    "documentos": (8, 60),
    "coder_agent": (5, 60),
    "creative_agent": (5, 60),
    "electronics": (10, 60),
    "limpieza_sistema": (3, 60),
    "comando_sistema": (10, 60),
    "default": (10, 60),
}


def permitir_accion(categoria: str) -> bool:
    """
    Devuelve True si la acción puede proceder, False si ya se alcanzó el
    límite para esa categoría en la ventana de tiempo configurada. Cada
    rechazo queda registrado en auditoría, para poder revisar después si
    hubo un patrón de uso anormal.
    """
    limite, ventana = LIMITES_POR_DEFECTO.get(categoria, LIMITES_POR_DEFECTO["default"])
    ahora = time.time()

    with _lock:
        llamadas = _registro_llamadas[categoria]
        llamadas[:] = [t for t in llamadas if ahora - t < ventana]

        if len(llamadas) >= limite:
            registrar_evento(
                modulo="rate_limiter",
                accion=f"limite_excedido({categoria})",
                resultado=f"Se alcanzó el límite de {limite} acciones en {ventana}s para '{categoria}'.",
                nivel=NIVEL_ADVERTENCIA,
            )
            return False

        llamadas.append(ahora)
        return True


def resetear(categoria: str = None) -> None:
    """Utilidad de depuración/pruebas: limpia el registro de una categoría o de todas."""
    with _lock:
        if categoria:
            _registro_llamadas.pop(categoria, None)
        else:
            _registro_llamadas.clear()