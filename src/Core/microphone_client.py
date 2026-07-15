import speech_recognition as sr
from src.Interfaces.input_interface import IVoiceInput

class MicrophoneClient(IVoiceInput):
    def __init__(self):
        self.reconocedor = sr.Recognizer()
        self.reconocedor.dynamic_energy_threshold = True
        self.reconocedor.pause_threshold = 1.3 
        # Segundos mínimos de silencio que deben ocurrir tras una frase para validarla
        self.reconocedor.non_speaking_duration = 0.6 
        
        self.calibrado = False  # Bandera para calibrar solo una vez

    def escuchar(self, modo_pasivo=False) -> str:
        """Abre el micrófono, escucha una frase y la convierte a texto."""
        with sr.Microphone() as fuente:
            # Calibramos el ruido ambiental ÚNICAMENTE la primera vez que se enciende el mic
            if not self.calibrado:
                print("\n[REVAN]: Calibrando espectro acústico inicial (0.5s)...")
                # Bajamos ligeramente el tiempo de ajuste para evitar falsos positivos
                self.reconocedor.adjust_for_ambient_noise(fuente, duration=0.6)
                self.calibrado = True

            # Si está esperando el aplauso, configuramos tiempos ultra cortos
            tiempo_espera = 1 if modo_pasivo else 7
            limite_frase = 2 if modo_pasivo else 11

            if not modo_pasivo:
                print("\n[REVAN]: Escuchando...")
            
            try:
                audio = self.reconocedor.listen(fuente, timeout=tiempo_espera, phrase_time_limit=limite_frase)
                
                if not modo_pasivo:
                    print("[REVAN]: Procesando lo escuchado...")
                
                texto = self.reconocedor.recognize_google(audio, language="es-ES")
                
                if not modo_pasivo:
                    print(f"[Tú]: {texto}")
                return texto
                
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                if modo_pasivo:
                    return "aplauso"
                return ""
            except sr.RequestError as e:
                print(f"Error de conexión con el servicio de voz: {e}")
                return ""