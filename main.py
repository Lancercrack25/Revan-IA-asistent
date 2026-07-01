from src.Core.Elevenlabs_client import ElevenLabsClient
from src.Core.Config_loader import cargar_ajustes

if __name__ == "__main__":
    ajustes = cargar_ajustes()
    titulo = ajustes.get("USER_NAME")
    
    print("🤖 Inicializando sistema de voz...")
    revan_voz = ElevenLabsClient()
    
    # El saludo épico
    mensaje = f"Sistemas en línea, {titulo}. Todos los módulos de control de su ordenador están listos para sus ordenes"
    print(f"Texto a decir: '{mensaje}'")
    
    revan_voz.hablar(mensaje)
    print("✅ Prueba finalizada.")