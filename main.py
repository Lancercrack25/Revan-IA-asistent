import os
import sys

# 🛡️ 1. ESCUDO ABSOLUTO: Bloqueamos pycache
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

# 📦 2. IMPORTACIONES DE TU ARQUITECTURA MODULAR
from src.Core.Gemini_client import GeminiClient
from src.Core.Elevenlabs_client import ElevenLabsClient
from src.Core.microphone_client import MicrophoneClient
from src.Core.Config_loader import cargar_ajustes
from src.Gui.Dashboard import RevanGUI

# 🚀 NUEVA IMPORTACIÓN DE AUTOMATIZACIÓN
from src.Automation.System_commands import desplegar_monitores_windows

# Inicialización de componentes globales
cerebro_ia = None
voz_ia = None
oidos_ia = None
gui = None
titulo = "Maestro"
sistema_activo = False

def esperar_aplauso():
    global oidos_ia, gui, sistema_activo
    try:
        # Le indicamos al cliente que use el modo rápido para cazar el ruido seco
        captura = oidos_ia.escuchar(modo_pasivo=True)
        # Si devuelve texto o nuestro comodín "GOLPE_ACUSTICO", encendemos los sistemas
        if captura.strip():
            print(f"💥 ¡Señal acústica validada! Inicializando REVAN...")
            encender_sistemas()
            return
    except Exception as e:
        pass
    if not sistema_activo:
        gui.app.after(50, esperar_aplauso)

def encender_sistemas():
    """Ejecuta la modularización táctica al recibir el aplauso."""
    global cerebro_ia, voz_ia, oidos_ia, gui, titulo, sistema_activo
    sistema_activo = True

    print("⚡ Inicializando secuencia de despliegue...")
    
    # 🔥 LLAMADA MODULAR: Mandamos a ejecutar las ventanas nativas desde el otro archivo
    desplegar_monitores_windows()

    # Desplegar la interfaz de chat de REVAN
    gui.mostrar_panel()
    
    gui.actualizar_estado("⚙️ CONECTANDO COGNICIÓN...", "#7ef1ff")
    cerebro_ia = GeminiClient()
    voz_ia = ElevenLabsClient()

    gui.actualizar_estado("⚡ EN LÍNEA", "#7ef1ff")
    gui.agregar_mensaje("revan", f"Protocolo de aplausos validado. Módulos de automatización e interfaces cargadas. Estoy listo, {titulo}.")
    voz_ia.hablar(f"Sistemas en línea. Herramientas del sistema desplegadas, {titulo}.")
    
    gui.app.after(100, procesar_ciclo_voz)

def procesar_ciclo_voz():
    global cerebro_ia, voz_ia, oidos_ia, gui, titulo

    if gui.debe_cerrar:
        gui.actualizar_estado("Desconectando...", "#f85149")
        voz_ia.hablar(f"Entendido, {titulo}. Desconectando sistemas tácticos.")
        gui.app.quit()
        return

    try:
        gui.actualizar_estado("🎤 ESCUCHANDO...", "#58a6ff")
        orden = oidos_ia.escuchar()
        
        if orden.strip():
            gui.agregar_mensaje("tu", orden)
            
            if any(palabra in orden.lower() for palabra in ["salir", "apagar sistema", "desconectar", "adiós", "apágate"]):
                gui.actualizar_estado("Desconectando...", "#f85149")
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
        print(f"❌ Ocurrió un error en el ciclo de voz: {e}")

    gui.app.after(100, procesar_ciclo_voz)

def main():
    global oidos_ia, gui, titulo
    
    print("🌌 Inicializando cargador base de REVAN...")
    ajustes = cargar_ajustes()
    titulo = ajustes.get("USER_NAME", "Maestro") if ajustes else "Maestro"
    # 1. Iniciamos la GUI de REVAN visible desde el principio para ver el estado
    gui = RevanGUI(titulo_usuario=titulo)
    gui.mostrar_panel() 
    gui.actualizar_estado("💤 MODO PASIVO (APLAUDA)", "#ffb703") # Amarillo de espera
    # 2. Encendemos los oídos de la IA
    oidos_ia = MicrophoneClient()
    # 3. Lanzamos el bucle de escaneo de impacto
    gui.app.after(500, esperar_aplauso)
    gui.app.mainloop()