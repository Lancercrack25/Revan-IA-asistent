import os
from openai import OpenAI
from src.Core.Config_loader import cargar_credenciales, cargar_ajustes

class GeminiClient:
    """
    Cliente 'Disfrazado': Mantiene la interfaz de GeminiClient pero consulta
    a Llama 3.1 8B Instruct en NVIDIA NIM para evitar errores de cuotas de Google.
    """
    def __init__(self):
        credenciales = cargar_credenciales() or {}
        ajustes = cargar_ajustes() or {}
        api_key = (
            credenciales.get("GEMINI_API_KEY")
        )

        if not api_key:
            raise ValueError("No se encontró la API Key de NVIDIA en las credenciales.")

        # Conexión directa a los servidores de NVIDIA NIM mediante el cliente de OpenAI
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        
        self.titulo = ajustes.get("USER_NAME", "Maestro") if ajustes else "Maestro"

        self.system_prompt = (
            f"Eres REVAN, un asistente avanzado como Jarvis de Iron Man. "
            f"Te estás dirigiendo a tu usuario como {self.titulo}. "
            f"Mantén una conversación natural, inteligente y fluida. "
            f"Tus respuestas deben ser concisas (máximo 2 a 3 oraciones). "
            f"Responde siempre en español aunque si detectas otro idioma responde en ese"
        )

        self.historial = [
            {"role": "system", "content": self.system_prompt}
        ]

    def generar_respuesta(self, orden: str) -> str:
        try:
            self.historial.append({"role": "user", "content": orden})

            # Llamada al modelo Llama 3.1 8B Instruct de Meta en NVIDIA NIM
            response = self.client.chat.completions.create(
                model="meta/llama-3.1-8b-instruct",
                messages=self.historial,
                temperature=0.6,
                max_tokens=150
            )

            respuesta_texto = response.choices[0].message.content.strip()

            self.historial.append({"role": "assistant", "content": respuesta_texto})

            # Mantenemos la memoria corta para respuestas ultrarrápidas
            if len(self.historial) > 10:
                self.historial = [self.historial[0]] + self.historial[-8:]

            return respuesta_texto

        except Exception as e:
            print(f"[GeminiClient -> NVIDIA Respaldo Error]: {e}")
            return f"Lo siento, {self.titulo}, mis sistemas de lenguaje han tenido un percance."