import os
import threading
HAS_PYGAME = False
try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except Exception:
    import winsound

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def _play_audio(ruta_archivo: str):
    if not os.path.exists(ruta_archivo):
        return
    try:
        if HAS_PYGAME:
            sonido = pygame.mixer.Sound(ruta_archivo)
            sonido.play()
        elif ruta_archivo.endswith(".wav"):
            winsound.PlaySound(ruta_archivo, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        print(f"[Sound FX Error]: {e}")

def reproducir_sfx(categoria: str, nombre_efecto: str):
    carpeta_destino = os.path.join(BASE_DIR, categoria)
    ruta_wav = os.path.join(carpeta_destino, f"{nombre_efecto}.wav")
    ruta_mp3 = os.path.join(carpeta_destino, f"{nombre_efecto}.mp3")
    target = ruta_wav if os.path.exists(ruta_wav) else ruta_mp3

    if os.path.exists(target):
        threading.Thread(target=_play_audio, args=(target,), daemon=True).start()
    else:
        print(f"[SFX Info]: No se encontró el audio en '{categoria}/{nombre_efecto}'")