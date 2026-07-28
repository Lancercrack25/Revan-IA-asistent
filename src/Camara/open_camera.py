import cv2
import time
import threading
from src.Services.os_service import _analizar_frame_con_llava

class RevanCameraManager:
    def __init__(self):
        self.cap = None
        self.is_running = False
        self.vigilancia_activa = False
        self.lock = threading.Lock()
        # Frames en memoria
        self.current_frame = None
        self.frame_referencia = None
        # Hilos
        self._thread_camera = None
        # Configuración de vigilancia
        self.sensibilidad_pct = 8.0
        self.cooldown_seg = 10.0
        self.intervalo_seg = 1.5
        self.ultimo_analisis = 0.0

    def _porcentaje_cambio(self, frame_a, frame_b) -> float:
        """Aritmética ligera en OpenCV para detectar movimiento sin consumir IA."""
        gris_a = cv2.cvtColor(frame_a, cv2.COLOR_BGR2GRAY)
        gris_b = cv2.cvtColor(frame_b, cv2.COLOR_BGR2GRAY)
        gris_a = cv2.GaussianBlur(gris_a, (21, 21), 0)
        gris_b = cv2.GaussianBlur(gris_b, (21, 21), 0)
        diferencia = cv2.absdiff(gris_a, gris_b)
        _, umbral = cv2.threshold(diferencia, 25, 255, cv2.THRESH_BINARY)
        pixeles_cambiados = cv2.countNonZero(umbral)
        total_pixeles = umbral.shape[0] * umbral.shape[1]
        return (pixeles_cambiados / total_pixeles) * 100

    def abrir_camara(self, voz_ia=None, sincronizar_estado_esfera=None):
        """Inicia el pipeline visual y la ventana OpenCV."""
        if self.is_running:
            print("[CAM]: La cámara ya está activa.")
            return False

        self.is_running = True
        self._thread_camera = threading.Thread(
            target=self._bucle_principal, 
            args=(voz_ia, sincronizar_estado_esfera),
            daemon=True
        )
        self._thread_camera.start()
        return True

    def _bucle_principal(self, voz_ia=None, sincronizar_estado_esfera=None):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            print("[CAM]: No se pudo abrir el dispositivo de video.")
            self.is_running = False
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        ret, frame_inicial = self.cap.read()
        if ret:
            self.frame_referencia = frame_inicial.copy()

        ultimo_chequeo_vigilancia = time.time()

        while self.is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue

            with self.lock:
                self.current_frame = frame.copy()
            ahora = time.time()
            if self.vigilancia_activa and (ahora - ultimo_chequeo_vigilancia >= self.intervalo_seg):
                ultimo_chequeo_vigilancia = ahora
                
                if self.frame_referencia is not None:
                    cambio = self._porcentaje_cambio(self.frame_referencia, frame)
                    en_cooldown = (ahora - self.ultimo_analisis) < self.cooldown_seg

                    if cambio >= self.sensibilidad_pct and not en_cooldown:
                        print(f"[Vigilancia]: Cambio detectado ({cambio:.1f}%). Consultando a LLaVA...")
                        self.ultimo_analisis = ahora

                        # Disparar análisis de LLaVA en un hilo separado para NO congelar el video en vivo
                        threading.Thread(
                            target=self._ejecutar_analisis_llava,
                            args=(frame.copy(), voz_ia, sincronizar_estado_esfera),
                            daemon=True
                        ).start()

                self.frame_referencia = frame.copy()
            hud_frame = frame.copy()
            estado_txt = "MODO VIGILANCIA: ACTIVO" if self.vigilancia_activa else "VISION DIRECTA"
            color_badge = (0, 255, 136) if self.vigilancia_activa else (255, 240, 0)

            # Capas visuales del HUD
            cv2.putText(hud_frame, f"REVAN // {estado_txt}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color_badge, 2)
            cv2.circle(hud_frame, (frame.shape[1] - 30, 30), 8, color_badge, -1)

            cv2.imshow("REVAN - CAMERA & VISION CENTER", hud_frame)

            # Salida manual con tecla ESC o 'q'
            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break

        self.cerrar_camara()

    def _ejecutar_analisis_llava(self, frame, voz_ia, sincronizar_estado_esfera):
        """Ejecuta LLaVA y gestiona los estados de la interfaz/voz."""
        if sincronizar_estado_esfera:
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")

        resultado = _analizar_frame_con_llava(frame)

        if sincronizar_estado_esfera:
            sincronizar_estado_esfera("HABLANDO", "#ff0055")
            
        if voz_ia:
            voz_ia.hablar(resultado)
            
        if sincronizar_estado_esfera:
            sincronizar_estado_esfera("ESPERA", "#0077ff")

    def activar_vigilancia(self, activar=True):
        self.vigilancia_activa = activar
        print(f"[CAM]: Vigilancia {'ACTIVADA' if activar else 'DESACTIVADA'}.")

    def analizar_ahora(self, voz_ia=None, sincronizar_estado_esfera=None):
        """Responde a la orden manual por voz/chat: 'REVAN, ¿qué ves?'."""
        with self.lock:
            if self.current_frame is None:
                return "No hay señal de cámara activa."
            snapshot = self.current_frame.copy()

        # Ejecuta LLaVA bajo demanda
        threading.Thread(
            target=self._ejecutar_analisis_llava,
            args=(snapshot, voz_ia, sincronizar_estado_esfera),
            daemon=True
        ).start()
        return "Analizando imagen táctica..."

    def cerrar_camara(self):
        """Detiene la cámara y limpia la ventana."""
        self.is_running = False
        self.vigilancia_activa = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        print("[CAM]: Sistema de cámara liberado.")

# Instancia Global del Módulo
revan_cam = RevanCameraManager()

# ==============================================================================
# FUNCIONES ENVOLVENTES (WRAPPERS) PARA COMPATIBILIDAD DIRECTA CON MAIN.PY
# ==============================================================================

def iniciar_vigilancia(voz_ia=None, sincronizar_estado_esfera=None) -> bool:
    """Abre la cámara si no está activa y habilita el modo vigilancia."""
    if not revan_cam.is_running:
        revan_cam.abrir_camara(voz_ia=voz_ia, sincronizar_estado_esfera=sincronizar_estado_esfera)
        time.sleep(0.5)

    if not revan_cam.vigilancia_activa:
        revan_cam.activar_vigilancia(True)
        return True
    return False

def detener_vigilancia() -> bool:
    """Desactiva la vigilancia y cierra la cámara limpia."""
    if revan_cam.vigilancia_activa or revan_cam.is_running:
        revan_cam.cerrar_camara()
        return True
    return False

def vigilancia_activa() -> bool:
    """Verifica si el modo vigilancia o la cámara están corriendo."""
    return revan_cam.vigilancia_activa or revan_cam.is_running

def analizar_que_ve_camara(voz_ia=None, sincronizar_estado_esfera=None) -> str:
    """Abre la cámara si está apagada y ejecuta la visión LLaVA instantánea."""
    if not revan_cam.is_running:
        revan_cam.abrir_camara(voz_ia=voz_ia, sincronizar_estado_esfera=sincronizar_estado_esfera)
        time.sleep(0.8)
    
    return revan_cam.analizar_ahora(voz_ia=voz_ia, sincronizar_estado_esfera=sincronizar_estado_esfera)