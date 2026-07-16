import os
import requests
import pygame

class ElevenLabsClient:
    def __init__(self):
        # Puerto confirmado en su archivo settings.json y capturas de pantalla
        self.url_api = "http://127.0.0.1:3900/v1/audio/speech"
        self.url_voces = "http://127.0.0.1:3900/v1/audio/voices"

        # Actualizado con el voice_id y el nombre que pasaste.
        self.voice_id = "0b6fd25d"
        self.voice_name_legible = "Voice 06:13 PM — CLONE"  # solo para logs

        if not pygame.mixer.get_init():
            pygame.mixer.init()

    def _resolver_voice_id(self):
        try:
            r = requests.get(self.url_voces, timeout=5)
            if r.status_code != 200:
                return self.voice_id  # no se pudo verificar, se usa el que hay

            voces = r.json().get("voices", [])

            # ¿Sigue existiendo el voice_id actual?
            if any(v.get("voice_id") == self.voice_id for v in voces):
                return self.voice_id

            # Si no, buscar por nombre y avisar del cambio
            for v in voces:
                if v.get("name") == self.voice_name_legible:
                    print(f"⚠️ [OmniVoice]: voice_id cambió de '{self.voice_id}' a '{v.get('voice_id')}', actualizando.")
                    self.voice_id = v.get("voice_id")
                    return self.voice_id

            print(f"⚠️ [OmniVoice]: No se encontró '{self.voice_name_legible}' entre las voces disponibles. Usando el último ID conocido.")
            return self.voice_id
        except Exception as e:
            print(f"⚠️ [OmniVoice]: No se pudo verificar el voice_id ({e}). Usando el último conocido.")
            return self.voice_id

    def hablar(self, text: str, voice: str = None):
        """Genera y reproduce el audio asegurando la comunicación con el backend local."""
        voz_final = voice if voice else self._resolver_voice_id()

        print(f"📡 [OmniVoice Request] -> {self.url_api}")
        print(f"   Invocando clon exacto: voice_id='{voz_final}' ({self.voice_name_legible})")

        payload = {
            "model": "tts-1",
            "input": text,
            "voice": voz_final,
            "response_format": "mp3"
        }

        output_filename = "output.mp3"

        try:
            respuesta = requests.post(self.url_api, json=payload, timeout=180, stream=True)

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
                    os.remove(output_filename)
            else:
                print(f"❌ Error del servidor local (Código {respuesta.status_code}).")
                print(f"   Detalles devueltos por OmniVoice: {respuesta.text}")

        except Exception as e:
            print(f"❌ Error crítico de comunicación: {str(e)}")

# Instancia global requerida por el core del sistema
client_voz = ElevenLabsClient()