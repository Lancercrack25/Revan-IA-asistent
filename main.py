import os
import sys

# 🛡️ 1. ESCUDO ABSOLUTO: Bloqueamos pycache antes de que Python toque las subcarpetas
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

# 📦 2. IMPORTACIONES DE TU ARQUITECTURA REAL
from src.Core.Gemini_client import GeminiClient
from src.Core.Elevenlabs_client import ElevenLabsClient
from src.Core.microphone_client import MicrophoneClient
from src.Core.Config_loader import cargar_ajustes
from src.Gui.Dashboard import RevanGUI  # <-- Tu interfaz CustomTkinter con Núcleo Holográfico

# Inicialización de componentes globales
cerebro_ia = None
voz_ia = None
oidos_ia = None
gui = None
titulo = "Maestro"

def procesar_ciclo_voz():
    """Procesa una iteración del micrófono y la IA sin congelar la interfaz web-style."""
    global cerebro_ia, voz_ia, oidos_ia, gui, titulo

    # Si el usuario presionó el botón rojo de apagar en la GUI
    if gui.debe_cerrar:
        gui.actualizar_estado("Desconectando...", "#f85149")
        voz_ia.hablar(f"Entendido, {titulo}. Desconectando sistemas tácticos, espero volver a activarme.")
        gui.app.quit()
        return

    try:
        # 1. Cambiamos estado a ESCUCHANDO (El núcleo parpadeará rápido en Cyan)
        gui.actualizar_estado("🎤 ESCUCHANDO...", "#58a6ff")
        orden = oidos_ia.escuchar()
        
        if orden.strip():
            # El usuario habló, lo mostramos en la interfaz
            gui.agregar_mensaje("tu", orden)
            
            # Comandos por voz para apagar el sistema
            if any(palabra in orden.lower() for palabra in ["salir", "apagar sistema", "desconectar", "adiós", "apágate"]):
                gui.actualizar_estado("Desconectando...", "#f85149")
                voz_ia.hablar(f"Entendido, {titulo}. Desconectando sistemas tácticos.")
                gui.app.quit()
                return

            # 2. Cambiamos estado a PENSANDO (El núcleo girará a máxima velocidad de procesamiento)
            gui.actualizar_estado("🧠 PENSANDO...", "#7ef1ff")
            respuesta_texto = cerebro_ia.generar_respuesta(orden)
            
            # 3. Mostramos la respuesta y pasamos a HABLANDO (El anillo del núcleo vibrará y se expandirá con la voz)
            gui.agregar_mensaje("revan", respuesta_texto)
            gui.actualizar_estado("🔊 REVAN HABLANDO...", "#00f0ff")
            voz_ia.hablar(respuesta_texto)
            
            # 4. Regresa al estado base EN LÍNEA (El núcleo respira de forma calmada)
            gui.actualizar_estado("⚡ EN LÍNEA", "#7ef1ff")

    except Exception as e:
        gui.actualizar_estado("⚠️ ERROR EN SISTEMA", "#f85149")
        print(f"❌ Ocurrió un error en el ciclo de voz: {e}")

    # Regla de oro de las GUIs: Re-programamos esta misma función para que se ejecute 
    # en 100 milisegundos, manteniendo el bucle infinito vivo de forma asíncrona
    gui.app.after(100, procesar_ciclo_voz)

def main():
    global cerebro_ia, voz_ia, oidos_ia, gui, titulo
    
    print("🌌 Inicializando sistemas tácticos de REVAN (Modo GUI + Voz)...")
    
    # Cargar Ajustes iniciales
    ajustes = cargar_ajustes()
    titulo = ajustes.get("USER_NAME", "Maestro") if ajustes else "Maestro"
    
    # Inicializar la interfaz gráfica primero
    gui = RevanGUI(titulo_usuario=titulo)
    gui.actualizar_estado("⚙️ CARGANDO IA...", "#7ef1ff")
    
    try:
        # Cargar los motores lógicos y de audio
        cerebro_ia = GeminiClient()
        voz_ia = ElevenLabsClient()
        oidos_ia = MicrophoneClient()
    except Exception as e:
        print(f"❌ Error crítico de inicialización: {e}")
        return

    # Saludo inicial a través del sintetizador y la interfaz
    gui.actualizar_estado("⚡ EN LÍNEA", "#7ef1ff")
    gui.agregar_mensaje("revan", f"Sistemas principales en línea. Estoy listo, {titulo}.")
    
    # Programamos el inicio del ciclo de escucha en segundo plano
    gui.app.after(100, procesar_ciclo_voz)
    
    # Arrancamos la ventana (este método se queda con el control visual)
    gui.app.mainloop()

if __name__ == "__main__":
    main()