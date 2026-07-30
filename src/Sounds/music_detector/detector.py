import os
import asyncio
import webbrowser
import sounddevice as sd
from scipy.io.wavfile import write
from shazamio import Shazam

TEMP_WAV = os.path.join(os.path.dirname(__file__), "temp_escucha.wav")

def capturar_audio_ambiente(segundos: int = 6) -> str:
    """Graba unos segundos del audio del micrófono o sistema."""
    print(f"[Music Detector]: Escuchando ambiente por {segundos} segundos...")
    grabacion = sd.rec(int(segundos * 44100), samplerate=44100, channels=1, dtype='int16')
    sd.wait()
    write(TEMP_WAV, 44100, grabacion)
    return TEMP_WAV

async def _reconocer(ruta_wav: str):
    shazam = Shazam()
    return await shazam.recognize(ruta_wav)

def identificar_y_abrir_cancion() -> str:
    try:
        archivo = capturar_audio_ambiente(segundos=6)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(_reconocer(archivo))

        # Borrar temporal después de procesar
        if os.path.exists(archivo):
            os.remove(archivo)

        track = res.get("track", {})
        if not track:
            return "No logré identificar la canción que suena en el ambiente, Señor."

        titulo = track.get("title", "Desconocida")
        artista = track.get("subtitle", "Artista Desconocido")
        
        # Abrir YouTube con el tema encontrado
        query = f"{titulo} {artista}".replace(" ", "+")
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")

        return f"La canción es '{titulo}' de {artista}. Abrí la búsqueda en YouTube para usted, Señor."

    except Exception as e:
        print(f"[Music Detector Error]: {e}")
        return "Hubo una interrupción al intentar procesar el reconocedor de música."