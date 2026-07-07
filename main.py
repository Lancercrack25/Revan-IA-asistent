import os
import sys
import time
import threading
import subprocess

# Prevenir la generación de archivos de caché compilados (.pyc)
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

# 🔌 Importaciones del Sistema REVAN (Cerebro Localizado)
from src.Core.Ollama_client import OllamaClient  
from src.Core.Elevenlabs_client import ElevenLabsClient
from src.Core.microphone_client import MicrophoneClient
from src.Core.Config_loader import cargar_ajustes
from src.Gui.Dashboard import RevanGUI
from src.Automation.System_commands import desplegar_monitores_windows
# Conexión directa al puente real del servidor
from src.Interfaces.servidor import iniciar_servidor_ui, transmitir_desde_hilo_externo

# Instancias y Controles Globales
cerebro_ia = None
voz_ia = None
oidos_ia = None
gui = None
titulo = "Señor"
sistema_activo = False

# 🧠 VARIABLES DE CONTROL DE ATENCIÓN (MODO JARVIS CHETADO)
ultima_interaccion = 0  # Almacena el timestamp de la última orden procesada
TIEMPO_ATENCION = 30    # Tiempo en segundos para mantener el canal abierto sin pedir el nombre

def hilo_servidor_web():
    """Ejecuta el servidor FastAPI/Uvicorn para la esfera 3D en un hilo dedicado."""
    try:
        servidor = iniciar_servidor_ui()
        servidor.run()
    except Exception as e:
        print(f"⚠️ Error al inicializar el servidor web de la esfera: {e}")

def sincronizar_estado_esfera(estado, color_hex):
    """Envía de forma segura los estados de voz e IA al loop en ejecución de FastAPI."""
    transmitir_desde_hilo_externo(estado, color_hex)

def encender_sistemas():
    """Ejecuta la secuencia de despliegue cronológico (Monitores -> CustomTkinter -> Esfera)."""
    global cerebro_ia, voz_ia, oidos_ia, gui, titulo, sistema_activo
    sistema_activo = True

    print("⚡ Inicializando secuencia de despliegue cronológico...")
    print("🪟 [1/3] Desplegando herramientas del sistema (Monitores nativos)...")
    try:
        desplegar_monitores_windows()
    except Exception as e:
        print(f"⚠️ Aviso al desplegar monitores nativos: {e}")

    time.sleep(0.4) 

    gui.actualizar_estado("⚙️ CONECTANDO COGNICIÓN...", "#7ef1ff")
    sincronizar_estado_esfera("CONECTANDO", "#7ef1ff")
    print("💻 [2/3] Panel CustomTkinter Activo.")
    
    try:
        # Inicialización de motores locales
        cerebro_ia = OllamaClient()
        voz_ia = ElevenLabsClient()

        gui.actualizar_estado("⚡ EN LÍNEA", "#7ef1ff")
        gui.agregar_mensaje("revan", f"Protocolo de aplausos validado. Módulos de automatización e interfaces cargadas de forma local. Estoy listo, {titulo}.")
        
        time.sleep(0.2)

        try:
            subprocess.Popen(
                'start brave --app=http://127.0.0.1:8000 --window-size=670,670',
                shell=True
            )
            print("🌐 [3/3] Núcleo Web Desplegado (Esfera 3D).")
        except Exception as e:
            print(f"⚠️ Error al lanzar la interfaz web: {e}")

        sincronizar_estado_esfera("HABLANDO", "#ff0055")
        voz_ia.hablar(f"Sistemas en línea. Herramientas del sistema desplegadas localmente, {titulo}.")
        sincronizar_estado_esfera("ESPERA", "#0077ff")
        
        gui.app.after(100, procesar_ciclo_voz)
        
    except Exception as e:
        gui.actualizar_estado("⚠️ ERROR EN COGNICIÓN", "#f85149")
        sincronizar_estado_esfera("ERROR", "#f85149")
        print(f"❌ Error crítico al inicializar las APIs locales: {e}")

def procesar_ciclo_voz():
    """Ciclo avanzado estilo Jarvis con ventana de atención de tiempo dinámico."""
    global cerebro_ia, voz_ia, oidos_ia, gui, ultima_interaccion
    try:
        print("🔵 [REVAN]: Escuchando...")
        sincronizar_estado_esfera("ESCUCHANDO", "#7ef1ff")
        orden_sucia = oidos_ia.escuchar()
        
        if not orden_sucia:
            sincronizar_estado_esfera("ESPERA", "#0077ff")
            gui.app.after(100, procesar_ciclo_voz)
            return

        orden_minusculas = orden_sucia.lower().strip()
        print(f"🧠 [Matriz de captura]: '{orden_minusculas}'")

        # Evaluar si estamos dentro de la ventana de tiempo activa tras una petición válida
        tiempo_actual = time.time()
        en_ventana_atencion = (tiempo_actual - ultima_interaccion) < TIEMPO_ATENCION

        # 🎯 ENRUTADOR CONTEXTUAL JARVIS:
        if "revan" in orden_minusculas:
            # Si se le llama por su nombre, limpia la cadena y abre/renueva el contador de atención
            partes = orden_minusculas.split("revan", 1)
            orden_limpia = partes[1].strip() if len(partes) > 1 else ""
            ultima_interaccion = tiempo_actual  
        elif en_ventana_atencion:
            # Modo Conversación Fluida Activo: procesa la orden directa omitiendo el nombre
            print("🔥 [MODO JARVIS]: Canal abierto. Procesando orden directa...")
            orden_limpia = orden_minusculas
            ultima_interaccion = tiempo_actual  # Cada interacción exitosa resetea los 30 segundos
        else:
            # Fuera de la ventana y sin invocación explícita, se filtra como ruido de fondo
            print("🔊 [REVAN]: Ruido ambiental o conversación ajena detectada. Ignorando...")
            sincronizar_estado_esfera("ESPERA", "#0077ff")
            gui.app.after(100, procesar_ciclo_voz)
            return

        # Si se invoca el nombre de la IA pero no hay comando posterior
        if not orden_limpia:
            sincronizar_estado_esfera("HABLANDO", "#ff0055")
            voz_ia.hablar("Sistemas listos, Señor. ¿Qué comando desea ejecutar?")
            sincronizar_estado_esfera("ESPERA", "#0077ff")
            gui.app.after(100, procesar_ciclo_voz)
            return

        # Procesamiento táctico con Ollama
        sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
        respuesta_final = cerebro_ia.generar_respuesta(orden_limpia)
        
        # Sincronización con la interfaz gráfica
        gui.agregar_mensaje("user", orden_sucia)
        gui.agregar_mensaje("revan", respuesta_final)
        
        # Vocalización limpia
        sincronizar_estado_esfera("HABLANDO", "#ff0055")
        voz_ia.hablar(respuesta_final)
        sincronizar_estado_esfera("ESPERA", "#0077ff")

    except Exception as e:
        print(f"⚠️ Error detectado en el bucle táctico de voz: {e}")
        sincronizar_estado_esfera("ESPERA", "#0077ff")
    
    gui.app.after(100, procesar_ciclo_voz)

def main():
    global oidos_ia, gui, sistema_activo, titulo
    
    print("🌌 Inicializando cargador base de REVAN...")
    ajustes = cargar_ajustes()
    titulo = ajustes.get("USER_NAME", "Señor") if ajustes else "Señor"
    
    t_web = threading.Thread(target=hilo_servidor_web, daemon=True)
    t_web.start()

    oidos_ia = MicrophoneClient()
    
    print(" REVAN en modo pasivo. Esperando señal acústica (aplauso)...")
    while True:
        try:
            # 🎯 PARÁMETRO CORREGIDO: Se reincorpora el control nativo para el pico del aplauso
            captura = oidos_ia.escuchar(modo_pasivo=True)
            if captura.strip():
                print(f"💥 ¡Señal acústica validada! Inicializando REVAN...")
                break
        except Exception as e:
            print(f"Aviso en escaneo pasivo: {e}")
        time.sleep(0.1)

    print("⚡ Desplegando interfaces tácticas...")
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