import os
import re
import asyncio
import threading
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
        # Antes en 12s: la primera generación de cada arranque de OmniVoice
        # Studio incluye cargar el modelo a memoria/VRAM, lo cual puede
        # tardar más que eso -sobre todo sin GPU dedicada-, así que
        # constantemente se rendía y caía al respaldo aunque el servidor sí
        # estuviera respondiendo, solo que lento. Se sube a 40s para darle
        # margen real a esa carga inicial.
        self.timeout_omnivoice = 40
        # Código ISO 639-1 para OmniVoice Studio. Confirmado contra el
        # esquema real de /v1/audio/speech (ver docs de OmniVoice Studio en
        # http://127.0.0.1:3900/docs): el campo se llama 'language' y espera
        # un código de 2 letras, no el nombre completo del idioma. Antes el
        # payload no mandaba este campo -sin él, el motor generaba con el
        # idioma por defecto (no español), lo que sonaba con acento/fonética
        # de otro idioma sobre la voz clonada, aunque la voz en sí ya estaba
        # guardada correctamente como español en su perfil.
        self.idioma_tts = "es"

        if not pygame.mixer.get_init():
            pygame.mixer.init()

    def _limpiar_texto_para_tts(self, texto: str) -> str:
        if not texto:
            return ""
        return re.sub(r'\s+', ' ', texto).strip()

    def _resolver_voice_id(self):
        try:
            r = requests.get(self.url_voces, timeout=2)
            if r.status_code != 200:
                return self.voice_id

            voces = r.json().get("voices", [])

            if any(v.get("voice_id") == self.voice_id for v in voces):
                return self.voice_id

            for v in voces:
                if v.get("name") == self.voice_name_legible:
                    print(f"[OmniVoice]: voice_id cambió de '{self.voice_id}' a '{v.get('voice_id')}', actualizando.")
                    self.voice_id = v.get("voice_id")
                    return self.voice_id

            print(f"[OmniVoice]: No se encontró '{self.voice_name_legible}'. Usando el último ID conocido.")
            return self.voice_id
        except Exception as e:
            # Silencioso cuando OmniVoice no está abierto para no saturar consola
            return self.voice_id

    def _intentar_omnivoice(self, texto_limpio: str) -> bool:
        """Intenta generar y reproducir con la voz clonada. Devuelve True si tuvo éxito."""
        voz_final = self._resolver_voice_id()

        payload = {
            "model": "tts-1",
            "input": texto_limpio,
            "voice": voz_final,
            "response_format": "mp3",
            "language": self.idioma_tts,
        }

        output_filename = "output.mp3"

        try:
            # Timeout de conexión muy reducido (1.5s) si OmniVoice no está corriendo
            respuesta = requests.post(
                self.url_api, json=payload,
                timeout=(1.5, self.timeout_omnivoice),
                stream=True,
            )

            if respuesta.status_code != 200:
                print(f"[Voz]: OmniVoice devolvió error {respuesta.status_code}.")
                return False

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
                    print(f"[Voz]: No se pudo eliminar el archivo temporal: {e}")

            return True

        except requests.exceptions.Timeout:
            print(f"[Voz]: OmniVoice tardó demasiado, cambiando a respaldo rápido...")
            return False
        except Exception:
            # OmniVoice fuera de línea -> saltar suavemente al respaldo
            return False

    async def _generar_audio_respaldo(self, texto: str, ruta_salida: str):
        comunicador = edge_tts.Communicate(texto, self.voz_respaldo)
        await comunicador.save(ruta_salida)

    def _hablar_respaldo(self, texto_limpio: str):
        """Respaldo rápido con edge_tts (Microsoft) con gestión asíncrona segura."""
        if not HAS_EDGE_TTS:
            print("[Voz]: No hay respaldo disponible (falta edge_tts). No se pudo hablar.")
            return

        output_filename = "output_respaldo.mp3"
        try:
            # Comprobar si hay un loop asíncrono en ejecución (FastAPI / WebSockets)
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # Enviar la tarea al loop existente sin bloquear el hilo principal
                future = asyncio.run_coroutine_threadsafe(
                    self._generar_audio_respaldo(texto_limpio, output_filename), loop
                )
                future.result(timeout=8)
            else:
                # Si no hay loop corriendo en este hilo
                asyncio.run(self._generar_audio_respaldo(texto_limpio, output_filename))

            # Reproducción de audio con pygame
            pygame.mixer.music.load(output_filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()

            if os.path.exists(output_filename):
                os.remove(output_filename)

        except Exception as e:
            print(f"[Voz Error]: Falló también la voz de respaldo: {e}")

    def hablar(self, text: str, voice: str = None):
        texto_limpio = self._limpiar_texto_para_tts(text)
        if not texto_limpio:
            print("[Voz]: Intento de vocalizar un texto vacío. Cancelado.")
            return

        exito = self._intentar_omnivoice(texto_limpio)
        if not exito:
            self._hablar_respaldo(texto_limpio)

    def precalentar_en_hilo(self):
        """
        Manda una petición mínima a OmniVoice en un hilo aparte, sin
        reproducir el resultado, solo para forzar que el motor cargue el
        modelo a memoria/VRAM antes de que el usuario reciba la primera
        respuesta real -esa carga inicial es la que se comía el timeout
        (ver self.timeout_omnivoice) y hacía caer al respaldo justo en el
        saludo de bienvenida.
        """
        def _tarea():
            try:
                requests.post(
                    self.url_api,
                    json={
                        "model": "tts-1",
                        "input": "hola",
                        "voice": self.voice_id,
                        "response_format": "mp3",
                        "language": self.idioma_tts,
                    },
                    timeout=(1.5, self.timeout_omnivoice),
                )
                print("[Voz]: OmniVoice precalentado.")
            except Exception:
                pass

        threading.Thread(target=_tarea, daemon=True).start()


# --- INSTANCIAS Y FUNCIONES DE COMPATIBILIDAD CON MAIN.PY ---
client_voz = ElevenLabsClient()

def hablar_en_hilo_seguro(texto: str):
    threading.Thread(
        target=client_voz.hablar,
        args=(texto,),
        daemon=True
    ).start()