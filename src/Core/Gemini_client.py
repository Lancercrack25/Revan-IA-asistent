import os
from google import genai
from google.genai import types
from src.Core.Config_loader import cargar_credenciales, cargar_ajustes

class GeminiClient:
    def __init__(self):
        #Cargar credenciales y ajustes
        credenciales = cargar_credenciales()
        ajustes = cargar_ajustes()
        # Soportamos tanto tu cargador como las variables de entorno normales
        api_key = credenciales.get("GEMINI_API_KEY") if credenciales else os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("No se encontró la GEMINI_API_KEY en las credenciales.")

        # Inicializamos el nuevo cliente oficial de Google
        self.client = genai.Client(api_key=api_key)
        self.titulo = ajustes.get("USER_NAME", "Maestro") if ajustes else "Maestro"

        # 3. Personalidad y contexto de REVAN
       # 3. Personalidad y contexto de REVAN
        instruccion_sistema = (
            f"Eres REVAN, un asistente avanzado como Jarvis de las películas de Iron Man, pero con más personalidad. "
            f"Te estás dirigiendo a tu usuario, a quien reconoces y respetas profundamente como tu {self.titulo}. "
            f"Mantén una conversación natural, fluida, inteligente y madura. "
            f"Tus respuestas deben ser concisas (máximo de 2 o 4 oraciones cortas) para que al hablar "
            f"no suenes aburrido ni satures el audio. Sé directo, estratégico y leal.\n"
            f"REGLAS CRÍTICAS:\n"
            f"1. Responde SIEMPRE en español, sin importar si el usuario habla otro idioma o si recibes texto ruidoso.\n"
            f"2. Si te preguntan sobre cualquier tema, responde con total sinceridad y sin rodeos, aportando valor real.\n"
            f"3. NUNCA leas rutas de carpetas o comandos técnicos feos (ej. C:\\Users\\...); simplifícalos a 'su escritorio' o 'su equipo'.\n"
            f"4. ACCIÓN DIRECTA: Tienes acceso total para ejecutar acciones en la PC mediante tus herramientas (tools). "
            f"Cuando el usuario pida abrir, buscar, crear o ejecutar algo, usa la herramienta correspondiente sin dudar "
            f"y NUNCA digas que no tienes acceso al sistema."
        )

        # 4. Configurar el chat con la instrucción de sistema integrada en el SDK moderno
        config = types.GenerateContentConfig(
            system_instruction=instruccion_sistema
        )

        # 5. Iniciamos el chat con memoria usando el modelo nativo rápido
        print("[REVAN]: Memoria e historial de conversación activados (SDK Moderno).")
        self.chat = self.client.chats.create(
            model="gemini-2.5-flash",
            config=config
        )

    def generar_respuesta(self, orden: str) -> str:
        try:
            respuesta = self.chat.send_message(orden)
            return respuesta.text
        except Exception as e:
            return f"Lo siento, {self.titulo}, mis sistemas cognitivos han tenido un percance: {str(e)}"