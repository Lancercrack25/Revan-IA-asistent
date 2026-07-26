import os
import sys
import time
import threading
import subprocess
import unicodedata

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

from src.Core.NimClient import NimClient
from src.Core.Elevenlabs_client import ElevenLabsClient
from src.Core.microphone_client import MicrophoneClient
from src.Core.Config_loader import cargar_ajustes, cargar_credenciales
from src.Gui.Dashboard import RevanGUI
from src.Automation.System_commands import desplegar_monitores_windows
from src.Interfaces.servidor import (
    iniciar_servidor_ui, transmitir_desde_hilo_externo,
    transmitir_chat_desde_hilo_externo, registrar_manejador_comando_texto,
)
from src.Database.init import inicializar_base_datos
from src.Services.agent_orchestrator import ejecutar_misión_compleja
from src.Camara.open_camera import iniciar_vigilancia, detener_vigilancia, vigilancia_activa
from src.Camara.esfera_control import iniciar_control_esfera, detener_control_esfera, control_esfera_activo
from src.Network.analize_network import analizar_red
from src.Network.velocidad_latencia import probar_velocidad_con_navegador, reportar_latencia
from src.Network.busqueda_intrusos import detectar_intrusos, marcar_todos_como_conocidos
from src.Core.Gemini_client import GeminiClient
from src.Phone.whatsapp_service import preparar_envio_inteligente, confirmar_envio_inteligente, cancelar_envio_pendiente

# Instancias y Controles Globales
cerebro_ia = None
gemini_ia = None
voz_ia = None
oidos_ia = None
gui = None
titulo = "Señor"
sistema_activo = False
ultima_interaccion = 0
TIEMPO_ATENCION = 18

PALABRAS_CLAVE_ACCION = [
    "word", "excel", "documento", "archivo", "carpeta", "crea", "crear",
    "abre", "abrir", "navegador", "brave", "youtube", "video", "busca",
    "juego", "jugar", "monitores", "camara", "mira", "whatsapp", "mensaje",
    "inicia", "iniciar", "lanza", "lanzar", "ejecuta", "ejecutar",
    "corre", "prende", "enciende", "investiga", "recuerda", "guarda", "analiza",
    "telefono", "celular", "envia", "enviar", "confirma", "confirmar", "cancela", "cancelar"
]

def quitar_acentos(texto: str) -> str:
    """Elimina acentos y tildes para evitar fallos de coincidencia por STT."""
    if not texto:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def hilo_servidor_web():
    """Ejecuta el servidor FastAPI/Uvicorn para la esfera 3D y el dashboard en un hilo dedicado."""
    try:
        servidor = iniciar_servidor_ui()
        servidor.run()
    except Exception as e:
        print(f" Error en el servidor web de la esfera: {e}")

def sincronizar_estado_esfera(estado, color_hex):
    """Envía los estados de voz e IA al loop de la esfera 3D vía WebSocket."""
    try:
        transmitir_desde_hilo_externo(estado, color_hex)
    except Exception as e:
        print(f" Error al sincronizar esfera: {e}")

def sincronizar_chat_dashboard(rol: str, texto: str):
    """Envía un mensaje de chat al dashboard web (además del chat de escritorio)."""
    try:
        transmitir_chat_desde_hilo_externo(rol, texto)
    except Exception as e:
        print(f" Error al sincronizar chat del dashboard: {e}")

def apagar_sistema():
    """Ejecuta el protocolo de desconexión y cierre limpio de REVAN."""
    global sistema_activo, gui
    print("\n[REVAN]: Iniciando secuencia de desconexión...")
    sistema_activo = False

    if vigilancia_activa():
        detener_vigilancia()
    if control_esfera_activo():
        detener_control_esfera()

    sincronizar_estado_esfera("HABLANDO", "#ff0055")
    if voz_ia:
        voz_ia.hablar(f"Desconectando sistemas. Hasta luego, {titulo}.")

    sincronizar_estado_esfera("DESCONECTADO", "#444444")
    time.sleep(0.5)

    if gui and hasattr(gui, 'app'):
        gui.app.after(100, gui.app.destroy)

    print("[REVAN]: Sistema totalmente apagado.")
    sys.exit(0)

def encender_sistemas():
    """Secuencia de despliegue cronológico."""
    global cerebro_ia, gemini_ia, voz_ia, oidos_ia, gui, titulo, sistema_activo
    sistema_activo = True

    print("Inicializando secuencia de despliegue cronológico...")
    print("[1/3] Desplegando monitores nativos...")
    try:
        desplegar_monitores_windows()
    except Exception as e:
        print(f"Aviso al desplegar monitores nativos: {e}")

    time.sleep(0.4)

    gui.actualizar_estado("CONECTANDO COGNICIÓN...", "#7ef1ff")
    sincronizar_estado_esfera("CONECTANDO", "#7ef1ff")
    print("[2/3] Panel CustomTkinter Activo.")

    try:
        credenciales = cargar_credenciales() or {}
        api_key_nim = credenciales.get("NVIDIA_NIM_API_KEY", os.getenv("NVIDIA_NIM_API_KEY", ""))

        cerebro_ia = NimClient(api_key=api_key_nim)
        gemini_ia = GeminiClient()
        voz_ia = ElevenLabsClient()

        gui.actualizar_estado("EN LÍNEA", "#7ef1ff")
        gui.agregar_mensaje("revan", f"Sistemas en línea, {titulo}. Listo para recibir instrucciones.")

        time.sleep(0.2)

        try:
            subprocess.Popen(
                'start brave --app=http://127.0.0.1:8000 --window-size=670,670',
                shell=True
            )
            print("[3/3] Núcleo Web Desplegado (Esfera 3D + Dashboard).")
        except Exception as e:
            print(f" Error al lanzar la interfaz web: {e}")

        # Registrar el manejador de comandos de texto que llegan desde el
        # dashboard web, para que servidor.py pueda invocarlo cuando el
        # WebSocket reciba un mensaje de tipo "comando_texto".
        registrar_manejador_comando_texto(procesar_comando_texto)

        sincronizar_estado_esfera("HABLANDO", "#ff0055")
        voz_ia.hablar(f"Sistemas en línea. Herramientas desplegadas exitosamente, {titulo}.")
        sincronizar_estado_esfera("ESPERA", "#0077ff")

        hilo_voz = threading.Thread(target=bucle_escucha_hilo, daemon=True)
        hilo_voz.start()

    except Exception as e:
        gui.actualizar_estado("ERROR EN COGNICIÓN", "#f85149")
        sincronizar_estado_esfera("ERROR", "#f85149")
        print(f" Error crítico al inicializar las APIs locales: {e}")

def bucle_escucha_hilo():
    global sistema_activo
    while sistema_activo:
        procesar_ciclo_voz()
        time.sleep(0.05)

def procesar_ciclo_voz():
    """Captura audio, aplica el filtro de palabra de activación ('Revan' /
    ventana de atención), y delega la orden ya limpia a ejecutar_orden()."""
    global oidos_ia, ultima_interaccion
    try:
        sincronizar_estado_esfera("ESCUCHANDO", "#00ffcc")
        print("\n[REVAN]: Escuchando...")

        orden_sucia = oidos_ia.escuchar()
        if not orden_sucia or not orden_sucia.strip():
            sincronizar_estado_esfera("ESPERA", "#0077ff")
            return

        orden_minusculas = orden_sucia.lower().strip()
        orden_busqueda = quitar_acentos(orden_minusculas)
        print(f"[Captura]: '{orden_minusculas}'")

        tiempo_actual = time.time()
        en_ventana_atencion = (tiempo_actual - ultima_interaccion) < TIEMPO_ATENCION

        if "revan" in orden_busqueda:
            partes = orden_minusculas.split("revan", 1)
            orden_limpia = partes[1].strip() if len(partes) > 1 else ""
            ultima_interaccion = tiempo_actual
        elif en_ventana_atencion:
            print("[MODO JARVIS]: Canal abierto. Procesando orden directa...")
            orden_limpia = orden_minusculas
            ultima_interaccion = tiempo_actual
        else:
            print("[REVAN]: Ruido de fondo o conversación ajena ignorada.")
            sincronizar_estado_esfera("ESPERA", "#0077ff")
            return

        if not orden_limpia:
            sincronizar_estado_esfera("HABLANDO", "#ff0055")
            time.sleep(0.15)
            voz_ia.hablar(f"Sistemas listos, {titulo}. ¿Qué comando desea ejecutar?")
            sincronizar_estado_esfera("ESPERA", "#0077ff")
            ultima_interaccion = time.time()
            return

        ejecutar_orden(orden_limpia, orden_mostrar=orden_sucia)

    except Exception as e:
        print(f"Error en el bucle táctico de voz: {e}")
        sincronizar_estado_esfera("ESPERA", "#0077ff")

def procesar_comando_texto(texto: str):
    global ultima_interaccion
    if not texto or not texto.strip():
        return

    print(f"[Modo Texto]: '{texto.strip()}'")
    ultima_interaccion = time.time()  # también extiende la ventana de atención por voz
    ejecutar_orden(texto.strip(), orden_mostrar=texto.strip())

def ejecutar_orden(orden_limpia: str, orden_mostrar: str = None):
    global cerebro_ia, gemini_ia, voz_ia, gui, ultima_interaccion

    orden_mostrar = orden_mostrar if orden_mostrar is not None else orden_limpia
    orden_limpia_sin_acentos = quitar_acentos(orden_limpia)

    def _hablar_y_mostrar(texto_respuesta: str):
        """Habla la respuesta Y la refleja en ambos chats (escritorio + dashboard web)."""
        sincronizar_estado_esfera("HABLANDO", "#ff0055")
        if gui and hasattr(gui, 'app'):
            gui.app.after(0, lambda u=orden_mostrar: gui.agregar_mensaje("user", u))
            gui.app.after(0, lambda b=texto_respuesta: gui.agregar_mensaje("revan", b))
        sincronizar_chat_dashboard("usuario", orden_mostrar)
        sincronizar_chat_dashboard("revan", texto_respuesta)
        voz_ia.hablar(texto_respuesta)
        sincronizar_estado_esfera("ESPERA", "#0077ff")
        ultima_interaccion = time.time()

    try:
        # --- INTERCEPTOR DE APAGADO ---
        palabras_desconexion = ["desconectar", "desconectate", "apagar", "apagate", "cerrar programa", "adios revan", "desconexion"]
        if any(cmd in orden_limpia_sin_acentos for cmd in palabras_desconexion):
            apagar_sistema()
            return

        # --- INTERCEPTOR MÓDULO TELÉFONO / WHATSAPP ---
        palabras_whatsapp = ["manda un whatsapp", "envia un whatsapp", "mandale un whatsapp", "enviale un whatsapp", "envia un mensaje", "manda un mensaje"]
        es_confirmacion = any(cmd in orden_limpia_sin_acentos for cmd in ["confirma", "confirmar", "envialo", "mandalo", "si envialo", "si mandala"])
        es_cancelacion = any(cmd in orden_limpia_sin_acentos for cmd in ["cancela", "cancelar", "aborta", "abortar", "no lo envies"])

        if es_confirmacion:
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            resultado = confirmar_envio_inteligente()
            _hablar_y_mostrar(resultado)
            return

        if es_cancelacion:
            resultado = cancelar_envio_pendiente()
            _hablar_y_mostrar(resultado)
            return

        if any(cmd in orden_limpia_sin_acentos for cmd in palabras_whatsapp):
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            try:
                partes_a = orden_limpia.split(" a ", 1)
                if len(partes_a) > 1:
                    partes_diga = partes_a[1].split(" que diga ", 1)
                    destinatario = partes_diga[0].strip()
                    mensaje_texto = partes_diga[1].strip() if len(partes_diga) > 1 else "Hola"

                    respuesta_prep = preparar_envio_inteligente(destinatario, mensaje_texto)
                    _hablar_y_mostrar(respuesta_prep)
                    return
            except Exception as err_wa:
                print(f"[Modulo Telefono]: Error analizando comando: {err_wa}")

        # --- INTERCEPTOR DE VIGILANCIA DE CÁMARA ---
        palabras_iniciar_vigilancia = ["vigila la camara", "vigilancia", "mantente al pendiente de la camara"]
        palabras_detener_vigilancia = ["deja de vigilar", "deten la vigilancia", "detente de vigilar", "para de vigilar"]

        if any(cmd in orden_limpia_sin_acentos for cmd in palabras_iniciar_vigilancia):
            if iniciar_vigilancia(voz_ia, sincronizar_estado_esfera):
                _hablar_y_mostrar(f"Vigilancia de cámara activada, {titulo}. Le avisaré si algo cambia.")
            else:
                _hablar_y_mostrar("La vigilancia ya estaba activa, Señor.")
            return

        if any(cmd in orden_limpia_sin_acentos for cmd in palabras_detener_vigilancia):
            if detener_vigilancia():
                _hablar_y_mostrar("Vigilancia de cámara desactivada.")
            else:
                _hablar_y_mostrar("No había ninguna vigilancia activa, Señor.")
            return

        # --- INTERCEPTOR DE CONTROL DE ESFERA POR MANO ---
        raices_control = ["control", "manipul", "mueve", "mover"]
        palabras_detener_intent = ["deja de", "deten", "detente", "para de", "suelta", "quita el control"]

        if "esfera" in orden_limpia_sin_acentos and any(p in orden_limpia_sin_acentos for p in palabras_detener_intent):
            if detener_control_esfera():
                _hablar_y_mostrar("Control de esfera desactivado.")
            else:
                _hablar_y_mostrar("No había ningún control de esfera activo, Señor.")
            return

        if "esfera" in orden_limpia_sin_acentos and any(r in orden_limpia_sin_acentos for r in raices_control):
            if vigilancia_activa():
                _hablar_y_mostrar("No puedo activar el control por mano mientras la vigilancia esté usando la cámara, Señor. Desactívela primero.")
            elif iniciar_control_esfera():
                _hablar_y_mostrar(f"Control de esfera por mano activado, {titulo}.")
            else:
                _hablar_y_mostrar("El control de esfera ya estaba activo, Señor.")
            return

        # --- INTERCEPTOR DE CONSULTAS DE RED ---
        palabras_lista = orden_limpia_sin_acentos.split()
        es_consulta_velocidad = "velocidad" in orden_limpia_sin_acentos and any(p in orden_limpia_sin_acentos for p in ["red", "internet", "conexion"])
        es_consulta_latencia = "latencia" in orden_limpia_sin_acentos or "ping" in palabras_lista
        es_consulta_intrusos = any(p in orden_limpia_sin_acentos for p in [
            "intruso", "intrusos", "quien esta conectado",
            "dispositivos conectados", "estoy seguro", "es segura mi red",
            "seguridad de mi red", "mi red es segura",
        ])
        es_marcar_conocidos = "marca" in orden_limpia_sin_acentos and ("conocido" in orden_limpia_sin_acentos or "conocidos" in orden_limpia_sin_acentos)
        es_consulta_red = (
            not (es_consulta_velocidad or es_consulta_latencia or es_consulta_intrusos or es_marcar_conocidos)
            and ("red" in palabras_lista or "ip" in palabras_lista or
                 any(p in orden_limpia_sin_acentos for p in ["internet", "conexion"]))
        )

        if es_consulta_velocidad:
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            voz_ia.hablar("Un momento, Señor, estoy abriendo el navegador y probando la velocidad de su conexión...")
            resultado_red = probar_velocidad_con_navegador()
            _hablar_y_mostrar(resultado_red)
            return

        if es_consulta_latencia:
            _hablar_y_mostrar(reportar_latencia())
            return

        if es_marcar_conocidos:
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            voz_ia.hablar("Un momento, Señor, estoy escaneando su red...")
            resultado_marcado = marcar_todos_como_conocidos()
            _hablar_y_mostrar(resultado_marcado)
            return

        if es_consulta_intrusos:
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            voz_ia.hablar("Un momento, Señor, estoy escaneando su red en busca de dispositivos intrusos...")
            resultado_intrusos = detectar_intrusos()
            _hablar_y_mostrar(resultado_intrusos)
            return

        if es_consulta_red:
            _hablar_y_mostrar(analizar_red())
            return

        sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
        print("[REVAN]: Procesando inteligencia...")

        if any(w in orden_limpia_sin_acentos for w in ["camara", "que ves"]):
            orden_limpia = "enciende la camara y dime que ves"
            orden_limpia_sin_acentos = quitar_acentos(orden_limpia)

        respuesta_final = None
        try:
            respuesta_final = ejecutar_misión_compleja(orden_limpia, cerebro_ia)
        except Exception as err_mision:
            print(f"[Orquestador]: Excepción en misión compleja: {err_mision}")

        if respuesta_final is None:
            es_comando_accion = any(palabra in orden_limpia_sin_acentos for palabra in PALABRAS_CLAVE_ACCION)

            if es_comando_accion:
                print("[Enrutador]: Orden táctica detectada -> NimClient")
                try:
                    respuesta_final = cerebro_ia.generar_respuesta(orden_limpia)
                except Exception as err_nim:
                    print(f"[Enrutador]: Error en NimClient: {err_nim}")

                if (not respuesta_final or not respuesta_final.strip()) and gemini_ia:
                    print("[Enrutador]: NimClient sin respuesta. Respaldando con Gemini...")
                    try:
                        respuesta_final = gemini_ia.generar_respuesta(orden_limpia)
                    except Exception as err_gemini:
                        print(f"[Enrutador]: Error en Gemini: {err_gemini}")
            else:
                print("[Enrutador]: Conversación detectada -> Gemini")
                if gemini_ia:
                    try:
                        respuesta_final = gemini_ia.generar_respuesta(orden_limpia)
                    except Exception as err_gemini:
                        print(f"[Enrutador]: Error en Gemini: {err_gemini}")

                if not respuesta_final or not respuesta_final.strip():
                    print("[Enrutador]: Gemini sin respuesta. Respaldando con NimClient...")
                    try:
                        respuesta_final = cerebro_ia.generar_respuesta(orden_limpia)
                    except Exception as err_nim:
                        print(f"[Enrutador]: Error en NimClient: {err_nim}")

        if not respuesta_final or not respuesta_final.strip():
            respuesta_final = f"No he recibido datos válidos del procesador táctico, {titulo}."

        _hablar_y_mostrar(respuesta_final)

    except Exception as e:
        print(f"Error al ejecutar la orden: {e}")
        sincronizar_estado_esfera("ESPERA", "#0077ff")

def main():
    global oidos_ia, gui, sistema_activo, titulo

    print("[REVAN]: Inicializando infraestructura base...")
    try:
        inicializar_base_datos()
    except Exception as e:
        print(f"Alerta al desplegar base de datos: {e}")

    ajustes = cargar_ajustes()
    titulo = ajustes.get("USER_NAME", "Señor") if ajustes else "Señor"
    t_web = threading.Thread(target=hilo_servidor_web, daemon=True)
    t_web.start()
    oidos_ia = MicrophoneClient()

    print("REVAN en modo pasivo. Esperando señal acústica...")
    while True:
        try:
            captura = oidos_ia.escuchar(modo_pasivo=True)
            if captura and captura.strip():
                print("¡Señal acústica validada! Inicializando REVAN...")
                break
        except Exception as e:
            print(f"Aviso en escaneo pasivo: {e}")
        time.sleep(0.1)

    print("Desplegando interfaz gráfica...")
    gui = RevanGUI(titulo_usuario=titulo)

    try:
        gui.mostrar_panel()
    except AttributeError:
        if hasattr(gui, 'app'):
            gui.app.deiconify()
    gui.app.after(250, encender_sistemas)
    gui.app.mainloop()

if __name__ == "__main__":
    main()