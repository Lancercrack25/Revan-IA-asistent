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

    time.sleep(0.4) # Retraso estratégico para la organización de ventanas en Windows

    gui.actualizar_estado("⚙️ CONECTANDO COGNICIÓN...", "#7ef1ff")
    sincronizar_estado_esfera("CONECTANDO", "#7ef1ff")
    print("💻 [2/3] Panel CustomTkinter Activo.")
    
    try:
        # 🎯 Inicialización del Cerebro Local Ollama optimizado para tu GTX 1060
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

        # Saludo inicial sonoro de REVAN con el estado cromático correcto
        sincronizar_estado_esfera("HABLANDO", "#ff0055")
        voz_ia.hablar(f"Sistemas en línea. Herramientas del sistema desplegadas localmente, {titulo}.")
        sincronizar_estado_esfera("ESPERA", "#0077ff")
        
        # Enlazamos el bucle repetitivo de procesamiento de voz
        gui.app.after(100, procesar_ciclo_voz)
        
    except Exception as e:
        gui.actualizar_estado("⚠️ ERROR EN COGNICIÓN", "#f85149")
        sincronizar_estado_esfera("ERROR", "#f85149")
        print(f"❌ Error crítico al inicializar las APIs locales: {e}")

def procesar_ciclo_voz():
    """Ciclo táctico en main.py que filtra el ruido ambiental mediante palabra clave."""
    global cerebro_ia, voz_ia, oidos_ia, gui
    try:
        print("🔵 [REVAN]: Escuchando...")
        sincronizar_estado_esfera("ESCUCHANDO", "#7ef1ff")
        orden_sucia = oidos_ia.escuchar()
        
        # Si el micrófono no captó nada (Silencio), reabrimos ciclo de inmediato
        if not orden_sucia:
            sincronizar_estado_esfera("ESPERA", "#0077ff")
            gui.app.after(100, procesar_ciclo_voz)
            return

        orden_minusculas = orden_sucia.lower().strip()
        print(f"🧠 [Matriz de captura]: '{orden_minusculas}'")

        # 🎯 EL FILTRO ANTIRRUIDO CRÍTICO:
        if not orden_minusculas.startswith("revan"):
            print("🔊 [REVAN]: Interferencia o comando sin palabra clave detectado. Ignorando...")
            sincronizar_estado_esfera("ESPERA", "#0077ff")
            gui.app.after(100, procesar_ciclo_voz)
            return

        # Si llegó aquí, sí te dirigiste a la IA. Limpiamos el prefijo "revan"
        orden_limpia = orden_minusculas.replace("revan", "").strip()
        
        # Caso por si solo dijiste su nombre sin orden
        if not orden_limpia:
            sincronizar_estado_esfera("HABLANDO", "#ff0055")
            voz_ia.hablar("Sistemas listos, Señor. ¿Qué comando desea ejecutar?")
            sincronizar_estado_esfera("ESPERA", "#0077ff")
            gui.app.after(100, procesar_ciclo_voz)
            return

        # 3. Enviamos la orden limpia al cerebro de Ollama parchado (Corregido: cerebro_ia)
        sincronizar_estado_esfera("PROCESANDO", "#ffaa00")
        respuesta_final = cerebro_ia.generar_respuesta(orden_limpia)
        
        # Actualizamos la interfaz gráfica con el texto real
        gui.agregar_mensaje("user", orden_sucia)
        gui.agregar_mensaje("revan", respuesta_final)
        
        # 4. Vocalización asíncrona mediante hilos (Corregido: voz_ia)
        sincronizar_estado_esfera("HABLANDO", "#ff0055")
        voz_ia.hablar(respuesta_final)
        sincronizar_estado_esfera("ESPERA", "#0077ff")

    except Exception as e:
        print(f"⚠️ Error detectado en el bucle táctico de voz: {e}")
        sincronizar_estado_esfera("ESPERA", "#0077ff")
    
    # Mantenemos el ciclo vivo en Tkinter de forma segura
    gui.app.after(100, procesar_ciclo_voz)

def main():
    global oidos_ia, gui, sistema_activo, titulo
    
    print("🌌 Inicializando cargador base de REVAN...")
    ajustes = cargar_ajustes()
    titulo = ajustes.get("USER_NAME", "Señor") if ajustes else "Señor"
    
    # Lanzamos el backend de red en segundo plano inmediatamente
    t_web = threading.Thread(target=hilo_servidor_web, daemon=True)
    t_web.start()

    oidos_ia = MicrophoneClient()
    
    print(" REVAN en modo pasivo. Esperando señal acústica (aplauso)...")
    while True:
        try:
            captura = oidos_ia.escuchar()
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