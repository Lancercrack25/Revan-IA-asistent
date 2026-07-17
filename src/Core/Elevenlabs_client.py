import os
import re
import asyncio
import requests
import pygame

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False
    print("[Voz]: 'edge_tts' no instalado. Instálalo con: pip install edge-tts (necesario para el respaldo rápido).")


class ElevenLabsClient:
    def __init__(self):
        self.url_api = "http://127.0.0.1:3900/v1/audio/speech"
        self.url_voces = "http://127.0.0.1:3900/v1/audio/voices"
        self.voice_id = "0b6fd25d"
        self.voice_name_legible = "Voice 06:13 PM — CLONE"

        # Voz de respaldo de Microsoft Edge TTS (rápida, sin GPU, sin clon)
        self.voz_respaldo = "es-MX-JorgeNeural"

        # Timeout CORTO para OmniVoice: si no responde en este tiempo, se
        # asume que va a tardar demasiado y se cae directo al respaldo, en
        # vez de dejarte esperando minutos por tu voz clonada.
        self.timeout_omnivoice = 12  # segundos

        if not pygame.mixer.get_init():
            pygame.mixer.init()

    def _limpiar_texto_para_tts(self, texto: str) -> str:
        if not texto:
            return ""
        return re.sub(r'\s+', ' ', texto).strip()

    def _resolver_voice_id(self):
        try:
            r = requests.get(self.url_voces, timeout=3)
            if r.status_code != 200:
                return self.voice_id
            voces = r.json().get("voices", [])
            if any(v.get("voice_id") == self.voice_id for v in voces):
                return self.voice_id
            for v in voces:
                if v.get("name") == self.voice_name_legible:
                    self.voice_id = v.get("voice_id")
                    return self.voice_id
            return self.voice_id
        except Exception:
            return self.voice_id

    def _intentar_omnivoice(self, texto_limpio: str) -> bool:
        """Intenta generar y reproducir con la voz clonada. Devuelve True si
        tuvo éxito, False si falló o tardó demasiado (para caer al respaldo)."""
        voz_final = self._resolver_voice_id()

        payload = {
            "model": "tts-1",
            "input": texto_limpio,
            "voice": voz_final,
            "response_format": "mp3"
        }

        output_filename = "output.mp3"

        try:
            respuesta = requests.post(
                self.url_api, json=payload,
                timeout=(3, self.timeout_omnivoice),
                stream=True
            )

            if respuesta.status_code != 200:
                print(f"[Voz]: OmniVoice devolvió error {respuesta.status_code}, usando respaldo.")
                return False

            with open(output_filename, "wb") as f:
                for chunk in respuesta.iter_content(chunk_size=4096):
                    if chunk:
                        f.write(chunk)

            pygame.mixer.music.load(output_filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()

            if os.path.exists(output_filename):
                try:
                    os.remove(output_filename)
                except Exception:
                    pass

            return True

        except requests.exceptions.Timeout:
            print(f"[Voz]: OmniVoice tardó más de {self.timeout_omnivoice}s, usando respaldo rápido.")
            return False
        except Exception as e:
            print(f"[Voz]: OmniVoice no disponible ({e}), usando respaldo rápido.")
            return False

    async def _generar_audio_respaldo(self, texto: str, ruta_salida: str):
        comunicador = edge_tts.Communicate(texto, self.voz_respaldo)
        await comunicador.save(ruta_salida)

    def _hablar_respaldo(self, texto_limpio: str):
        """Respaldo rápido con edge_tts (Microsoft), sin GPU, sin clon."""
        if not HAS_EDGE_TTS:
            print("[Voz]: No hay respaldo disponible (falta edge_tts). No se pudo hablar.")
            return

        output_filename = "output_respaldo.mp3"
        try:
            asyncio.run(self._generar_audio_respaldo(texto_limpio, output_filename))

            pygame.mixer.music.load(output_filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()

            if os.path.exists(output_filename):
                os.remove(output_filename)
        except Exception as e:
            print(f"[Voz]: Falló también el respaldo: {e}")

    def hablar(self, text: str, voice: str = None):
        """
        Intenta primero la voz clonada (OmniVoice). Si tarda más de
        self.timeout_omnivoice o falla, cae automáticamente a edge_tts
        (rápido, confiable, sin GPU) para que REVAN siempre responda,
        aunque a veces sea con voz genérica en vez de tu clon.
        """
        texto_limpio = self._limpiar_texto_para_tts(text)
        if not texto_limpio:
            return

        exito = self._intentar_omnivoice(texto_limpio)
        if not exito:
            self._hablar_respaldo(texto_limpio)


# Instancia global requerida por el core del sistema
client_voz = ElevenLabsClient()