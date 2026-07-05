import os
import sys
import time
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

from src.Core.Gemini_client import GeminiClient
from src.Core.Elevenlabs_client import ElevenLabsClient
from src.Core.microphone_client import MicrophoneClient
from src.Core.Config_loader import cargar_ajustes
from src.Gui.Dashboard import RevanGUI
from src.Automation.System_commands import desplegar_monitores_windows

# Componentes globales
cerebro_ia = None
voz_ia = None
oidos_ia = None
gui = None
titulo = "Maestro"
sistema_activo = False

def encender_sistemas():
    """Ejecuta la modularización táctica al recibir el aplauso."""
    global cerebro_ia, voz_ia, oidos_ia, gui, titulo, sistema_activo
    sistema_activo = True

    print("⚡ Inicializando secuencia de despliegue...")
    
    # 1. Se abren las ventanas nativas de Windows (Administrador de tareas, Monitor, etc.)
    try:
        desplegar_monitores_windows()
    except Exception as e:
        print(f"⚠️ Aviso al desplegar monitores nativos: {e}")

    # 2. Conectamos los motores cognitivos e inteligencias sin romper el ciclo gráfico
    gui.actualizar_estado("⚙️ CONECTANDO COGNICIÓN...", "#7ef1ff")
    
    try:
        cerebro_ia = GeminiClient()
        voz_ia = ElevenLabsClient()

        # 3. Activación completa en la interfaz
        gui.actualizar_estado("⚡ EN LÍNEA", "#7ef1ff")
        gui.agregar_mensaje("revan", f"Protocolo de aplausos validado. Módulos de automatización e interfaces cargadas. Estoy listo, {titulo}.")
        
        # El asistente habla para confirmar la carga
        voz_ia.hablar(f"Sistemas en línea. Herramientas del sistema desplegadas, {titulo}.")
        
        # Lanzamos el bucle continuo de escucha de voz
        gui.app.after(100, procesar_ciclo_voz)
        
    except Exception as e:
        gui.actualizar_estado("⚠️ ERROR EN COGNICIÓN", "#f85149")
        print(f"❌ Error crítico al inicializar las APIs (Gemini/ElevenLabs): {e}")

def procesar_ciclo_voz():
    global cerebro_ia, voz_ia, oidos_ia, gui, titulo

    if gui.debe_cerrar:
        gui.actualizar_estado("Desconectando...", "#f85149")
        if voz_ia:
            voz_ia.hablar(f"Entendido, {titulo}. Desconectando sistemas tácticos.")
        gui.app.quit()
        return

    try:
        gui.actualizar_estado("ESCUCHANDO...", "#58a6ff")
        orden = oidos_ia.escuchar()
        
        if orden.strip():
            gui.agregar_mensaje("tu", orden)
            
            # Comandos de apagado rápido
            if any(palabra in orden.lower() for palabra in ["salir", "apagar sistema", "desconectar", "adiós", "apágate"]):
                gui.actualizar_estado("Desconectando...", "#f85149")
                if voz_ia:
                    voz_ia.hablar(f"Entendido, {titulo}. Desconectando sistemas tácticos.")
                gui.app.quit()
                return

            gui.actualizar_estado("🧠 PENSANDO...", "#7ef1ff")
            respuesta_texto = cerebro_ia.generar_respuesta(orden)
            
            gui.agregar_mensaje("revan", respuesta_texto)
            gui.actualizar_estado("🔊 REVAN HABLANDO...", "#00f0ff")
            voz_ia.hablar(respuesta_texto)
            gui.actualizar_estado("⚡ EN LÍNEA", "#7ef1ff")

    except Exception as e:
        gui.actualizar_estado("⚠️ ERROR EN SISTEMA", "#f85149")
        print(f"Ocurrió un error en el ciclo de voz: {e}")

    gui.app.after(100, procesar_ciclo_voz)

def main():
    global oidos_ia, gui, sistema_activo
    
    print("🌌 Inicializando cargador base de REVAN...")
    ajustes = cargar_ajustes()
    titulo = ajustes.get("USER_NAME", "Maestro") if ajustes else "Maestro"
    # 1. Encendemos el hardware de escucha básica
    oidos_ia = MicrophoneClient()
    # 2. BUCLE PASIVO: Retención en consola vigilando el aplauso
    print(" REVAN en modo pasivo. Esperando señal acústica (aplauso)...")
    
    while True:
        try:
            captura = oidos_ia.escuchar(modo_pasivo=True)
            if captura.strip():
                print(f"💥 ¡Señal acústica validada! Inicializando REVAN...")
                break # Rompe la retención y pasa al despliegue
                
        except Exception as e:
            print(f"Aviso en escaneo pasivo: {e}")
            
        time.sleep(0.1)

    # 3. EL DESPERTAR: Se ejecuta tras validar el impacto acústico
    print("⚡ Desplegando interfaces tácticas...")
    # Instanciamos la ventana principal
    gui = RevanGUI(titulo_usuario=titulo)
    # Intentamos forzar la visibilidad del panel resolviendo fallas de nombres
    try:
        gui.mostrar_panel()
    except AttributeError:
        if hasattr(gui, 'app'):
            gui.app.deiconify() # Método nativo de Tkinter para restaurar ventanas ocultas
    # Guardamos 250 milisegundos para que Windows pinte la GUI antes de correr los subprocesos pesados
    gui.app.after(250, encender_sistemas)
    # Encendemos el motor visual de Tkinter (mantiene la app viva en pantalla)
    gui.app.mainloop()

if __name__ == "__main__":
    main()