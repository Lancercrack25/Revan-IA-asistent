import os
import requests
import pygame
from src.Interfaces.voice_interface import IVoiceOutput
from src.Core.Config_loader import cargar_credenciales, cargar_ajustes

class ElevenLabsClient(IVoiceOutput):
    def __init__(self):
        # 1. Cargamos credenciales y ajustes
        credenciales = cargar_credenciales()
        ajustes = cargar_ajustes()
        
        if not credenciales or "ELEVENLABS_API_KEY" not in credenciales:
            raise ValueError("❌ No se encontró la ELEVENLABS_API_KEY.")
        if not ajustes or "VOICE_ID" not in ajustes:
            raise ValueError("❌ No se configuró el VOICE_ID en settings.json.")
            
        self.api_key = credenciales["ELEVENLABS_API_KEY"]
        self.voice_id = ajustes["VOICE_ID"]
        self.model_id = ajustes.get("MODEL_VOICE", "eleven_multilingual_v2")
        
        # 2. Inicializamos el motor de audio de pygame
        pygame.mixer.init()

    def hablar(self, texto: str):
        """Envía el texto a ElevenLabs, guarda un archivo temporal y lo reproduce."""
        print(f"🎙️ Revan está procesando audio...")
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        data = {
            "text": texto,
            "model_id": self.model_id,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        try:
            # Petición a la API
            respuesta = requests.post(url, json=data, headers=headers)
            
            if respuesta.status_code == 200:
                archivo_temporal = "temp_voice.mp3"
                
                # Guardamos el archivo de audio recibido
                with open(archivo_temporal, "wb") as f:
                    f.write(respuesta.content)
                
                # Reproducimos el audio con Pygame
                pygame.mixer.music.load(archivo_temporal)
                pygame.mixer.music.play()
                
                # Esperamos a que termine de hablar antes de continuar el código
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                
                # Liberamos el archivo de audio y lo borramos para no dejar basura
                pygame.mixer.music.unload()
                os.remove(archivo_temporal)
                
            else:
                print(f"❌ Error de ElevenLabs (Código {respuesta.status_code}): {respuesta.text}")
        except Exception as e:
            print(f"❌ Fallo al reproducir la voz de Revan: {str(e)}")