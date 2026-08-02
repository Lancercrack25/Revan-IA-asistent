import time
from typing import Callable, Optional

FRASES_CONFIRMAR = {
    "confirma", "confirmar", "confirmalo", "confírmalo", "procede", "adelante",
    "si", "sí", "si porfavor", "sí por favor", "ejecuta", "ejecutalo",
    "hazlo", "dale",
}
FRASES_CANCELAR = {
    "cancela", "cancelar", "cancelalo", "cancélalo", "no", "no gracias",
    "abortar", "abortalo", "detente", "mejor no",
}

_MAX_PALABRAS_RESPUESTA_CORTA = 4

class GestorConfirmacion:
    def __init__(self, ttl_segundos: int = 60):
        self.ttl_segundos = ttl_segundos
        self._pendiente: Optional[dict] = None

    def solicitar(
        self,
        descripcion: str,
        callback_confirmar: Callable[[], str],
        callback_cancelar: Optional[Callable[[], str]] = None,
    ) -> str:
        """
        Registra una acción pendiente y devuelve el texto que REVAN debe
        decir para pedir la confirmación. 'callback_confirmar' solo se
        ejecuta si el usuario confirma dentro del TTL.
        """
        self._pendiente = {
            "descripcion": descripcion,
            "confirmar": callback_confirmar,
            "cancelar": callback_cancelar,
            "timestamp": time.time(),
        }
        return (
            f"Señor, esto es lo que voy a hacer:\n» {descripcion}\n\n"
            f"¿Confirmo? Responda 'confirma' o 'cancela'."
        )

    def hay_pendiente(self) -> bool:
        if self._pendiente is None:
            return False
        if (time.time() - self._pendiente["timestamp"]) > self.ttl_segundos:
            self._pendiente = None
            return False
        return True

    def descripcion_pendiente(self) -> Optional[str]:
        return self._pendiente["descripcion"] if self.hay_pendiente() else None

    def procesar_respuesta(self, texto_respuesta: str) -> Optional[str]:
        """
        Devuelve el resultado de confirmar/cancelar si 'texto_respuesta' es
        una respuesta corta y exacta a una de las frases reconocidas.
        Devuelve None si no hay nada pendiente, si expiró, o si la respuesta
        es en realidad una orden distinta no relacionada con la
        confirmación (en cuyo caso NO se toca la acción pendiente, sigue
        esperando).
        """
        if not self.hay_pendiente():
            return None

        respuesta = (texto_respuesta or "").lower().strip().rstrip(".!¡¿?")

        # Respuestas largas = el usuario está pidiendo otra cosa, no
        # confirmando ni cancelando. No interceptamos.
        if len(respuesta.split()) > _MAX_PALABRAS_RESPUESTA_CORTA:
            return None

        if respuesta in FRASES_CONFIRMAR:
            accion = self._pendiente
            self._pendiente = None
            return accion["confirmar"]()

        if respuesta in FRASES_CANCELAR:
            accion = self._pendiente
            self._pendiente = None
            if accion["cancelar"]:
                return accion["cancelar"]()
            return "Acción cancelada, Señor."

        return None

    def cancelar_manual(self) -> str:
        if not self.hay_pendiente():
            return "No hay ninguna acción pendiente que cancelar, Señor."
        accion = self._pendiente
        self._pendiente = None
        if accion["cancelar"]:
            return accion["cancelar"]()
        return "Acción cancelada, Señor."