import os
import sys
import time
import threading
import asyncio
import subprocess

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

from src.Core.Gemini_client import GeminiClient
from src.Core.Elevenlabs_client import ElevenLabsClient
from src.Core.microphone_client import MicrophoneClient
from src.Core.Config_loader import cargar_ajustes
from src.Gui.Dashboard import RevanGUI
from src.Automation.System_commands import desplegar_monitores_windows

# Importamos el inicializador del servidor de la esfera 3D
from src.Interfaces.servidor import iniciar_servidor_ui

# Componentes globales
cerebro_ia = None
voz_ia = None
oidos_ia = None
gui = None
titulo = "Maestro"
sistema_activo = False

# Bucle de eventos asíncronos global para WebSockets
loop_asincrono_global = None

def hilo_servidor_web():
    """Ejecuta el servidor FastAPI/Uvicorn para la esfera 3D en un canal independiente."""
    try:
        servidor = iniciar_servidor_ui()
        servidor.run()
    except Exception as e:
        print(f"⚠️ Error al inicializar el servidor web de la esfera: {e}")

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

    # 2. DESPLIEGUE DEL WIDGET FLOTANTE EN BRAVE (Optimizado para tu navegador por defecto)
    try:
        # Estrategia 1: Intentar arrancar Brave directamente usando el CMD
        subprocess.Popen(
            'start brave --app=http://127.0.0.1:8000/static/index.html --window-size=450,450',
            shell=True
        )
    except Exception:
        try:
            # Estrategia 2: Si falla el comando directo, buscamos la ruta típica de Brave en Windows
            ruta_brave = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
            if os.path.exists(ruta_brave):
                subprocess.Popen([
                    ruta_brave, 
                    "--app=http://127.0.0.1:8000/static/index.html", 
                    "--window-size=450,450"
                ])
            else:
                # Estrategia 3: Respaldo de emergencia en el navegador predeterminado del sistema
                import webbrowser
                webbrowser.open("http://127.0.0.1:8000/static/index.html")
        except Exception as e:
            print(f"⚠️ No se pudo inicializar la interfaz flotante: {e}")

    # 3. Conectamos los motores cognitivos e inteligencias sin romper el ciclo gráfico
    gui.actualizar_estado("⚙️ CONECTANDO COGNICIÓN...", "#7ef1ff")
    
    try:
        cerebro_ia = GeminiClient()
        voz_ia = ElevenLabsClient()

        # 4. Activación completa en ambas interfaces simultáneamente
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

            gui.actualizar_estado("🧠 PENSANDO...", "#ffaa00") # Cambia a dorado en consola y esfera web de Brave
            respuesta_texto = cerebro_ia.generar_respuesta(orden)
            
            gui.agregar_mensaje("revan", respuesta_texto)
            gui.actualizar_estado("🔊 REVAN HABLANDO...", "#ff0055") # Cambia a fucsia/rojo latido en ambas pantallas
            voz_ia.hablar(respuesta_texto)
            gui.actualizar_estado("⚡ EN LÍNEA", "#7ef1ff")

    except Exception as e:
        gui.actualizar_estado("⚠️ ERROR EN SISTEMA", "#f85149")
        print(f"Ocurrió un error en el ciclo de voz: {e}")

    gui.app.after(100, procesar_ciclo_voz)

def main():
    global oidos_ia, gui, sistema_activo, loop_asincrono_global, titulo
    
    print("🌌 Inicializando cargador base de REVAN...")
    ajustes = cargar_ajustes()
    titulo = ajustes.get("USER_NAME", "Maestro") if ajustes else "Maestro"
    
    # 1. Inicializamos el bucle asíncrono para FastAPI antes de disparar hilos gráficos
    loop_asincrono_global = asyncio.new_event_loop()
    asyncio.set_event_loop(loop_asincrono_global)

    # 2. Lanzamos el servidor de la Esfera Web 3D en segundo plano
    t_web = threading.Thread(target=hilo_servidor_web, daemon=True)
    t_web.start()

    # 3. Encendemos el hardware de escucha básica
    oidos_ia = MicrophoneClient()
    
    # 4. BUCLE PASIVO: Retención en consola vigilando el aplauso
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

    # 5. EL DESPERTAR: Se ejecuta tras validar el impacto acústico del aplauso
    print("⚡ Desplegando interfaces tácticas...")
    
    # Instanciamos la ventana principal de CustomTkinter
    gui = RevanGUI(titulo_usuario=titulo)
    
    # Inyectamos el bucle asíncrono que creamos para que el Dashboard pueda transmitir comandos de red a Brave
    gui.loop_ui = loop_asincrono_global

    # Forzar la visibilidad del panel resolviendo fallas de nombres nativos de Tkinter
    try:
        gui.mostrar_panel()
    except AttributeError:
        if hasattr(gui, 'app'):
            gui.app.deiconify()
            
    # Concedemos 250 milisegundos para que Windows termine de pintar la interfaz antes del subproceso pesado
    gui.app.after(250, encender_sistemas)
    
    # Encendemos el motor visual en el hilo principal (mantiene la app viva en pantalla)
    gui.app.mainloop()

if __name__ == "__main__":
    main()