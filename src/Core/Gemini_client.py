from google import genai
from google.genai import types
from src.Interfaces.llm_interfaces import ILLMClient
from src.Core.Config_loader import cargar_credenciales

class GeminiClient(ILLMClient):
    def __init__(self):
        # 1. Cargar llaves del JSON
        credenciales = cargar_credenciales()
        if not credenciales or "GEMINI_API_KEY" not in credenciales:
            raise ValueError("❌ No se encontró la GEMINI_API_KEY en credentials.json")
        
        # 2. Inicializar cliente de Google
        self.client = genai.Client(api_key=credenciales["GEMINI_API_KEY"])
        self.model_name = "gemini-2.5-flash"  # El modelo más rápido y recomendado
        
        # 3. Configurar las instrucciones del sistema (La personalidad de Revan)
        config = types.GenerateContentConfig(
            system_instruction="Eres Revan, un asistente de IA sofisticado, educado e ingenioso. "
                               "Respondes de manera concisa y te diriges al usuario como 'Señor'."
        )
        
        # 4. CREAR LA MEMORIA: Iniciamos un chat continuo que guardará el historial solo
        self.chat = self.client.chats.create(model=self.model_name, config=config)
        print("🤖 Cerebro de Revan inicializado con memoria de corto plazo.")

    def enviar_mensaje(self, mensaje: str) -> str:
        """Envía el mensaje al chat para que recuerde el contexto anterior."""
        try:
            response = self.chat.send_message(mensaje)
            return response.text
        except Exception as e:
            return f"❌ Error en el cerebro de Gemini: {str(e)}"

    def obtener_historial(self) -> list:
        """Devuelve los mensajes acumulados en esta sesión."""
        return self.chat.get_history()

    def limpiar_memoria(self):
        """Reinicia el chat para borrar la memoria de corto plazo."""
        self.chat = self.client.chats.create(model=self.model_name)
        print("🧠 Memoria de corto plazo reiniciada.")