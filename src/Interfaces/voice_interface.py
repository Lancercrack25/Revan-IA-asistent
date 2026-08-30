from abc import ABC, abstractmethod

class IVoiceOutput(ABC):
    @abstractmethod
    def hablar(self, texto: str):
        pass