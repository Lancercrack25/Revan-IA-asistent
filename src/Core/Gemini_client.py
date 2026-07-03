import google.generativeai as genai 
from src.Core.Config_loader import cargar_credenciales, cargar_ajustes

class GeminiClient:
    def __init__(self):
        # 1. Cargar credenciales y ajustes
        credenciales = cargar_credenciales()
        ajustes = cargar_ajustes()
        
        if not credenciales or "GEMINI_API_KEY" not in credenciales:
            raise ValueError("❌ No se encontró la GEMINI_API_KEY.")
            
        genai.configure(api_key=credenciales["GEMINI_API_KEY"])
        
        # 2. Obtener y guardar el título del usuario
        self.titulo = ajustes.get("USER_NAME", "Maestro") if ajustes else "Maestro"
        
        # 3. Darle la personalidad y el contexto conversacional
        instruccion_sistema = (
            f"Eres REVAN, un asistente avanzado como Jarvis de las películas de Iron Man, pero con más personalidad. "
            f"Te estás dirigiendo a tu usuario, a quien reconoces y respetas profundamente como tu {self.titulo}. "
            f"Mantén una conversación natural, fluida, inteligente y madura. "
            f"Tus respuestas deben ser concisas (máximo de 2 o 3 oraciones cortas) para que al hablar "
            f"no suenes aburrido ni satures el audio. Sé directo, estratégico y leal."
        )
        
        # 4. Inicializar el modelo con la versión flash más reciente y compatible
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=instruccion_sistema
        )
        
        # 5. Iniciamos el chat con memoria
        print("🧠 [REVAN]: Memoria e historial de conversación activados.")
        self.chat = self.model.start_chat(history=[])

    def generar_respuesta(self, orden: str) -> str:
        """Envía el mensaje al chat con memoria y devuelve la respuesta continua."""
        try:
            # Enviamos el mensaje dentro de la sesión de chat
            respuesta = self.chat.send_message(orden)
            return respuesta.text
        except Exception as e:
            return f"Lo siento, {self.titulo}, mis sistemas cognitivos han tenido un percance: {str(e)}"