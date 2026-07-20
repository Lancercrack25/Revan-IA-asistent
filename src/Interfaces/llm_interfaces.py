from abc import ABC, abstractmethod

class ILLMClient(ABC):
    """
    Contrato oficial para cualquier Cliente de IA en Jarvis.
    Esto asegura que si usas Gemini o Claude, ambos reaccionen igual.
    """
    
    @abstractmethod
    def enviar_mensaje(self, mensaje: str) -> str:
        """Envía el texto del usuario a la IA y devuelve la respuesta."""
        pass

    @abstractmethod
    def obtener_historial(self) -> list:
        """Devuelve los mensajes guardados en la memoria de la sesión."""
        pass

    @abstractmethod
    def limpiar_memoria(self):
        """Borra el historial de la sesión actual solo cuando el programa se cierre."""
        pass