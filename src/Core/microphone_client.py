import speech_recognition as sr
from src.Interfaces.input_interface import IVoiceInput

class MicrophoneClient(IVoiceInput):
    def __init__(self):
        self.reconocedor = sr.Recognizer()
        # Ajustamos umbrales para mejorar el reconocimiento en español
        self.reconocedor.dynamic_energy_threshold = True

    def escuchar(self) -> str:
        """Abre el micrófono, escucha una frase y la convierte a texto."""
        with sr.Microphone() as fuente:
            print("\n🔵 [REVAN]: Escuchando...")
            # Reduce el ruido ambiental por 1 segundo antes de escuchar
            self.reconocedor.adjust_for_ambient_noise(fuente, duration=1)
            
            try:
                # Escucha el audio (limita a 7 segundos de silencio máximo para no quedarse trabado)
                audio = self.reconocedor.listen(fuente, timeout=7, phrase_time_limit=10)
                print("🧠 [REVAN]: Procesando lo escuchado...")
                
                # Traduce usando el motor gratuito de Google en Español
                texto = self.reconocedor.recognize_google(audio, language="es-ES")
                print(f"🗣️ [Tú]: {texto}")
                return texto
                
            except sr.WaitTimeoutError:
                # Si pasaron los segundos y no dijiste nada
                return ""
            except sr.UnknownValueError:
                # Si el micrófono captó ruido pero no entendió palabras
                print("🔕 [REVAN]: No logré entender la orden.")
                return ""
            except sr.RequestError as e:
                print(f"❌ Error de conexión con el servicio de voz: {e}")
                return ""