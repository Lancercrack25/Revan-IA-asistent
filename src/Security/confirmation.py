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
            self._pendiente = None
            return False
        return True

    def descripcion_pendiente(self) -> Optional[str]:
        return self._pendiente["descripcion"] if self.hay_pendiente() else None

    def procesar_respuesta(self, texto_respuesta: str) -> Optional[str]:
        if not self.hay_pendiente():
            return None

        respuesta = (texto_respuesta or "").lower().strip().rstrip(".!¡¿?")

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