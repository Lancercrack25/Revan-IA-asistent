import os
import sys
import time
import threading
import subprocess
import unicodedata

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

from src.Core.NimClient import NimClient
from src.Core.Elevenlabs_client import ElevenLabsClient, hablar_en_hilo_seguro
from src.Core.microphone_client import MicrophoneClient
from src.Core.Config_loader import cargar_ajustes, cargar_credenciales
from src.Automation.System_commands import desplegar_monitores_windows
from src.Interfaces.servidor import (iniciar_servidor_ui, transmitir_desde_hilo_externo,transmitir_chat_desde_hilo_externo, registrar_manejador_comando_texto,)
from src.Database.init import inicializar_base_datos
from src.Services.agent_orchestrator import ejecutar_misión_compleja
from src.Core.Gemini_client import GeminiClient
from src.Camara.open_camera import iniciar_vigilancia, detener_vigilancia, vigilancia_activa
from src.Camara.esfera_control import iniciar_control_esfera, detener_control_esfera, control_esfera_activo
from src.Network.analize_network import analizar_red, abrir_terminal_ping, abrir_terminal_scan
from src.Network.velocidad_latencia import probar_velocidad_con_navegador, reportar_latencia
from src.Network.busqueda_intrusos import detectar_intrusos, marcar_todos_como_conocidos
from src.Phone.whatsapp_service import preparar_envio_inteligente, confirmar_envio_inteligente, cancelar_envio_pendiente
from src.Emails.email_control import (leer_ultimos_correos, contar_correos_sin_leer,preparar_borrador_correo, confirmar_envio_correo, cancelar_borrador_correo)
from src.Emails.registro_agenda import agendar_evento, consultar_agenda_hoy
from src.Emails.utils.nlp_date_parser import parsear_fecha_natural
from src.Sounds.sounds_main import reproducir_sfx

cerebro_ia = None
gemini_ia = None
voz_ia = None
oidos_ia = None
titulo = "Señor"
sistema_activo = False
esta_hablando = False
ultima_interaccion = 0
TIEMPO_ATENCION = 18

PALABRAS_CLAVE_ACCION = [
    "word", "excel", "documento", "archivo", "carpeta", "crea", "crear",
    "abre", "abrir", "navegador", "brave", "youtube", "video", "busca",
    "juego", "jugar", "monitores", "camara", "mira", "whatsapp", "mensaje",
    "inicia", "iniciar", "lanza", "lanzar", "ejecuta", "ejecutar",
    "corre", "prende", "enciende", "investiga", "recuerda", "guarda", "analiza",
    "telefono", "celular", "envia", "enviar", "confirma", "confirmar", "cancela", "cancelar",
    "correo", "correos", "email", "inbox", "buzon", "agenda", "agendar", "evento", "reunion", "cita"
]

def quitar_acentos(texto: str) -> str:
    if not texto:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def es_intencion_de_comando(texto: str) -> bool:
    texto_sin_acentos = quitar_acentos(texto.lower())
    es_orden = any(palabra in texto_sin_acentos for palabra in PALABRAS_CLAVE_ACCION)
    
    if es_orden:
        print("Clasificado localmente -> ORDEN")
    else:
        print("Clasificado localmente -> CONVERSACIÓN")
        
    return es_orden

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
    try:
        transmitir_chat_desde_hilo_externo(rol, texto)
    except Exception as e:
        print(f" Error al sincronizar chat del dashboard: {e}")

def apagar_sistema():
    """Ejecuta el protocolo de desconexión y cierre limpio de REVAN."""
    global sistema_activo, esta_hablando
    print("\n[REVAN]: Iniciando secuencia de desconexión...")
    sistema_activo = False

    if vigilancia_activa():
        detener_vigilancia()
    if control_esfera_activo():
        detener_control_esfera()

    esta_hablando = True
    sincronizar_estado_esfera("HABLANDO", "#ff0055")
    reproducir_sfx("welcome", "close")
    if voz_ia:
        voz_ia.hablar(f"Desconectando sistemas, {titulo}.")
    esta_hablando = False
    sincronizar_estado_esfera("DESCONECTADO", "#444444")
    time.sleep(0.5)

    print("[REVAN]: Sistema totalmente apagado.")
    sys.exit(0)

def encender_sistemas():
    global cerebro_ia, gemini_ia, voz_ia, oidos_ia, titulo, sistema_activo, esta_hablando
    sistema_activo = True

    print("Inicializando secuencia de despliegue cronológico...")
    print("[1/2] Desplegando monitores nativos...")
    try:
        desplegar_monitores_windows()
    except Exception as e:
        print(f"Aviso al desplegar monitores nativos: {e}")

    time.sleep(0.4)
    sincronizar_estado_esfera("CONECTANDO", "#7ef1ff")

    try:
        credenciales = cargar_credenciales() or {}
        api_key_nim = credenciales.get("NVIDIA_NIM_API_KEY", os.getenv("NVIDIA_NIM_API_KEY", ""))
        cerebro_ia = NimClient(api_key=api_key_nim)
        gemini_ia = GeminiClient()
        voz_ia = ElevenLabsClient()
        sincronizar_chat_dashboard("revan", f"Sistemas en línea, {titulo}. Listo para recibir instrucciones.")
        time.sleep(0.2)

        try:
            subprocess.Popen(
                'start brave --app=http://127.0.0.1:8000 --window-size=670,670',
                shell=True
            )
            print("[2/2] Núcleo Web Desplegado (Esfera 3D + Dashboard).")
            reproducir_sfx("welcome", "Bienvenida")
        except Exception as e:
            print(f" Error al lanzar la interfaz web: {e}")

        registrar_manejador_comando_texto(procesar_comando_texto)

        def saludo_inicial():
            global esta_hablando
            esta_hablando = True
            sincronizar_estado_esfera("HABLANDO", "#ff0055")
            if voz_ia:
                voz_ia.hablar(f"Bienvenido, {titulo}. Sistemas principales en línea,módulos y agentes han sido sincronizados exitosamente.un honor estar de vuelta listo para ejecutar sus nuevas ideas, ¿Que es lo que tiene en mente hoy {titulo}?")
            time.sleep(0.3)
            esta_hablando = False
            sincronizar_estado_esfera("ESPERA", "#0077ff")

        threading.Thread(target=saludo_inicial, daemon=True).start()
        hilo_voz = threading.Thread(target=bucle_escucha_hilo, daemon=True)
        hilo_voz.start()

    except Exception as e:
        sincronizar_estado_esfera("ERROR", "#f85149")
        print(f" Error crítico al inicializar las APIs locales: {e}")

def bucle_escucha_hilo():
    global sistema_activo
    while sistema_activo:
        procesar_ciclo_voz()
        time.sleep(0.05)

def procesar_ciclo_voz():
    global oidos_ia, ultima_interaccion, esta_hablando
    try:
        if esta_hablando:
            time.sleep(0.2)
            return

        sincronizar_estado_esfera("ESCUCHANDO", "#00ffcc")
        print("\n[REVAN]: Escuchando...")
        orden_sucia = oidos_ia.escuchar()

        if esta_hablando:
            return

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
            def responder_listo():
                global esta_hablando
                esta_hablando = True
                sincronizar_estado_esfera("HABLANDO", "#ff0055")
                if voz_ia:
                    voz_ia.hablar(f"Sistemas listos, {titulo}. ¿Qué comando desea ejecutar?")
                time.sleep(0.3)
                esta_hablando = False
                sincronizar_estado_esfera("ESPERA", "#0077ff")

            threading.Thread(target=responder_listo, daemon=True).start()
            ultima_interaccion = time.time()
            return

        ejecutar_orden(orden_limpia, orden_mostrar=orden_sucia)

    except Exception as e:
        print(f"Error en el bucle táctico de voz: {e}")
        sincronizar_estado_esfera("ESPERA", "#0077ff")

def procesar_comando_texto(texto: str):
    """Procesa mensajes que entran directamente desde el dashboard web."""
    global ultima_interaccion
    if not texto or not texto.strip():
        return

    print(f"[Modo Texto Recibido]: '{texto.strip()}'")
    ultima_interaccion = time.time()
    
    threading.Thread(
        target=ejecutar_orden,
        args=(texto.strip(), texto.strip()),
        daemon=True
    ).start()

def ejecutar_orden(orden_limpia: str, orden_mostrar: str = None):
    global cerebro_ia, gemini_ia, voz_ia, ultima_interaccion, esta_hablando
    orden_mostrar = orden_mostrar if orden_mostrar is not None else orden_limpia
    orden_limpia_sin_acentos = quitar_acentos(orden_limpia)

    def _hablar_y_mostrar(texto_respuesta: str):
        """Sincroniza el chat y bloquea la esfera en rojo durante la voz de ElevenLabs."""
        global ultima_interaccion, esta_hablando
        
        sincronizar_chat_dashboard("usuario", orden_mostrar)
        sincronizar_chat_dashboard("revan", texto_respuesta)

        def tarea_sincronizada_voz():
            global esta_hablando
            esta_hablando = True
            
            sincronizar_estado_esfera("HABLANDO", "#ff0055")
            
            if voz_ia:
                try:
                    voz_ia.hablar(texto_respuesta)
                except Exception as err_voz:
                    print(f"[Voz Error]: Fallo en la reproducción: {err_voz}")
            
            time.sleep(0.3)
            esta_hablando = False
            sincronizar_estado_esfera("ESPERA", "#0077ff")
        threading.Thread(target=tarea_sincronizada_voz, daemon=True).start()
        ultima_interaccion = time.time()

    try:
        # --- 1. SALUDOS BÁSICOS ---
        saludos_basicos = [
            "hola", "hola revan", "buenos dias", "buenas tardes", "buenas noches",
            "como estas", "hola como estas", "como estas revan", "que tal", "hola como estas ?", "que rollo", "que onda", "que pedo"
        ]
        if orden_limpia_sin_acentos.strip().rstrip("?") in saludos_basicos:
            print("[Escudo Local]: Saludo común detectado. Respondiendo localmente sin gastar tokens.")
            _hablar_y_mostrar(f"Sistemas nominales y en línea, {titulo}. ¿En qué puedo ayudarle hoy?")
            return

        palabras_desconexion = ["desconectar", "desconectate", "apagar", "apagate", "cerrar programa", "adios revan", "desconexion"]
        if any(cmd in orden_limpia_sin_acentos for cmd in palabras_desconexion):
            apagar_sistema()
            return
        # --- 2. MÓDULO EMAIL ---
        es_conteo_correo = any(p in orden_limpia_sin_acentos for p in ["cuantos correos", "correos por ver", "correos pendientes", "correos sin leer"])
        es_consulta_correo = not es_conteo_correo and any(
            p in orden_limpia_sin_acentos for p in [
                "leer correo", "revisar correo", "mis correos", "ver correos", 
                "buzon", "ultimos correos", "cuales son los correos", "cuales son los ultimos correos",
                "que correos tengo", "mis ultimos correos"
            ]
        )
        
        es_redaccion_asistida = any(p in orden_limpia_sin_acentos for p in ["ayudame a redactar", "redacta un correo", "escribe un correo", "haz un correo"])
        es_envio_directo = not es_redaccion_asistida and any(p in orden_limpia_sin_acentos for p in ["enviar correo", "manda un correo", "mandar correo", "envia un correo", "manda correo", "envia correo"])
        es_confirmar_mail = any(p in orden_limpia_sin_acentos for p in ["confirma el correo", "envia el correo", "confirmo correo"])
        es_cancelar_mail = any(p in orden_limpia_sin_acentos for p in ["cancela el correo", "descarta el correo"])

        if es_confirmar_mail:
            reproducir_sfx("modules", "emails")
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            _hablar_y_mostrar(confirmar_envio_correo())
            return

        if es_cancelar_mail:
            reproducir_sfx("modules", "emails")
            _hablar_y_mostrar(cancelar_borrador_correo())
            return

        if es_conteo_correo:
            reproducir_sfx("modules", "emails")
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            cantidad = contar_correos_sin_leer()
            if cantidad >= 0:
                _hablar_y_mostrar(f"Tiene {cantidad} correos sin leer en su buzón de entrada, {titulo}.")
            else:
                _hablar_y_mostrar("No pude verificar la cantidad de correos sin leer. Revise sus credenciales de acceso.")
            return

        if es_consulta_correo:
            reproducir_sfx("modules", "emails")
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            hablar_en_hilo_seguro(f"Revisando su buzón de entrada, {titulo}...")
            resumenes = leer_ultimos_correos(max_resultados=3)
            _hablar_y_mostrar("Señor, " + " ".join(resumenes))
            return

        if es_redaccion_asistida:
            reproducir_sfx("modules", "emails")
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            prompt_redaccion = f"Redacta un correo profesional basado en esta solicitud del usuario: '{orden_limpia}'. Devuelve únicamente el asunto y el cuerpo del mensaje bien formateados."
            
            cuerpo_generado = cerebro_ia.generar_respuesta(prompt_redaccion) if cerebro_ia else "No fue posible generar la redacción automáticamente."
            
            destinatario = "correo_por_defecto@ejemplo.com"
            if " a " in orden_limpia:
                partes = orden_limpia.split(" a ", 1)
                destinatario = partes[1].split()[0].strip()

            respuesta_preparada = preparar_borrador_correo(destinatario, "Notificación Generada por REVAN", cuerpo_generado)
            _hablar_y_mostrar(respuesta_preparada)
            return

        if es_envio_directo:
            reproducir_sfx("modules", "emails")
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            try:
                partes_a = orden_limpia.split(" a ", 1)
                if len(partes_a) > 1:
                    resto = partes_a[1]
                    partes_asunto = resto.split(" con asunto ", 1)
                    destinatario = partes_asunto[0].strip()

                    if len(partes_asunto) > 1:
                        partes_mensaje = partes_asunto[1].split(" y mensaje ", 1)
                        asunto = partes_mensaje[0].strip()
                        cuerpo = partes_mensaje[1].strip() if len(partes_mensaje) > 1 else "Mensaje enviado desde REVAN Assistant."
                    else:
                        asunto = "Notificación de REVAN Assistant"
                        cuerpo = "Mensaje sin cuerpo especificado."

                    respuesta_preparada = preparar_borrador_correo(destinatario, asunto, cuerpo)
                    _hablar_y_mostrar(respuesta_preparada)
                    return
                else:
                    _hablar_y_mostrar("Indíqueme el correo con el formato: envía un correo a 'destinatario' con asunto 'tema' y mensaje 'texto'.")
                    return
            except Exception as err_mail:
                print(f"[Email Error]: {err_mail}")
        # --- 3. MÓDULO AGENDA ---
        es_consulta_agenda = any(p in orden_limpia_sin_acentos for p in ["que tengo hoy", "agenda hoy", "eventos de hoy", "mis citas de hoy", "agenda del dia"])
        es_crear_evento = any(p in orden_limpia_sin_acentos for p in ["agendar", "agenda una", "agenda un", "crea un evento", "crear evento", "recuerdame"])

        if es_consulta_agenda:
            reproducir_sfx("modules", "Agenda")
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            resumen_agenda = consultar_agenda_hoy()
            _hablar_y_mostrar(resumen_agenda)
            return

        if es_crear_evento:
            reproducir_sfx("modules", "Agenda")
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            fecha_iso = parsear_fecha_natural(orden_limpia_sin_acentos)
            
            titulo_evento = "Compromiso Agendado"
            for disparador in ["agendar", "agenda", "recuerdame", "crea un evento"]:
                if disparador in orden_limpia_sin_acentos:
                    partes = orden_limpia.split(disparador, 1)
                    if len(partes) > 1 and partes[1].strip():
                        titulo_evento = partes[1].strip().capitalize()
                    break

            resultado_agendado = agendar_evento(
                titulo=titulo_evento,
                fecha_hora_str=fecha_iso,
                duracion_minutos=60
            )
            _hablar_y_mostrar(resultado_agendado)
            return
        # --- 4. MÓDULO WHATSAPP ---
        palabras_whatsapp = ["manda un whatsapp", "envia un whatsapp", "mandale un whatsapp", "enviale un whatsapp", "envia un mensaje", "manda un mensaje"]
        es_confirmacion = any(cmd in orden_limpia_sin_acentos for cmd in ["confirma", "confirmar", "envialo", "mandalo", "si envialo", "si mandala"])
        es_cancelacion = any(cmd in orden_limpia_sin_acentos for cmd in ["cancela", "cancelar", "aborta", "abortar", "no lo envies"])

        if es_confirmacion:
            reproducir_sfx("modules", "whats")
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            resultado = confirmar_envio_inteligente()
            _hablar_y_mostrar(resultado)
            return

        if es_cancelacion:
            reproducir_sfx("modules", "whats")
            resultado = cancelar_envio_pendiente()
            _hablar_y_mostrar(resultado)
            return

        if any(cmd in orden_limpia_sin_acentos for cmd in palabras_whatsapp):
            reproducir_sfx("modules", "whats")
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

        # --- 5. MÓDULO CÁMARA Y CONTROL DE ESFERA ---
        palabras_iniciar_vigilancia = ["vigila la camara", "vigilancia", "mantente al pendiente de la camara"]
        palabras_detener_vigilancia = ["deja de vigilar", "deten la vigilancia", "detente de vigilar", "para de vigilar"]

        if any(cmd in orden_limpia_sin_acentos for cmd in palabras_iniciar_vigilancia):
            reproducir_sfx("modules", "Cam")
            if iniciar_vigilancia(voz_ia, sincronizar_estado_esfera):
                _hablar_y_mostrar(f"Vigilancia de cámara activada, {titulo}. Le avisaré si algo cambia.")
            else:
                _hablar_y_mostrar("La vigilancia ya estaba activa, Señor.")
            return

        if any(cmd in orden_limpia_sin_acentos for cmd in palabras_detener_vigilancia):
            reproducir_sfx("modules", "Cam")
            if detener_vigilancia():
                _hablar_y_mostrar("Vigilancia de cámara desactivada.")
            else:
                _hablar_y_mostrar("No había ninguna vigilancia activa, Señor.")
            return
        
        raices_control = ["control", "manipul", "mueve", "mover"]
        palabras_detener_intent = ["deja de", "deten", "detente", "para de", "suelta", "quita el control"]

        if "esfera" in orden_limpia_sin_acentos and any(p in orden_limpia_sin_acentos for p in palabras_detener_intent):
            reproducir_sfx("modules", "Cam")
            if detener_control_esfera():
                _hablar_y_mostrar("Control de esfera desactivado.")
            else:
                _hablar_y_mostrar("No había ningún control de esfera activo, Señor.")
            return

        if "esfera" in orden_limpia_sin_acentos and any(r in orden_limpia_sin_acentos for r in raices_control):
            reproducir_sfx("modules", "Cam")
            if vigilancia_activa():
                _hablar_y_mostrar("No puedo activar el control por mano mientras la vigilancia esté usando la cámara, Señor. Desactívela primero.")
            elif iniciar_control_esfera():
                _hablar_y_mostrar(f"Control de esfera por mano activado, {titulo}.")
            else:
                _hablar_y_mostrar("El control de esfera ya estaba activo, Señor.")
            return
        # --- 6. MÓDULO REDES ---
        palabras_lista = orden_limpia_sin_acentos.split()
        es_consulta_velocidad = "velocidad" in orden_limpia_sin_acentos and any(p in orden_limpia_sin_acentos for p in ["red", "internet", "conexion"])
        es_consulta_latencia = "latencia" in orden_limpia_sin_acentos or ("ping" in palabras_lista and "terminal" not in orden_limpia_sin_acentos)
        es_ping_terminal = "ping" in palabras_lista and any(p in orden_limpia_sin_acentos for p in ["terminal", "cmd", "consola", "haz"])
        es_escaneo_puertos = any(p in orden_limpia_sin_acentos for p in ["escaneo de puertos", "escanear puertos", "puertos abiertos", "ver conexiones", "netstat"])
        es_consulta_intrusos = any(p in orden_limpia_sin_acentos for p in [
            "intruso", "intrusos", "quien esta conectado",
            "dispositivos conectados", "estoy seguro", "es segura mi red",
            "seguridad de mi red", "mi red es segura",
        ])
        es_marcar_conocidos = "marca" in orden_limpia_sin_acentos and ("conocido" in orden_limpia_sin_acentos or "conocidos" in orden_limpia_sin_acentos)
        es_consulta_red = (
            not (es_consulta_velocidad or es_consulta_latencia or es_consulta_intrusos or es_marcar_conocidos or es_escaneo_puertos or es_ping_terminal)
            and ("red" in palabras_lista or "ip" in palabras_lista or
                 any(p in orden_limpia_sin_acentos for p in ["internet", "conexion"]))
        )

        if es_consulta_velocidad:
            reproducir_sfx("modules", "redes")
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            hablar_en_hilo_seguro("Un momento, Señor, estoy abriendo el navegador y probando la velocidad de su conexión...")
            resultado_red = probar_velocidad_con_navegador()
            _hablar_y_mostrar(resultado_red)
            return

        if es_consulta_latencia:
            reproducir_sfx("modules", "redes")
            _hablar_y_mostrar(reportar_latencia())
            return

        if es_ping_terminal:
            reproducir_sfx("modules", "redes")
            partes_ping = orden_limpia.split("ping")
            target = partes_ping[-1].replace("a", "").strip() if len(partes_ping) > 1 and partes_ping[-1].strip() else "8.8.8.8"
            _hablar_y_mostrar(abrir_terminal_ping(target))
            return

        if es_escaneo_puertos:
            reproducir_sfx("modules", "redes")
            _hablar_y_mostrar(abrir_terminal_scan())
            return

        if es_marcar_conocidos:
            reproducir_sfx("modules", "redes")
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            hablar_en_hilo_seguro("Un momento, Señor, estoy escaneando su red...")
            resultado_marcado = marcar_todos_como_conocidos()
            _hablar_y_mostrar(resultado_marcado)
            return

        if es_consulta_intrusos:
            reproducir_sfx("modules", "redes")
            sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
            hablar_en_hilo_seguro("Un momento, Señor, estoy escaneando su red en busca de dispositivos intrusos...")
            resultado_intrusos = detectar_intrusos(abrir_terminal=True)
            _hablar_y_mostrar(resultado_intrusos)
            return

        if es_consulta_red:
            reproducir_sfx("modules", "redes")
            _hablar_y_mostrar(analizar_red())
            return

        sincronizar_estado_esfera("PROCESANDO", "#ffaa00")

        if any(w in orden_limpia_sin_acentos for w in ["camara", "que ves"]):
            reproducir_sfx("modules", "Cam")
            orden_limpia = "enciende la camara y dime que ves"

        es_orden_tecnica = es_intencion_de_comando(orden_limpia)
        respuesta_final = None

        if es_orden_tecnica:
            print("[Enrutador]: Procesando comando con Orquestador / NimClient...")
            try:
                respuesta_final = ejecutar_misión_compleja(orden_limpia, cerebro_ia)
            except Exception as err_mision:
                print(f"[Orquestador Error]: {err_mision}")

            if not respuesta_final or not respuesta_final.strip():
                try:
                    respuesta_final = cerebro_ia.generar_respuesta(orden_limpia)
                except Exception as err_nim:
                    print(f"[NimClient Error]: {err_nim}")
        else:
            print("[Enrutador]: Intención -> CONVERSACIÓN FLUIDA")
            if gemini_ia:
                try:
                    res_gemini = gemini_ia.generar_respuesta(orden_limpia)
                    if res_gemini and "percance" not in res_gemini.lower() and "429" not in res_gemini:
                        respuesta_final = res_gemini
                except Exception as err_gemini:
                    print(f"[Gemini Error / Quota Exhausted]: {err_gemini}")

            if not respuesta_final or not respuesta_final.strip():
                print("[Enrutador]: Gemini no disponible. Derivando a Cerebro NVIDIA NIM...")
                try:
                    respuesta_final = cerebro_ia.generar_respuesta(orden_limpia)
                except Exception as err_nim:
                    print(f"[NimClient Error]: {err_nim}")

        if not respuesta_final or not respuesta_final.strip():
            respuesta_final = f"Sistemas de lenguaje momentáneamente saturados, {titulo}. Por favor reintente en unos segundos."

        _hablar_y_mostrar(respuesta_final)

    except Exception as e:
        print(f"Error al ejecutar la orden: {e}")
        sincronizar_estado_esfera("ESPERA", "#0077ff")

def main():
    global oidos_ia, sistema_activo, titulo
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

    encender_sistemas()
    try:
        while sistema_activo:
            time.sleep(1)
    except KeyboardInterrupt:
        apagar_sistema()

if __name__ == "__main__":
    main()