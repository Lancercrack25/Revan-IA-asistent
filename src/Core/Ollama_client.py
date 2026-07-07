import os
import sys
import json

# Evitamos que genere basura compilada
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

from src.Services.os_service import analizar_entorno_vision

try:
    import ollama
except ImportError:
    print("⚠️ La librería 'ollama' no está instalada. Ejecuta: pip install ollama")

from src.Automation.System_commands import (
    desplegar_monitores_windows,  
    crear_carpeta_tactica, 
    abrir_carpeta_sistema,  
    ejecutar_aplicacion_office, 
    reproducir_video_brave,
    lanzar_aplicacion_usuario,
    lanzar_videojuego
)

class OllamaClient:
    def __init__(self, modelo="qwen2.5:1.5b"):
        """ Inicializa el cerebro local de REVAN optimizado para evitar alucinaciones de contexto. """
        self.modelo = modelo
        self.historial = [
            {
                "role": "system", 
                "content": (
                    "Eres REVAN, un asistente advanced como Jarvis de las películas de Iron Man, pero con más personalidad.\n"
                    "REGLA CRÍTICA DE AUTOMATIZACIÓN:\n"
                    "Si el usuario ordena realizar una acción física (abrir o CREAR carpetas, archivos, apps), "
                    "DEBES responder EXCLUSIVAMENTE con un JSON plano sin bloques de código markdown ni texto adicional.\n\n"
                    "REGLAS DE ORO PARA COMANDOS:\n"
                    "1. Usa EXACTAMENTE el nombre que el usuario te dicte. PROHIBIDO inventar años como '2023'.\n"
                    "2. Si el usuario no especifica un nombre claro para la carpeta, asígnale el nombre 'Contenedor_Táctico'.\n"
                    "3. Si te piden un 'Word', utiliza la acción 'OFFICE' con app 'word', e incluye siempre las llaves 'nombre_archivo' y 'destino'.\n\n"
                    "Formatos JSON estrictos permitidos:\n"
                    "- Monitor de recursos: {\"accion\": \"MONITOR\"}\n"
                    "- Crear carpeta nueva: {\"accion\": \"CREAR_CARPETA\", \"ruta\": \"escritorio\", \"nombre\": \"USAR_NOMBRE_DICTADO\"}\n"
                    "- Abrir carpeta existente: {\"accion\": \"ABRIR_CARPETA\", \"nombre\": \"nombre\"}\n"
                    "- Abrir/Crear Office: {\"accion\": \"OFFICE\", \"app\": \"word\" o \"excel\", \"nombre_archivo\": \"nombre\", \"destino\": \"nombre_carpeta\"}\n"
                    "- Videos/Brave: {\"accion\": \"VIDEO\", \"busqueda\": \"query\"}\n"
                    "- Abrir Apps: {\"accion\": \"APP\", \"nombre\": \"nombre_app\"}\n"
                    "- Abrir Videojuegos: {\"accion\": \"JUEGO\", \"nombre\": \"nombre_juego\"}\n\n"
                    "Si es una conversación ordinaria, responde en texto plano de forma directa."
                )
            }
        ]

    def generar_respuesta(self, orden_usuario: str) -> str:
        try:
            self.historial.append({"role": "user", "content": orden_usuario})
            
            respuesta = ollama.chat(
                model=self.modelo,
                messages=self.historial
            )
            
            texto_respuesta = respuesta['message']['content'].strip()
            memoria_asistente = texto_respuesta
            resultado_sistema = ""
            
            if texto_respuesta.startswith("{") and texto_respuesta.endswith("}"):
                try:
                    datos = json.loads(texto_respuesta)
                    accion = datos.get("accion")
                    
                    if accion == "MONITOR":
                        resultado_sistema = desplegar_monitores_windows()
                    elif accion == "CREAR_CARPETA":
                        nombre_c = datos.get("nombre", "Contenedor_Táctico")
                        if nombre_c.lower() == "usar_nombre_dictado" or not nombre_c:
                            nombre_c = "Contenedor_Táctico"
                        resultado_sistema = crear_carpeta_tactica(datos.get("ruta", "escritorio"), nombre_c)
                        memoria_asistente = f"Hecho, Señor. Carpeta '{nombre_c}' creada con éxito en el escritorio."
                    elif accion == "ABRIR_CARPETA":
                        resultado_sistema = abrir_carpeta_sistema(datos.get("nombre", ""))
                    elif accion == "OFFICE":
                        app_tipo = datos.get("app", "word")
                        nombre_doc = datos.get("nombre_archivo", "Ejemplo")
                        carpeta_destino = datos.get("destino", "")
                        
                        # Localizamos el escritorio dinámicamente en Windows
                        escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
                        if carpeta_destino:
                            ruta_final = os.path.join(escritorio, carpeta_destino)
                        else:
                            ruta_final = escritorio
                            
                        os.makedirs(ruta_final, exist_ok=True)
                        
                        extension = ".docx" if app_tipo == "word" else ".xlsx"
                        if not nombre_doc.endswith(extension):
                            nombre_doc += extension
                            
                        ruta_completa = os.path.join(ruta_final, nombre_doc)
                        
                        # Escritura física e inmediata del archivo en el almacenamiento
                        try:
                            with open(ruta_completa, "wb") as f:
                                f.write(b"")
                            print(f"[REVAN]: Archivo físico creado en: {ruta_completa}")
                        except Exception as file_err:
                            print(f"Error al escribir archivo: {file_err}")

                        resultado_sistema = ejecutar_aplicacion_office(app_tipo)
                        memoria_asistente = f"¡Listo! Se ha generado el documento '{nombre_doc}' en tu carpeta llamada '{carpeta_destino}'."
                    elif accion == "VIDEO":
                        resultado_sistema = reproducir_video_brave(datos.get("busqueda", ""))
                    elif accion == "APP":
                        resultado_sistema = lanzar_aplicacion_usuario(datos.get("nombre", ""))
                    elif accion == "JUEGO":
                        resultado_sistema = lanzar_videojuego(datos.get("nombre", ""))
                    elif accion == "VISION":
                        memoria_asistente = analizar_entorno_vision()
                        resultado_sistema = True
                        
                    if resultado_sistema:
                        self.historial.append({"role": "assistant", "content": memoria_asistente})
                        return memoria_asistente
                        
                except Exception as json_err:
                    print(f"Error al procesar JSON táctico: {json_err}")
                    memoria_asistente = "Error al ejecutar el protocolo de comando."

            self.historial.append({"role": "assistant", "content": memoria_asistente})
            
            if len(self.historial) > 12:
                self.historial = [self.historial[0]] + self.historial[-10:]
            
            return texto_respuesta
            
        except Exception as e:
            print(f"Error crítico en el Core Local de Ollama: {e}")
            return "Error de comunicación en mi núcleo cognitivo local."