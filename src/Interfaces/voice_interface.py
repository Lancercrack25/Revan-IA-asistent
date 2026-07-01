from abc import ABC, abstractmethod

class IVoiceOutput(ABC):
    """
    Contrato oficial para el sistema de voz de Revan.
    Si en el futuro cambias ElevenLabs por otra voz local, usará las mismas funciones.
    """
    
    @abstractmethod
    def hablar(self, texto: str):
        """Convierte texto a voz y lo reproduce inmediatamente."""
        pass