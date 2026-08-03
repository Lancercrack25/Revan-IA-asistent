"""
Gestor genérico de 'acciones pendientes de confirmación', con expiración
(TTL).

Este patrón ya existía duplicado de forma ad-hoc en
src/Phone/whatsapp_service.py (variable global ACCION_PENDIENTE). Se
extrajo aquí para que CUALQUIER módulo que vaya a ejecutar una acción
potencialmente irreversible -el futuro Coder_agent ejecutando código
generado por IA, borrar archivos, enviar mensajes, etc.- pueda exigir
confirmación explícita del usuario sin reimplementar la misma lógica de
TTL y de coincidencia de frases cada vez (y sin repetir el bug que tuvo
whatsapp_service.py: interpretar "si"/"no" como substring en cualquier
parte de una frase no relacionada).

Uso típico:

    gestor = GestorConfirmacion(ttl_segundos=60)

    def _ejecutar():
        return hacer_la_accion_real()

    texto_para_hablar = gestor.solicitar(
        descripcion="Voy a ejecutar 'borrar_temporales.py' en su equipo.",
        callback_confirmar=_ejecutar,
    )
    # ... más tarde, con la siguiente orden del usuario:
    respuesta = gestor.procesar_respuesta(orden_usuario)
    if respuesta:
        # el usuario confirmó o canceló, 'respuesta' ya trae el resultado
        ...
"""

import time
from typing import Callable, Optional

from src.Security.auditoria import registrar_evento, NIVEL_INFO, NIVEL_ADVERTENCIA


# Frases cortas reconocidas como confirmación/cancelación explícita. Se
# comparan por IGUALDAD EXACTA (tras limpiar la frase), nunca por substring
# -así una orden larga no relacionada que contenga "si" o "no" en medio de
# otra palabra o frase nunca dispara una acción por accidente.
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
        registrar_evento(
            modulo="confirmacion",
            accion="solicitar",
            resultado=f"Acción pendiente registrada: {descripcion}",
            nivel=NIVEL_INFO,
        )
        return (
            f"Señor, esto es lo que voy a hacer:\n» {descripcion}\n\n"
            f"¿Confirmo? Responda 'confirma' o 'cancela'."
        )

    def hay_pendiente(self) -> bool:
        if self._pendiente is None:
            return False
        if (time.time() - self._pendiente["timestamp"]) > self.ttl_segundos:
            registrar_evento(
                modulo="confirmacion",
                accion="expirar",
                resultado=f"Acción pendiente expiró sin confirmación: {self._pendiente['descripcion']}",
                nivel=NIVEL_ADVERTENCIA,
            )
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
            registrar_evento(
                modulo="confirmacion",
                accion="confirmar",
                resultado=f"Usuario confirmó: {accion['descripcion']}",
                nivel=NIVEL_INFO,
            )
            return accion["confirmar"]()

        if respuesta in FRASES_CANCELAR:
            accion = self._pendiente
            self._pendiente = None
            registrar_evento(
                modulo="confirmacion",
                accion="cancelar",
                resultado=f"Usuario canceló: {accion['descripcion']}",
                nivel=NIVEL_INFO,
            )
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