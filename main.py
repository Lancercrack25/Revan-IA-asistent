import os
import sys
import time
import threading
import subprocess

# Prevenir la generación de archivos de caché compilados (.pyc)
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

# Importaciones del Sistema REVAN
from src.Core.Gemini_client import GeminiClient
from src.Core.Elevenlabs_client import ElevenLabsClient
from src.Core.microphone_client import MicrophoneClient
from src.Core.Config_loader import cargar_ajustes
from src.Gui.Dashboard import RevanGUI
from src.Automation.System_commands import desplegar_monitores_windows
# 🎯 Conexión directa al puente real del servidor
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
        # Inicialización de Clientes API externos
        cerebro_ia = GeminiClient()
        voz_ia = ElevenLabsClient()

        gui.actualizar_estado("⚡ EN LÍNEA", "#7ef1ff")
        gui.agregar_mensaje("revan", f"Protocolo de aplausos validado. Módulos de automatización e interfaces cargadas. Estoy listo, {titulo}.")
        
        time.sleep(0.2)

        try:
            subprocess.Popen(
                'start brave --app=http://127.0.0.1:8000 --window-size=450,450',
                shell=True
            )
            print("🌐 [3/3] Núcleo Web Desplegado (Esfera 3D).")
        except Exception as e:
            print(f"⚠️ Error al lanzar la interfaz web: {e}")

        # Saludo inicial sonoro de REVAN con el estado cromático correcto
        sincronizar_estado_esfera("HABLANDO", "#ff0055")
        voz_ia.hablar(f"Sistemas en línea. Herramientas del sistema desplegadas, {titulo}.")
        sincronizar_estado_esfera("ESPERA", "#0077ff")
        
        # Enlazamos el bucle repetitivo de procesamiento de voz
        gui.app.after(100, procesar_ciclo_voz)
        
    except Exception as e:
        gui.actualizar_estado("⚠️ ERROR EN COGNICIÓN", "#f85149")
        sincronizar_estado_esfera("ERROR", "#f85149")
        print(f"❌ Error crítico al inicializar las APIs: {e}")

def procesar_ciclo_voz():
    """Administra los cambios de estado cromáticos basados en la actividad de voz."""
    global cerebro_ia, voz_ia, oidos_ia, gui, titulo

    if gui.debe_cerrar:
        gui.actualizar_estado("Desconectando...", "#f85149")
        sincronizar_estado_esfera("DESCONECTANDO", "#f85149")
        if voz_ia:
            voz_ia.hablar(f"Entendido, {titulo}. Desconectando sistemas tácticos.")
        gui.app.quit()
        return

    try:
        # 🎤 ESCUCHANDO: El usuario habla (Esfera pasa a Cian)
        gui.actualizar_estado("ESCUCHANDO...", "#58a6ff")
        sincronizar_estado_esfera("ESCUCHANDO", "#00ffcc")
        
        orden = oidos_ia.escuchar()
        
        if orden.strip():
            gui.agregar_mensaje("tu", orden)
            
            # Comando de apagado inmediato
            if any(palabra in orden.lower() for palabra in ["salir", "apagar sistema", "desconectar", "adiós", "apágate"]):
                gui.actualizar_estado("Desconectando...", "#f85149")
                sincronizar_estado_esfera("DESCONECTANDO", "#f85149")
                if voz_ia:
                    voz_ia.hablar(f"Entendido, {titulo}. Desconectando sistemas tácticos.")
                gui.app.quit()
                return

            # 🧠 PENSANDO: Gemini procesa la orden (Esfera pasa a Dorado)
            gui.actualizar_estado("🧠 PENSANDO...", "#ffaa00")
            sincronizar_estado_esfera("PENSANDO", "#ffaa00")
            
            respuesta_texto = cerebro_ia.generar_respuesta(orden)
            
            # 🔊 HABLANDO: ElevenLabs reproduce el audio (Esfera pasa a Fucsia)
            gui.agregar_mensaje("revan", respuesta_texto)
            gui.actualizar_estado("🔊 REVAN HABLANDO...", "#ff0055")
            sincronizar_estado_esfera("HABLANDO", "#ff0055")
            
            voz_ia.hablar(respuesta_texto)
            
            # ⚡ RETORNO: El sistema vuelve a reposo (Esfera pasa a Azul)
            gui.actualizar_estado("⚡ EN LÍNEA", "#7ef1ff")
            sincronizar_estado_esfera("ESPERA", "#0077ff")

    except Exception as e:
        gui.actualizar_estado("⚠️ ERROR EN SISTEMA", "#f85149")
        sincronizar_estado_esfera("ERROR", "#f85149")
        print(f"Ocurrió un error en el ciclo de voz: {e}")

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