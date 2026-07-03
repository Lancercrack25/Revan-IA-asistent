from abc import ABC, abstractmethod

class IVoiceInput(ABC):
    """Contrato para que Revan pueda escuchar órdenes por el micrófono."""
    
    @abstractmethod
    def escuchar(self) -> str:
        """Escucha el micrófono y devuelve el texto procesado. Si no entiende, devuelve una cadena vacía."""
        pass