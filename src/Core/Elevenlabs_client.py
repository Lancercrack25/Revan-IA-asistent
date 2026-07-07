import os
import asyncio
import pygame
import edge_tts
import time
import threading  # 👈 1. Importamos la librería de hilos táctica

class ElevenLabsClient:
    def __init__(self):
        """Inicializa el motor de voz neural local compatible con Tkinter y GUI."""
        self.voice = "es-MX-JorgeNeural"  # O la que prefieras probar
        self.archivo_temporal = "revan_voice.mp3"
        
        # Inicializamos el mezclador de pygame de forma segura
        pygame.mixer.init()

    def hablar(self, texto):
        """Vocaliza el texto en un hilo secundario para NO congelar Tkinter ni desincronizar comandos."""
        # 👈 2. Metemos todo el proceso en un hilo independiente (daemon=True)
        hilo_voz = threading.Thread(target=self._proceso_hablar_hilo, args=(texto,), daemon=True)
        hilo_voz.start()

    def _proceso_hablar_hilo(self, texto):
        """Método interno que gestiona la generación y reproducción en segundo plano."""
        try:
            # 3. Generamos el audio sincrónicamente en el loop del hilo secundario
            asyncio.run(self._generar_audio(texto))
            
            # 4. Reproducimos de forma controlada sin afectar a main.py
            self._reproducir_audio()
        except Exception as e:
            print(f"⚠️ Error en el módulo de voz local: {e}")

    async def _generar_audio(self, texto):
        texto_limpio = str(texto).replace("{", "").replace("}", "")
        texto_limpio = texto_limpio.replace("[", "").replace("]", "").strip()
        
        if not texto_limpio:
            texto_limpio = "Sistemas estables."
            
        communicate = edge_tts.Communicate(texto_limpio, self.voice, rate="-9%")
        await communicate.save(self.archivo_temporal)

    def _reproducir_audio(self):
        if os.path.exists(self.archivo_temporal):
            # Cargamos y disparamos el audio inmediatamente
            pygame.mixer.music.load(self.archivo_temporal)
            pygame.mixer.music.play()
            
            # Al estar en su propio hilo, este bucle ya no congela la app ni interrumpe el micrófono
            while pygame.mixer.music.get_busy():
                time.sleep(0.05) 
                
            # Forzamos la detención absoluta y descargamos el archivo
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            
            # Borramos el temporal de inmediato
            try:
                os.remove(self.archivo_temporal)
            except:
                pass