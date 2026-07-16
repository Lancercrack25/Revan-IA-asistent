import cv2
import time
import threading

from src.Services.os_service import _analizar_frame_con_llava

sys_evento_detener = threading.Event()
_hilo_vigilancia = None


def _porcentaje_cambio(frame_a, frame_b) -> float:
    """
    Compara dos frames en escala de grises y devuelve qué porcentaje de
    píxeles cambió de forma significativa. Esto es pura aritmética de
    OpenCV/NumPy, sin ningún modelo de IA de por medio: no cuesta tokens,
    no toca la GPU para IA, es prácticamente gratis computacionalmente.
    """
    gris_a = cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY)
    gris_b = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)

    # Suavizado para ignorar ruido/grano de la cámara (que si no, dispara
    # falsos positivos constantemente incluso sin que nada se mueva)
    gris_a = cv2.GaussianBlur(gris_a, (21, 21), 0)
    gris_b = cv2.GaussianBlur(gris_b, (21, 21), 0)

    diferencia = cv2.absdiff(gris_a, gris_b)
    _, umbral = cv2.threshold(diferencia, 25, 255, cv2.THRESH_BINARY)

    pixeles_cambiados = cv2.countNonZero(umbral)
    total_pixeles = umbral.shape[0] * umbral.shape[1]

    return (pixeles_cambiados / total_pixeles) * 100


def _bucle_vigilancia(voz_ia, sincronizar_estado_esfera=None,intervalo_seg=1.5, sensibilidad_pct=8.0, cooldown_seg=10.0):
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[Vigilancia]: No se pudo abrir la cámara para iniciar la vigilancia.")
        return

    print("[Vigilancia]: Cámara abierta. Vigilando cambios de escena...")

    ret, frame_referencia = cap.read()
    if not ret:
        print("[Vigilancia]: No se pudo leer el primer frame. Abortando.")
        cap.release()
        return

    ultimo_analisis = 0.0

    try:
        while not sys_evento_detener.is_set():
            time.sleep(intervalo_seg)

            ret, frame_actual = cap.read()
            if not ret:
                continue

            cambio = _porcentaje_cambio(frame_referencia, frame_actual)
            en_cooldown = (time.time() - ultimo_analisis) < cooldown_seg

            if cambio >= sensibilidad_pct and not en_cooldown:
                print(f"[Vigilancia]: Cambio detectado ({cambio:.1f}%). Analizando con LLaVA...")

                if sincronizar_estado_esfera:
                    sincronizar_estado_esfera("PROCESANDO", "#ffaa00")

                resultado = _analizar_frame_con_llava(frame_actual)

                if sincronizar_estado_esfera:
                    sincronizar_estado_esfera("HABLANDO", "#ff0055")
                voz_ia.hablar(resultado)
                if sincronizar_estado_esfera:
                    sincronizar_estado_esfera("ESPERA", "#0077ff")

                ultimo_analisis = time.time()

            # El frame actual se vuelve la nueva referencia SIEMPRE (haya
            # disparado análisis o no), para que la comparación futura sea
            # contra "hace un momento" y no contra el inicio de la sesión.
            frame_referencia = frame_actual

    finally:
        cap.release()
        print("[Vigilancia]: Cámara liberada. Vigilancia detenida.")


def iniciar_vigilancia(voz_ia, sincronizar_estado_esfera=None,
                        intervalo_seg=1.5, sensibilidad_pct=8.0, cooldown_seg=10.0) -> bool:
    """Arranca la vigilancia en un hilo aparte. Devuelve False si ya estaba corriendo."""
    global _hilo_vigilancia

    if _hilo_vigilancia and _hilo_vigilancia.is_alive():
        print("[Vigilancia]: Ya está corriendo, no se inicia de nuevo.")
        return False

    sys_evento_detener.clear()
    _hilo_vigilancia = threading.Thread(
        target=_bucle_vigilancia,
        args=(voz_ia, sincronizar_estado_esfera, intervalo_seg, sensibilidad_pct, cooldown_seg),
        daemon=True
    )
    _hilo_vigilancia.start()
    return True


def detener_vigilancia() -> bool:
    """Señala al hilo de vigilancia que se detenga y libere la cámara."""
    global _hilo_vigilancia

    if not _hilo_vigilancia or not _hilo_vigilancia.is_alive():
        return False

    sys_evento_detener.set()
    _hilo_vigilancia.join(timeout=5)
    return True


def vigilancia_activa() -> bool:
    return bool(_hilo_vigilancia and _hilo_vigilancia.is_alive())