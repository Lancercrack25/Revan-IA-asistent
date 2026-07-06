import os
import sys
import json

# Evitamos que genere basura compilada
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

try:
    import ollama
except ImportError:
    print("⚠️ La librería 'ollama' no está instalada. Ejecuta: pip install ollama")

# Importamos las herramientas de automatización
from src.Automation.System_commands import (
    desplegar_monitores_windows, 
    ejecutar_limpieza_sistema, 
    crear_carpeta_tactica, 
    ejecutar_aplicacion_office, 
    reproducir_video_brave
)

class OllamaClient:
    def __init__(self, modelo="qwen2.5:1.5b"):
        """ Inicializa el cerebro local optimizado para los 4GB de VRAM con enrutamiento táctico. """
        self.modelo = modelo
        self.historial = [
            {
                "role": "system", 
                "content": (
                    "Eres REVAN, un asistente cyberpunk táctico militar. Responde siempre en español de forma concisa. "
                    "REGLA CRÍTICA: Si el usuario te ordena hacer una acción física en la PC, DEBES responder EXCLUSIVAMENTE con un JSON plano sin comentarios. "
                    "Formatos permitidos:\n"
                    "- Monitor de recursos: {\"accion\": \"MONITOR\"}\n"
                    "- Liberar espacio: {\"accion\": \"LIMPIEZA\"}\n"
                    "- Crear carpeta: {\"accion\": \"CARPETA\", \"ruta\": \"escritorio\", \"nombre\": \"nombre\"}\n"
                    "- Abrir Office: {\"accion\": \"OFFICE\", \"app\": \"word\" o \"excel\"}\n"
                    "- Videos/Brave: {\"accion\": \"VIDEO\", \"busqueda\": \"nombre o link\"}\n"
                    "Si es conversación o preguntas generales, responde en texto plano normal, directo y militar."
                )
            }
        ]

    def generar_respuesta(self, orden_usuario: str) -> str:
        try:
            # Enviamos la orden junto con las instrucciones del sistema
            respuesta = ollama.chat(
                model=self.modelo,
                messages=[*self.historial, {"role": "user", "content": orden_usuario}]
            )
            
            texto_respuesta = respuesta['message']['content'].strip()
            
            # 📡 Interceptor de Comandos Automatizados
            if texto_respuesta.startswith("{") and texto_respuesta.endswith("}"):
                try:
                    datos = json.loads(texto_respuesta)
                    accion = datos.get("accion")
                    
                    if accion == "MONITOR":
                        return desplegar_monitores_windows()
                    elif accion == "LIMPIEZA":
                        return ejecutar_limpieza_sistema()
                    elif accion == "CARPETA":
                        return crear_carpeta_tactica(datos.get("ruta", "escritorio"), datos.get("nombre", "Nueva_Carpeta"))
                    elif accion == "OFFICE":
                        return ejecutar_aplicacion_office(datos.get("app", "word"))
                    elif accion == "VIDEO":
                        return reproducir_video_brave(datos.get("busqueda", ""))
                except Exception:
                    pass # Si falla el parseo JSON, fluye como texto normal

            # Si es conversación fluida, guardamos en memoria y retornamos
            self.historial.append({"role": "user", "content": orden_usuario})
            self.historial.append({"role": "assistant", "content": texto_respuesta})
            
            return texto_respuesta
            
        except Exception as e:
            print(f"❌ Error crítico en el Core Local de Ollama: {e}")
            return "Error de comunicación en mi núcleo cognitivo local. Asegúrate de que Ollama esté corriendo."