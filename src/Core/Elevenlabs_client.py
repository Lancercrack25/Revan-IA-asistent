import os
import re
import requests
import pygame

class ElevenLabsClient:
    def __init__(self):
        self.url_api = "http://127.0.0.1:3900/v1/audio/speech"
        self.url_voces = "http://127.0.0.1:3900/v1/audio/voices"
        self.voice_id = "0b6fd25d"
        self.voice_name_legible = "Voice 06:13 PM — CLONE"

        if not pygame.mixer.get_init():
            pygame.mixer.init()

    def _limpiar_texto_para_tts(self, texto: str) -> str:
        if not texto:
            return ""
        return re.sub(r'\s+', ' ', texto).strip()

    def _resolver_voice_id(self):
        try:
            # Reducimos timeout de verificación a 3 segundos para no ralentizar el inicio
            r = requests.get(self.url_voces, timeout=3)
            if r.status_code != 200:
                return self.voice_id

            voces = r.json().get("voices", [])

            if any(v.get("voice_id") == self.voice_id for v in voces):
                return self.voice_id

            for v in voces:
                if v.get("name") == self.voice_name_legible:
                    print(f" [OmniVoice]: voice_id cambió de '{self.voice_id}' a '{v.get('voice_id')}', actualizando.")
                    self.voice_id = v.get("voice_id")
                    return self.voice_id

            print(f" [OmniVoice]: No se encontró '{self.voice_name_legible}'. Usando el último ID conocido.")
            return self.voice_id
        except Exception as e:
            print(f" [OmniVoice]: No se pudo verificar el voice_id ({e}). Usando el último conocido.")
            return self.voice_id

    def hablar(self, text: str, voice: str = None):
        """Genera y reproduce el audio asegurando la comunicación con el backend local."""
        texto_limpio = self._limpiar_texto_para_tts(text)

        # Evitar peticiones que rompan el motor local
        if not texto_limpio:
            print(" [OmniVoice]: Intento de vocalizar un texto vacío. Cancelado.")
            return

        voz_final = voice if voice else self._resolver_voice_id()

        print(f"[OmniVoice Request] -> {self.url_api}")
        print(f"Invocando clon exacto: voice_id='{voz_final}' ({self.voice_name_legible})")

        payload = {
            "model": "tts-1",
            "input": texto_limpio,     # <-- FALTABA: sin esto nunca se mandaba el texto a sintetizar
            "voice": voz_final,
            "response_format": "mp3"
        }

        output_filename = "output.mp3"

        try:
            # Timeout de lectura amplio para dar tiempo a la síntesis local
            respuesta = requests.post(self.url_api, json=payload, timeout=(5, 180), stream=True)

            if respuesta.status_code == 200:
                with open(output_filename, "wb") as f:
                    for chunk in respuesta.iter_content(chunk_size=4096):
                        if chunk:
                            f.write(chunk)

                print("🎵 [OmniVoice]: Audio generado con éxito. Reproduciendo...")
                pygame.mixer.music.load(output_filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)

                pygame.mixer.music.unload()
                if os.path.exists(output_filename):
                    try:
                        os.remove(output_filename)
                    except Exception as e:
                        print(f" No se pudo eliminar el archivo temporal: {e}")
            else:
                print(f" Error del servidor local (Código {respuesta.status_code}).")
                print(f"   Detalles devueltos por OmniVoice: {respuesta.text}")

        except requests.exceptions.Timeout:
            print(" [OmniVoice]: Error de Timeout. El servidor local tardó demasiado en responder.")
            print("👉 Consejo: Asegúrate de que el backend de OmniVoice está usando aceleración por hardware (CUDA/MPS) y no CPU pura.")
        except Exception as e:
            print(f" Error crítico de comunicación: {str(e)}")

# Instancia global requerida por el core del sistema
client_voz = ElevenLabsClient()