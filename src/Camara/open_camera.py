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
        self.current_frame = None
        self.frame_referencia = None
        self._thread_camera = None
        self.sensibilidad_pct = 8.0
        self.cooldown_seg = 10.0
        self.intervalo_seg = 1.5
        self.ultimo_analisis = 0.0
        self.ultimo_resultado_txt = ""
        self.tiempo_mostrar_resultado = 0.0  # Timestamp para ocultar la tarjeta tras 8s

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

    def abrir_camara(self, voz_ia=None, sincronizar_estado_esfera=None, duracion_preview=None):
        if self.is_running:
            print("[CAM]: La cámara ya está activa.")
            return False

        self.is_running = True
        self._thread_camera = threading.Thread(
            target=self._bucle_principal, 
            args=(voz_ia, sincronizar_estado_esfera, duracion_preview),
            daemon=True
        )
        self._thread_camera.start()
        return True

    def _dibujar_hud_tactico(self, frame) -> cv2.Mat:
        """Renderiza elementos cibernéticos en el video sin alterar la imagen original."""
        hud = frame.copy()
        h, w, _ = frame.shape
        color_hud = (0, 255, 136) if self.vigilancia_activa else (255, 230, 0)  # BGR
        long = 35
        grosor = 2
        pad = 20
        cv2.line(hud, (pad, pad), (pad + long, pad), color_hud, grosor)
        cv2.line(hud, (pad, pad), (pad, pad + long), color_hud, grosor)
        cv2.line(hud, (w - pad, pad), (w - pad - long, pad), color_hud, grosor)
        cv2.line(hud, (w - pad, pad), (w - pad, pad + long), color_hud, grosor)
        cv2.line(hud, (pad, h - pad), (pad + long, h - pad), color_hud, grosor)
        cv2.line(hud, (pad, h - pad), (pad, h - pad - long), color_hud, grosor)
        cv2.line(hud, (w - pad, h - pad), (w - pad - long, h - pad), color_hud, grosor)
        cv2.line(hud, (w - pad, h - pad), (w - pad, h - pad - long), color_hud, grosor)
        # 2. BANNER DE ESTADO SUPERIOR
        estado_txt = "MODO VIGILANCIA [ACTIVO]" if self.vigilancia_activa else "VISION DIRECTA"
        cv2.rectangle(hud, (pad, pad), (320, pad + 30), (15, 15, 15), -1)
        cv2.rectangle(hud, (pad, pad), (320, pad + 30), color_hud, 1)
        cv2.putText(hud, f"REVAN // {estado_txt}", (pad + 10, pad + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color_hud, 1)

        cv2.circle(hud, (w - pad - 10, pad + 10), 6, color_hud, -1)

        if self.ultimo_resultado_txt and (time.time() - self.tiempo_mostrar_resultado < 8.0):
            overlay = hud.copy()
            caja_y1 = h - 110
            caja_y2 = h - pad
            # Caja de vidrio oscuro
            cv2.rectangle(overlay, (pad, caja_y1), (w - pad, caja_y2), (10, 10, 15), -1)
            cv2.rectangle(overlay, (pad, caja_y1), (w - pad, caja_y2), (0, 255, 136), 1)

            # Título del reporte
            cv2.putText(overlay, "INFORME VISUAL // NVIDIA NIM & GEMINI API", (pad + 15, caja_y1 + 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 136), 1)
            # Texto del reporte
            texto_clean = self.ultimo_resultado_txt.replace("Según mi sensor óptico: ", "")
            if len(texto_clean) > 85:
                texto_clean = texto_clean[:82] + "..."

            cv2.putText(overlay, texto_clean, (pad + 15, caja_y1 + 55),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
            # Fusionar capa con transparencia
            cv2.addWeighted(overlay, 0.85, hud, 0.15, 0, hud)

        return hud

    def _bucle_principal(self, voz_ia=None, sincronizar_estado_esfera=None, duracion_preview=None):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            print("[CAM]: No se pudo abrir el dispositivo de video.")
            self.is_running = False
            return
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        for _ in range(10):
            self.cap.read()
        ret, frame_inicial = self.cap.read()
        if ret:
            self.frame_referencia = frame_inicial.copy()
            with self.lock:
                self.current_frame = frame_inicial.copy()

        ultimo_chequeo_vigilancia = time.time()
        tiempo_inicio_preview = time.time()

        while self.is_running and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                continue

            with self.lock:
                self.current_frame = frame.copy()

            ahora = time.time()
            if duracion_preview is not None and (ahora - tiempo_inicio_preview) >= duracion_preview:
                break

            # Lógica de Vigilancia
            if self.vigilancia_activa and (ahora - ultimo_chequeo_vigilancia >= self.intervalo_seg):
                ultimo_chequeo_vigilancia = ahora
                
                if self.frame_referencia is not None:
                    cambio = self._porcentaje_cambio(self.frame_referencia, frame)
                    en_cooldown = (ahora - self.ultimo_analisis) < self.cooldown_seg

                    if cambio >= self.sensibilidad_pct and not en_cooldown:
                        print(f"[Vigilancia]: Cambio detectado ({cambio:.1f}%). Consultando visión API...")
                        self.ultimo_analisis = ahora

                        threading.Thread(
                            target=self._ejecutar_analisis_llava,
                            args=(frame.copy(), voz_ia, sincronizar_estado_esfera),
                            daemon=True
                        ).start()

                self.frame_referencia = frame.copy()

            # RENDERIZAR HUD CIBERNÉTICO
            frame_hud = self._dibujar_hud_tactico(frame)
            cv2.imshow("REVAN - CAMERA & VISION CENTER", frame_hud)

            # Salida manual con tecla ESC o 'q'
            if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
                break
        self.cerrar_camara()

    def _ejecutar_analisis_llava(self, frame, voz_ia, sincronizar_estado_esfera):
        """Ejecuta la visión por API y actualiza la tarjeta gráfica del HUD.

        'voz_ia' se espera que sea un callable hablar(texto) -no un objeto
        con .hablar()-. Antes esta función marcaba HABLANDO/ESPERA a mano
        con sincronizar_estado_esfera(), sin tocar la bandera 'esta_hablando'
        de main.py: el bucle de escucha de voz no se enteraba de que REVAN
        estaba hablando durante un análisis de cámara y podía pisar el
        color con ESCUCHANDO en cualquier momento -mismo bug de
        desincronización que se corrigió para el resto de las respuestas,
        pero que en este módulo quedaba fuera-. Ahora quien llama pasa un
        callback ya envuelto en hablar_sincronizado() (ver main.py), así
        que aquí ya no se toca el estado de la esfera para la parte de
        hablar; solo se anuncia el estado PROCESANDO antes del análisis.
        """
        if sincronizar_estado_esfera:
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")

        resultado = _analizar_frame_con_llava(frame)

        # Actualizar datos para el HUD
        with self.lock:
            self.ultimo_resultado_txt = resultado
            self.tiempo_mostrar_resultado = time.time()

        if voz_ia:
            voz_ia(resultado)

    def activar_vigilancia(self, activar=True):
        self.vigilancia_activa = activar
        print(f"[CAM]: Vigilancia {'ACTIVADA' if activar else 'DESACTIVADA'}.")

    def analizar_ahora(self, voz_ia=None, sincronizar_estado_esfera=None):
        with self.lock:
            if self.current_frame is None:
                return "No hay señal de cámara activa."
            snapshot = self.current_frame.copy()

        threading.Thread(
            target=self._ejecutar_analisis_llava,
            args=(snapshot, voz_ia, sincronizar_estado_esfera),
            daemon=True
        ).start()
        return "Analizando imagen táctica..."

    def capturar_y_analizar(self, duracion_segundos: float = 3.0,
                             voz_ia=None, sincronizar_estado_esfera=None) -> str:
        camara_ya_activa = self.is_running

        if not camara_ya_activa:
            self.abrir_camara(
                voz_ia=voz_ia,
                sincronizar_estado_esfera=sincronizar_estado_esfera,
                duracion_preview=duracion_segundos,
            )
            tiempo_limite = time.time() + duracion_segundos + 3.0
            while (
                self._thread_camera
                and self._thread_camera.is_alive()
                and time.time() < tiempo_limite
            ):
                time.sleep(0.05)
        else:
            time.sleep(0.3)

        with self.lock:
            if self.current_frame is None:
                return "No logré capturar una imagen estable de la cámara, Señor."
            snapshot = self.current_frame.copy()
        resultado_contenedor = {}

        def _tarea_analisis():
            resultado_contenedor["texto"] = _analizar_frame_con_llava(snapshot)

        hilo_analisis = threading.Thread(target=_tarea_analisis, daemon=True)
        hilo_analisis.start()

        if not camara_ya_activa:
            nombre_ventana = "REVAN - CAMERA & VISION CENTER"
            cv2.namedWindow(nombre_ventana, cv2.WINDOW_NORMAL)
            contador_animacion = 0
            while hilo_analisis.is_alive():
                frame_mostrado = snapshot.copy()
                puntos = "." * ((contador_animacion // 8) % 4)
                cv2.putText(
                    frame_mostrado,
                    f"REVAN analizando{puntos}",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 170),
                    2,
                    cv2.LINE_AA,
                )
                cv2.imshow(nombre_ventana, frame_mostrado)
                cv2.waitKey(30)
                contador_animacion += 1

            try:
                cv2.destroyWindow(nombre_ventana)
            except Exception:
                pass
            cv2.waitKey(1)
        else:
            hilo_analisis.join()

        resultado = resultado_contenedor.get("texto", "No se pudo completar el análisis de visión, Señor.")

        with self.lock:
            self.ultimo_resultado_txt = resultado
            self.tiempo_mostrar_resultado = time.time()

        return resultado

    def cerrar_camara(self):
        """Detiene la cámara y limpia la ventana."""
        self.is_running = False
        self.vigilancia_activa = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()
        print("[CAM]: Sistema de cámara liberado.")
revan_cam = RevanCameraManager()

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

def analizar_que_ve_camara(voz_ia=None, sincronizar_estado_esfera=None, duracion_segundos: float = 3.0) -> str:
    return revan_cam.capturar_y_analizar(
        duracion_segundos=duracion_segundos,
        voz_ia=voz_ia,
        sincronizar_estado_esfera=sincronizar_estado_esfera,
    )