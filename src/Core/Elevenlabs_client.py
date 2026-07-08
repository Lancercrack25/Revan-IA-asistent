import os
import asyncio
import pygame
import edge_tts
import time

class ElevenLabsClient:
    def __init__(self):
        """Inicializa el motor de voz neural local compatible con Tkinter y GUI."""
        self.voice = "es-MX-JorgeNeural"  # Voz neuronal en español mexicano
        self.archivo_temporal = "revan_voice.mp3"
        
        # Inicializamos el mezclador de pygame
        if not pygame.mixer.get_init():
            pygame.mixer.init()

    def hablar(self, texto):
        """
        Vocaliza el texto de forma SÍNCRONA. 
        Mantiene retenida la ejecución MIENTRAS suena la voz para que la esfera 3D
        se mantenga en rojo (#ff0055) exactamente hasta que REVAN termine de hablar.
        """
        try:
            # 1. Generar el archivo de audio
            asyncio.run(self._generar_audio(texto))
            
            # 2. Reproducir y esperar a que finalice el audio
            self._reproducir_audio()
        except Exception as e:
            print(f"❌ Error en el módulo de voz local: {e}")

    async def _generar_audio(self, texto):
        """Limpia el texto y descarga el audio desde la API de Edge-TTS."""
        texto_limpio = str(texto).replace("{", "").replace("}", "")
        texto_limpio = texto_limpio.replace("[", "").replace("]", "").strip()
        
        if not texto_limpio:
            texto_limpio = "Sistemas estables."
            
        communicate = edge_tts.Communicate(texto_limpio, self.voice, rate="-9%")
        await communicate.save(self.archivo_temporal)

    def _reproducir_audio(self):
        """Carga en Pygame y bloquea el hilo hasta que la reproducción termina."""
        if os.path.exists(self.archivo_temporal):
            pygame.mixer.music.load(self.archivo_temporal)
            pygame.mixer.music.play()
            
            # 🎯 Bucle de espera activo: Mantiene bloqueada la función mientras el audio suena
            while pygame.mixer.music.get_busy():
                time.sleep(0.05) 
                
            # Limpieza del reproductor y del archivo temporal
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            
            try:
                os.remove(self.archivo_temporal)
            except Exception:
                pass