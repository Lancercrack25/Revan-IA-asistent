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

# Importamos el Orquestador Central unificado
from src.Automation.System_commands import (
    desplegar_monitores_windows, 
    ejecutar_limpieza_sistema, 
    crear_carpeta_tactica, 
    abrir_carpeta_sistema,  # 🎯 Importada para abrir tus carpetas físicas
    ejecutar_aplicacion_office, 
    reproducir_video_brave,
    lanzar_aplicacion_usuario,
    lanzar_videojuego
)

class OllamaClient:
    def __init__(self, modelo="qwen2.5:1.5b"):
        """ Inicializa el cerebro local de REVAN optimizado para 4GB de VRAM y automatización masiva. """
        self.modelo = modelo
        self.historial = [
            {
                "role": "system", 
                "content": (
                    "Eres REVAN, un asistente cyberpunk táctico militar. Responde siempre en español de forma concisa. "
                    "REGLA CRÍTICA: Si el usuario te ordena hacer una acción física en la PC (abrir apps, juegos, carpetas, etc.), "
                    "DEBES responder EXCLUSIVAMENTE con un JSON plano sin comentarios ni bloques de código markdown. "
                    "Formatos JSON permitidos:\n"
                    "- Monitor de recursos: {\"accion\": \"MONITOR\"}\n"
                    "- Liberar espacio: {\"accion\": \"LIMPIEZA\"}\n"
                    "- Crear carpeta nueva: {\"accion\": \"CREAR_CARPETA\", \"ruta\": \"escritorio\", \"nombre\": \"nombre\"}\n"
                    "- Abrir carpeta existente (Códigos, Portafolio, etc.): {\"accion\": \"ABRIR_CARPETA\", \"nombre\": \"codigos\" o \"portafolio\"}\n"
                    "- Abrir Office: {\"accion\": \"OFFICE\", \"app\": \"word\" o \"excel\"}\n"
                    "- Videos/Brave: {\"accion\": \"VIDEO\", \"busqueda\": \"nombre o link\"}\n"
                    "- Abrir Plataformas/Apps (Steam, Epic, Discord): {\"accion\": \"APP\", \"nombre\": \"epic games\" o \"steam\"}\n"
                    "- Abrir Videojuegos (Fortnite, Overwatch, DMC): {\"accion\": \"JUEGO\", \"nombre\": \"fortnite\" o \"marvel rivals\"}\n"
                    "Si es conversación o preguntas generales, responde en texto plano normal, directo y militar."
                )
            }
        ]

    def generar_respuesta(self, orden_usuario: str) -> str:
        try:
            # Enviamos la orden junto con las instrucciones estructuradas
            respuesta = ollama.chat(
                model=self.modelo,
                messages=[*self.historial, {"role": "user", "content": orden_usuario}]
            )
            
            texto_respuesta = respuesta['message']['content'].strip()
            
            # 📡 Interceptor y Enrutador Inteligente de Comandos JSON
            if texto_respuesta.startswith("{") and texto_respuesta.endswith("}"):
                try:
                    datos = json.loads(texto_respuesta)
                    accion = datos.get("accion")
                    
                    if accion == "MONITOR":
                        return desplegar_monitores_windows()
                    elif accion == "LIMPIEZA":
                        return ejecutar_limpieza_sistema()
                    elif accion == "CREAR_CARPETA":
                        return crear_carpeta_tactica(datos.get("ruta", "escritorio"), datos.get("nombre", "Nueva_Carpeta"))
                    elif accion == "ABRIR_CARPETA":
                        return abrir_carpeta_sistema(datos.get("nombre", ""))
                    elif accion == "OFFICE":
                        return ejecutar_aplicacion_office(datos.get("app", "word"))
                    elif accion == "VIDEO":
                        return reproducir_video_brave(datos.get("busqueda", ""))
                    elif accion == "APP":
                        return lanzar_aplicacion_usuario(datos.get("nombre", ""))
                    elif accion == "JUEGO":
                        return lanzar_videojuego(datos.get("nombre", ""))
                except Exception as json_err:
                    print(f"⚠️ Error al procesar JSON táctico: {json_err}")
                    pass 

            # Si es conversación ordinaria, mantenemos el hilo en la memoria local
            self.historial.append({"role": "user", "content": orden_usuario})
            self.historial.append({"role": "assistant", "content": texto_respuesta})
            
            return texto_respuesta
            
        except Exception as e:
            print(f"❌ Error crítico en el Core Local de Ollama: {e}")
            return "Error de comunicación en mi núcleo cognitivo local. Asegúrese de que el servidor Ollama esté activo."