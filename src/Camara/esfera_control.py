#este archivo s eencargara de darle el funcionamineto de poder manipular la esfera del asistente con solo la vision de la camaraimport cv2
import time
import math
import threading
import cv2

try:
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False
    print("[ControlEsfera]: Falta 'mediapipe'. Instálalo con: pip install mediapipe")

from src.Interfaces.servidor import transmitir_manipulacion_desde_hilo_externo

_evento_detener = threading.Event()
_hilo_control = None

def _bucle_control_esfera(intervalo_seg: float = 0.05):
    if not HAS_MEDIAPIPE:
        print("[ControlEsfera]: No se puede iniciar sin mediapipe instalado.")
        return

    mp_hands = mp.solutions.hands
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("[ControlEsfera]: No se pudo abrir la cámara.")
        return

    print("[ControlEsfera]: Cámara abierta. Mueve tu mano frente a la cámara para manipular la esfera.")

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.5,
    ) as hands:

        try:
            while not _evento_detener.is_set():
                ret, frame = cap.read()
                if not ret:
                    time.sleep(intervalo_seg)
                    continue

                frame = cv2.flip(frame, 1)  # espejo: se siente más natural al manipular
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                resultado = hands.process(rgb)

                if resultado.multi_hand_landmarks:
                    landmarks = resultado.multi_hand_landmarks[0].landmark

                    # Landmark 0 = muñeca (referencia de posición)
                    # Landmark 12 = punta del dedo medio (referencia de "extensión" de la mano)
                    muneca = landmarks[0]
                    medio = landmarks[12]

                    # Posición normalizada (0.0 a 1.0 en cada eje) -> convertida
                    # a un rango de rotación en radianes centrado en 0
                    rot_y = (muneca.x - 0.5) * 2 * math.pi   # mano izq/der -> rota la esfera en Y
                    rot_x = (muneca.y - 0.5) * 2 * math.pi   # mano arriba/abajo -> rota la esfera en X

                    # Distancia muñeca-dedo medio como aproximación de escala,
                    # limitada (clamp) para que no se deforme de forma exagerada
                    distancia = math.hypot(medio.x - muneca.x, medio.y - muneca.y)
                    escala = max(0.7, min(1.5, distancia * 4))

                    transmitir_manipulacion_desde_hilo_externo(rot_x, rot_y, escala)

                time.sleep(intervalo_seg)  # ~20 actualizaciones/seg: fluido sin saturar el WebSocket

        finally:
            cap.release()
            print("[ControlEsfera]: Cámara liberada. Control por mano detenido.")


def iniciar_control_esfera() -> bool:
    """Arranca el control por mano en un hilo aparte. Devuelve False si ya estaba corriendo."""
    global _hilo_control

    if _hilo_control and _hilo_control.is_alive():
        print("[ControlEsfera]: Ya está corriendo, no se inicia de nuevo.")
        return False

    _evento_detener.clear()
    _hilo_control = threading.Thread(target=_bucle_control_esfera, daemon=True)
    _hilo_control.start()
    return True


def detener_control_esfera() -> bool:
    """Detiene el control por mano y libera la cámara."""
    global _hilo_control

    if not _hilo_control or not _hilo_control.is_alive():
        return False

    _evento_detener.set()
    _hilo_control.join(timeout=5)
    return True


def control_esfera_activo() -> bool:
    return bool(_hilo_control and _hilo_control.is_alive())