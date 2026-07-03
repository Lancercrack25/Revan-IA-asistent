import os
import sys

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

from src.Core.Gemini_client import GeminiClient
from src.Core.Elevenlabs_client import ElevenLabsClient
from src.Core.microphone_client import MicrophoneClient  # NUEVO
from src.Core.Config_loader import cargar_ajustes

def main():
    print("🌌 Inicializando sistemas tácticos de REVAN (Modo Voz)...")
    
    # 1. Ajustes
    ajustes = cargar_ajustes()
    titulo = ajustes.get("USER_NAME", "Maestro") if ajustes else "Maestro"
    
    # 2. Inicializar componentes
    try:
        cerebro_ia = GeminiClient()
        voz_ia = ElevenLabsClient()
        oidos_ia = MicrophoneClient()  # NUEVO
    except Exception as e:
        print(f"❌ Error de inicialización: {e}")
        return

    print("\n🔊 Revan tomando el control...")
    voz_ia.hablar(f"Sistemas principales en línea. Estoy listo, {titulo}. Hábleme cuando lo desee.")
    
    # 3. Bucle por voz interactivo
    while True:
        try:
            # Revan se queda escuchando tu voz
            orden = oidos_ia.escuchar()
            
            # Si no dijiste nada o hubo un ruido extraño, salta al siguiente ciclo sin interrumpir
            if not orden.strip():
                continue
                
            # Comandos de apagado por voz
            if any(palabra in orden.lower() for palabra in ["salir", "apagar sistema", "desconectar","adios", "apagate"]):
                voz_ia.hablar(f"Entendido, {titulo}. Desconectando sistemas tácticos, espero volver a activarme para seguir sus instrucciones.")
                break
                
            print(f"🧠 Revan pensando respuesta...")
            #aqui se genera la respuesta de la ia y se te la da con voz
            respuesta_texto = cerebro_ia.generar_respuesta(orden)
            
            print(f"🤖 [REVAN]: {respuesta_texto}")
            voz_ia.hablar(respuesta_texto)
            
        except KeyboardInterrupt:
            print(f"\n🔒 Cierre de emergencia activado por el {titulo}.")
            break
        except Exception as e:
            print(f"❌ Ocurrió un error en el ciclo de voz: {e}")

if __name__ == "__main__":
    main()