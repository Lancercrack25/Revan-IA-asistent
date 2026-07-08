import os
import sys
import time
import threading
import subprocess

# Prevenir la generación de archivos de caché compilados (.pyc)
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

# Importaciones del Sistema REVAN
from src.Core.Ollama_client import OllamaClient  
from src.Core.Elevenlabs_client import ElevenLabsClient
from src.Core.microphone_client import MicrophoneClient
from src.Core.Config_loader import cargar_ajustes
from src.Gui.Dashboard import RevanGUI
from src.Automation.System_commands import desplegar_monitores_windows
from src.Interfaces.servidor import iniciar_servidor_ui, transmitir_desde_hilo_externo
from src.Database.init import inicializar_base_datos
from src.Services.agent_orchestrator import ejecutar_misión_compleja

# Instancias y Controles Globales
cerebro_ia = None
voz_ia = None
oidos_ia = None
gui = None
titulo = "Señor"
sistema_activo = False
ultima_interaccion = 0  
TIEMPO_ATENCION = 21    # Ventana de atención activa en segundos

def hilo_servidor_web():
    """Ejecuta el servidor FastAPI/Uvicorn para la esfera 3D en un hilo dedicado."""
    try:
        servidor = iniciar_servidor_ui()
        servidor.run()
    except Exception as e:
        print(f"❌ Error en el servidor web de la esfera: {e}")

def sincronizar_estado_esfera(estado, color_hex):
    """Envía los estados de voz e IA al loop de la esfera 3D vía WebSocket."""
    try:
        transmitir_desde_hilo_externo(estado, color_hex)
    except Exception as e:
        print(f"⚠️ Error al sincronizar esfera: {e}")

def encender_sistemas():
    """Secuencia de despliegue cronológico (Monitores -> CustomTkinter -> Esfera -> Hilo de Voz)."""
    global cerebro_ia, voz_ia, oidos_ia, gui, titulo, sistema_activo
    sistema_activo = True

    print("🚀 Inicializando secuencia de despliegue cronológico...")
    print("🪟 [1/3] Desplegando monitores nativos...")
    try:
        desplegar_monitores_windows()
    except Exception as e:
        print(f" Aviso al desplegar monitores nativos: {e}")

    time.sleep(0.4) 

    gui.actualizar_estado("CONECTANDO COGNICIÓN...", "#7ef1ff")
    sincronizar_estado_esfera("CONECTANDO", "#7ef1ff")
    print("🖥️ [2/3] Panel CustomTkinter Activo.")
    
    try:
        # Inicialización de motores locales
        cerebro_ia = OllamaClient()
        voz_ia = ElevenLabsClient()

        gui.actualizar_estado("EN LÍNEA", "#7ef1ff")
        gui.agregar_mensaje("revan", f"Sistemas en línea, {titulo}. Listo para recibir instrucciones.")
        
        time.sleep(0.2)

        try:
            subprocess.Popen(
                'start brave --app=http://127.0.0.1:8000 --window-size=670,670',
                shell=True
            )
            print("🌐 [3/3] Núcleo Web Desplegado (Esfera 3D).")
        except Exception as e:
            print(f"Error al lanzar la interfaz web: {e}")

        sincronizar_estado_esfera("HABLANDO", "#ff0055")
        voz_ia.hablar(f"Sistemas en línea. Herramientas desplegadas exitosamente, {titulo}.")
        sincronizar_estado_esfera("ESPERA", "#0077ff")
        
        # 🎯 SOLUCIÓN CRÍTICA: La escucha corre en un HILO SECUNDARIO para no congelar la GUI/Esfera
        hilo_voz = threading.Thread(target=bucle_escucha_hilo, daemon=True)
        hilo_voz.start()
        
    except Exception as e:
        gui.actualizar_estado("⚠️ ERROR EN COGNICIÓN", "#f85149")
        sincronizar_estado_esfera("ERROR", "#f85149")
        print(f"❌ Error crítico al inicializar las APIs locales: {e}")

def bucle_escucha_hilo():
    """Bucle infinito de escucha ejecutado exclusivamente fuera del hilo principal de la GUI."""
    global sistema_activo
    while sistema_activo:
        procesar_ciclo_voz()
        time.sleep(0.05)

def procesar_ciclo_voz():
    """Ciclo táctico de voz con manejo preciso de estados de esfera y orquestador."""
    global cerebro_ia, voz_ia, oidos_ia, gui, ultima_interaccion
    try:
        print("\n[REVAN]: Escuchando...")
        sincronizar_estado_esfera("ESCUCHANDO", "#7ef1ff") # 🔵 AZUL CLARO
        
        orden_sucia = oidos_ia.escuchar()
        
        if not orden_sucia:
            sincronizar_estado_esfera("ESPERA", "#0077ff") # 🔵 AZUL OSCURO
            return

        orden_minusculas = orden_sucia.lower().strip()
        print(f"[Captura]: '{orden_minusculas}'")

        tiempo_actual = time.time()
        en_ventana_atencion = (tiempo_actual - ultima_interaccion) < TIEMPO_ATENCION

        # Filtrado inteligente de comandos e invocación
        if "revan" in orden_minusculas:
            partes = orden_minusculas.split("revan", 1)
            orden_limpia = partes[1].strip() if len(partes) > 1 else ""
            ultima_interaccion = tiempo_actual  
        elif en_ventana_atencion:
            print("[MODO JARVIS]: Canal abierto. Procesando orden directa...")
            orden_limpia = orden_minusculas
            ultima_interaccion = tiempo_actual  
        else:
            print("[REVAN]: Ruido ambiental ignorado.")
            sincronizar_estado_esfera("ESPERA", "#0077ff")
            return

        if not orden_limpia:
            sincronizar_estado_esfera("HABLANDO", "#ff0055") # 🔴 ROJO
            voz_ia.hablar("Sistemas listos, Señor. ¿Qué comando desea ejecutar?")
            sincronizar_estado_esfera("ESPERA", "#0077ff")
            return

        # --- INTERCEPTOR DE PROCESAMIENTO ---
        sincronizar_estado_esfera("PROCESANDO", "#ffaa00") # 🟡 AMARILLO

        # Intercepción rápida para cámara (evita que el orquestador busque carpetas inventadas)
        if any(w in orden_limpia for w in ["camara", "cámara", "enciende la camara", "enciende la cámara", "que ves", "qué ves"]):
            orden_limpia = "enciende la camara y dime que ves"

        # Evaluar la misión en el orquestador
        respuesta_final = ejecutar_misión_compleja(orden_limpia, cerebro_ia)
        
        # Si el orquestador no la capturó, pasa a Ollama directamente
        if respuesta_final is None:
            respuesta_final = cerebro_ia.generar_respuesta(orden_limpia)

        # Actualización segura de Tkinter (Thread-safe)
        if gui and hasattr(gui, 'app'):
            gui.app.after(0, lambda user_text=orden_sucia: gui.agregar_mensaje("user", user_text))
            gui.app.after(0, lambda bot_text=respuesta_final: gui.agregar_mensaje("revan", bot_text))

        # Vocalización y cambio de estado a hablando
        sincronizar_estado_esfera("HABLANDO", "#ff0055") # 🔴 ROJO
        voz_ia.hablar(respuesta_final)
        sincronizar_estado_esfera("ESPERA", "#0077ff") # 🔵 AZUL OSCURO

    except Exception as e:
        print(f"❌ Error en el bucle táctico de voz: {e}")
        sincronizar_estado_esfera("ESPERA", "#0077ff")

def main():
    global oidos_ia, gui, sistema_activo, titulo
    
    print("🚀 [REVAN]: Inicializando infraestructura base...")
    
    try:
        inicializar_base_datos()
    except Exception as e:
        print(f"⚠️ Alerta al desplegar base de datos: {e}")
        
    ajustes = cargar_ajustes()
    titulo = ajustes.get("USER_NAME", "Señor") if ajustes else "Señor"
    
    # Servidor web en hilo independiente
    t_web = threading.Thread(target=hilo_servidor_web, daemon=True)
    t_web.start()

    oidos_ia = MicrophoneClient()
    
    print("🎙️ REVAN en modo pasivo. Esperando señal acústica...")
    while True:
        try:
            captura = oidos_ia.escuchar(modo_pasivo=True)
            if captura and captura.strip():
                print(f"⚡ ¡Señal acústica validada! Inicializando REVAN...")
                break
        except Exception as e:
            print(f"Aviso en escaneo pasivo: {e}")
        time.sleep(0.1)

    print("🖥️ Desplegando interfaz gráfica...")
    gui = RevanGUI(titulo_usuario=titulo)

    try:
        gui.mostrar_panel()
    except AttributeError:
        if hasattr(gui, 'app'):
            gui.app.deiconify()
            
    # Arrancar secuencia
    gui.app.after(250, encender_sistemas)
    gui.app.mainloop()

if __name__ == "__main__":
    main()