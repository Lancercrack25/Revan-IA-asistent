import os
import asyncio
import webbrowser
import sounddevice as sd
from scipy.io.wavfile import write
from shazamio import Shazam

TEMP_WAV = os.path.join(os.path.dirname(__file__), "temp_escucha.wav")

def obtener_dispositivo_loopback():
    """Busca el dispositivo Loopback WASAPI para grabar el audio interno (audífonos/altavoces)."""
    try:
        hostapis = sd.query_hostapis()
        wasapi_idx = None
        for i, api in enumerate(hostapis):
            if "WASAPI" in api["name"].upper():
                wasapi_idx = i
                break
        
        if wasapi_idx is not None:
            dispositivos = sd.query_devices()
            for i, dev in enumerate(dispositivos):
                # Busca un dispositivo de salida WASAPI marcado como loopback o la salida por defecto
                if dev["hostapi"] == wasapi_idx and dev["max_output_channels"] > 0:
                    # Devuelve el índice del dispositivo para usarlo en modo loopback
                    return i
    except Exception as e:
        print(f"[Music Detector Warning]: No se pudo autodetectar loopback WASAPI: {e}")
    
    return None  # Si falla, cae al dispositivo por defecto de sounddevice

def capturar_audio_sistema(segundos: int = 6) -> str:
    """Graba los audífonos/sistema usando loopback WASAPI de sounddevice."""
    print(f"[Music Detector]: Escuchando audio interno por {segundos} segundos...")
    samplerate = 44100
    
    # Intentamos habilitar la captura Loopback nativa en Windows
    try:
        # En sounddevice, pasar extra_settings le indica a WASAPI que grabe la salida
        wasapi_settings = sd.WasapiSettings(loopback=True)
        grabacion = sd.rec(
            int(segundos * samplerate),
            samplerate=samplerate,
            channels=2,
            dtype='int16',
            extra_settings=wasapi_settings
        )
    except Exception as err:
        print(f"[Music Detector]: Loopback directo falló ({err}), usando configuración estándar...")
        grabacion = sd.rec(int(segundos * samplerate), samplerate=samplerate, channels=1, dtype='int16')

    sd.wait()
    write(TEMP_WAV, samplerate, grabacion)
    return TEMP_WAV

async def _reconocer(ruta_wav: str):
    shazam = Shazam()
    return await shazam.recognize(ruta_wav)

def identificar_y_abrir_cancion() -> str:
    try:
        archivo = capturar_audio_sistema(segundos=6)
        
        # Manejo seguro del loop asyncio para no chocar si main.py ya tiene uno corriendo
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            # Si el bucle ya está corriendo en el hilo actual
            fut = asyncio.run_coroutine_threadsafe(_reconocer(archivo), loop)
            res = fut.result()
        else:
            res = loop.run_until_complete(_reconocer(archivo))

        # Limpieza del archivo temporal
        if os.path.exists(archivo):
            try:
                os.remove(archivo)
            except Exception:
                pass

        track = res.get("track", {})
        if not track:
            return "No logré identificar la canción que suena en sus audífonos, Señor."

        titulo = track.get("title", "Desconocida")
        artista = track.get("subtitle", "Artista Desconocido")
        
        # Abrir YouTube en el navegador
        query = f"{titulo} {artista}".replace(" ", "+")
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")

        return f"La canción es '{titulo}' de {artista}. Abrí la búsqueda en YouTube para usted, Señor."

    except Exception as e:
        print(f"[Music Detector Error]: {e}")
        return "Hubo una interrupción al intentar procesar el reconocedor de música."