import os
import asyncio
import webbrowser
import sounddevice as sd
from scipy.io.wavfile import write
from shazamio import Shazam

TEMP_WAV = os.path.join(os.path.dirname(__file__), "temp_escucha.wav")

def obtener_dispositivo_loopback():
    """Busca el dispositivo de salida predeterminado en WASAPI para audio interno."""
    try:
        hostapis = sd.query_hostapis()
        wasapi_idx = None
        for i, api in enumerate(hostapis):
            if "WASAPI" in api["name"].upper():
                wasapi_idx = i
                break
        
        if wasapi_idx is not None:
            dev_out_id = sd.default.device[1]
            dev_info = sd.query_devices(dev_out_id)
            
            if dev_info["hostapi"] == wasapi_idx:
                return dev_out_id
            
            for i, dev in enumerate(sd.query_devices()):
                if dev["hostapi"] == wasapi_idx and dev["max_output_channels"] > 0:
                    return i
    except Exception as e:
        print(f"[Music Detector Warning]: Error buscando loopback WASAPI: {e}")
    return None

def capturar_audio_sistema(segundos: int = 6) -> str:
    """
    Estrategia de Captura Dual:
    1. Graba audio interno (WASAPI Loopback)
    2. Si falla, hace fallback automático al Micrófono Ambiental (Mono, 1 Canal)
    """
    print(f"[Music Detector]: Iniciando escucha ({segundos}s)...")
    
    dispositivo_loopback = obtener_dispositivo_loopback()
    grabacion = None
    samplerate = 44100
    fuente_usada = "Desconocida"

    # --- INTENTO 1: Audio Interno (Loopback) ---
    if dispositivo_loopback is not None:
        try:
            info_dev = sd.query_devices(dispositivo_loopback)
            samplerate = int(info_dev.get("default_samplerate", 44100))
        except Exception:
            pass

        try:
            wasapi_settings = sd.WasapiSettings()
            wasapi_settings.loopback = True

            grabacion = sd.rec(
                int(segundos * samplerate),
                samplerate=samplerate,
                channels=2,
                dtype='int16',
                device=dispositivo_loopback,
                extra_settings=wasapi_settings
            )
            sd.wait()
            fuente_usada = "Audio Interno (WASAPI Loopback)"
            print(f"[Music Detector]: Captura exitosa usando {fuente_usada}.")
        except Exception as err_loopback:
            print(f"[Music Detector Warning]: Loopback no disponible ({err_loopback}). Activando fallback a micrófono...")
            grabacion = None

    # --- INTENTO 2: Fallback a Micrófono Ambiental (1 Canal / Mono) ---
    if grabacion is None:
        try:
            samplerate = 44100
            print("[Music Detector]: Escuchando a través del Micrófono Ambiental...")
            grabacion = sd.rec(
                int(segundos * samplerate),
                samplerate=samplerate,
                channels=1,  # 1 Canal evita el error PaErrorCode -9998 en micrófonos mono
                dtype='int16'
            )
            sd.wait()
            fuente_usada = "Micrófono Ambiental"
            print(f"[Music Detector]: Captura exitosa usando {fuente_usada}.")
        except Exception as err_mic:
            print(f"[Music Detector Error]: Error crítico. No se pudo grabar audio en ningún modo: {err_mic}")
            raise err_mic

    write(TEMP_WAV, samplerate, grabacion)
    return TEMP_WAV

async def _reconocer_async(ruta_wav: str):
    shazam = Shazam()
    return await shazam.recognize(ruta_wav)

def identificar_y_abrir_cancion() -> str:
    try:
        archivo = capturar_audio_sistema(segundos=6)

        # Manejo asíncrono para Shazamio
        try:
            res = asyncio.run(_reconocer_async(archivo))
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            res = loop.run_until_complete(_reconocer_async(archivo))

        # Limpieza del archivo temporal
        if os.path.exists(archivo):
            try:
                os.remove(archivo)
            except Exception:
                pass

        track = res.get("track", {})
        if not track:
            return "No logré identificar la canción, Señor. Asegúrese de que el sonido sea claro."

        titulo = track.get("title", "Desconocida")
        artista = track.get("subtitle", "Artista Desconocido")
        
        # Abrir resultado en YouTube
        query = f"{titulo} {artista}".replace(" ", "+")
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")

        return f"La canción es '{titulo}' de {artista}. Abrí la búsqueda en YouTube para usted, Señor."

    except Exception as e:
        print(f"[Music Detector Exception]: {e}")
        return f"Hubo una interrupción al intentar procesar el reconocedor de música: {e}"