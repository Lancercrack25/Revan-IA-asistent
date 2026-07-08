import os
import sys
import json
import re

# Prevenir la generación de archivos .pyc
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

# Servicios del Sistema y Gestión de Estado con PostgreSQL
from src.Services.os_service import (
    analizar_entorno_vision,
    abrir_carpeta_sistema,
    crear_carpeta_sistema,
    obtener_ruta_actual,
    registrar_accion_sistema
)

try:
    import ollama
except ImportError:
    print("⚠️ La librería 'ollama' no está instalada. Ejecuta: pip install ollama")

from src.Automation.System_commands import (
    desplegar_monitores_windows, 
    ejecutar_aplicacion_office, 
    reproducir_video_brave,
    lanzar_aplicacion_usuario,
    lanzar_videojuego
)

class OllamaClient:
    def __init__(self, modelo="qwen2.5:1.5b"):
        """Inicializa el cerebro local de REVAN optimizado para interacción por comandos JSON."""
        self.modelo = modelo
        self.historial = [
            {
                "role": "system", 
                "content": (
                    "Eres REVAN, un asistente avanzado tipo Jarvis para el sistema operativo.\n"
                    "REGLA CRÍTICA DE AUTOMATIZACIÓN:\n"
                    "Si el usuario ordena realizar una acción física (abrir o crear carpetas, archivos, apps, ver cámara), "
                    "DEBES responder EXCLUSIVAMENTE con un JSON plano sin bloques de código ni texto adicional.\n\n"
                    "REGLAS DE ORO PARA COMANDOS:\n"
                    "1. Usa EXACTAMENTE el nombre que el usuario te dicte.\n"
                    "2. Si el usuario no especifica un nombre claro para la carpeta, asigna 'Contenedor_Táctico'.\n"
                    "3. Para Word o Excel, utiliza la acción 'OFFICE' con app 'word' o 'excel'.\n\n"
                    "Formatos JSON estrictos permitidos:\n"
                    "- Activar Cámara / Ver entorno: {\"accion\": \"VISION\"}\n"
                    "- Monitor de recursos: {\"accion\": \"MONITOR\"}\n"
                    "- Crear carpeta nueva: {\"accion\": \"CREAR_CARPETA\", \"ruta\": \"actual\", \"nombre\": \"USAR_NOMBRE_DICTADO\"}\n"
                    "- Abrir carpeta existente: {\"accion\": \"ABRIR_CARPETA\", \"nombre\": \"nombre\"}\n"
                    "- Abrir/Crear Office: {\"accion\": \"OFFICE\", \"app\": \"word\", \"nombre_archivo\": \"nombre\", \"destino\": \"actual\"}\n"
                    "- Videos/Brave: {\"accion\": \"VIDEO\", \"busqueda\": \"query\"}\n"
                    "- Abrir Apps: {\"accion\": \"APP\", \"nombre\": \"nombre_app\"}\n"
                    "- Abrir Videojuegos: {\"accion\": \"JUEGO\", \"nombre\": \"nombre_juego\"}\n\n"
                    "Si es una conversación ordinaria, responde en texto plano de forma breve e inteligente."
                )
            }
        ]

    def _extraer_json(self, texto: str):
        """Extrae de forma segura un objeto JSON del texto devuelto por la IA."""
        try:
            # 1. Intentar parseo directo
            return json.loads(texto.strip())
        except json.JSONDecodeError:
            # 2. Buscar patrón JSON mediante Expresiones Regulares
            match = re.search(r'\{.*\}', texto, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return None

    def generar_respuesta(self, orden_usuario: str) -> str:
        try:
            orden_clean = orden_usuario.lower().strip()

            # 🎯 INTERCEPTOR 1: Disparo directo para visión y cámara
            if any(k in orden_clean for k in ["camara", "cámara", "enciende la camara", "enciende la cámara", "que ves", "qué ves", "ver entorno"]):
                print("📷 [OllamaClient]: Intercepción directa del sensor óptico...")
                memoria_asistente = analizar_entorno_vision()
                registrar_accion_sistema(orden_usuario, memoria_asistente, "VISION")
                self.historial.append({"role": "user", "content": orden_usuario})
                self.historial.append({"role": "assistant", "content": memoria_asistente})
                return memoria_asistente

            # Añadir interacción al historial de Ollama
            self.historial.append({"role": "user", "content": orden_usuario})
            
            respuesta = ollama.chat(
                model=self.modelo,
                messages=self.historial
            )
            
            texto_respuesta = respuesta['message']['content'].strip()
            memoria_asistente = texto_respuesta
            resultado_sistema = False

            # Evaluar si la respuesta contiene un comando JSON
            datos = self._extraer_json(texto_respuesta)

            if datos and isinstance(datos, dict) and "accion" in datos:
                accion = datos.get("accion")
                print(f"⚡ [OllamaClient]: Acción detectada -> {accion}")

                if accion == "MONITOR":
                    resultado_sistema = desplegar_monitores_windows()
                    memoria_asistente = "Monitores tácticos del sistema desplegados, Señor."
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "MONITOR")

                elif accion == "CREAR_CARPETA":
                    nombre_c = datos.get("nombre", "Contenedor_Táctico")
                    if str(nombre_c).lower() in ["usar_nombre_dictado", ""] or not nombre_c:
                        nombre_c = "Contenedor_Táctico"
                    
                    memoria_asistente = crear_carpeta_sistema(nombre_c)
                    resultado_sistema = True
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "CREAR_CARPETA")

                elif accion == "ABRIR_CARPETA":
                    nombre_target = datos.get("nombre", "")
                    memoria_asistente = abrir_carpeta_sistema(nombre_target)
                    resultado_sistema = True
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "ABRIR_CARPETA")

                elif accion == "OFFICE":
                    app_tipo = datos.get("app", "word")
                    nombre_doc = datos.get("nombre_archivo", "Documento_Táctico")
                    carpeta_destino = datos.get("destino", "")
                    
                    if carpeta_destino and carpeta_destino.lower() != "actual":
                        escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
                        ruta_final = os.path.join(escritorio, carpeta_destino)
                    else:
                        ruta_final = obtener_ruta_actual()
                        
                    os.makedirs(ruta_final, exist_ok=True)
                    
                    extension = ".docx" if app_tipo == "word" else ".xlsx"
                    if not nombre_doc.endswith(extension):
                        nombre_doc += extension
                        
                    ruta_completa = os.path.join(ruta_final, nombre_doc)
                    
                    try:
                        with open(ruta_completa, "wb") as f:
                            f.write(b"")
                        print(f"[REVAN]: Archivo físico generado en: {ruta_completa}")
                    except Exception as file_err:
                        print(f"❌ Error al escribir archivo físico: {file_err}")

                    resultado_sistema = ejecutar_aplicacion_office(app_tipo)
                    nombre_directorio_actual = os.path.basename(ruta_final)
                    memoria_asistente = f"¡Listo, Señor! Documento '{nombre_doc}' generado exitosamente en '{nombre_directorio_actual}'."
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "OFFICE")

                elif accion == "VIDEO":
                    resultado_sistema = reproducir_video_brave(datos.get("busqueda", ""))
                    memoria_asistente = f"Reproduciendo contenido sobre '{datos.get('busqueda', '')}' en Brave."
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "VIDEO")

                elif accion == "APP":
                    resultado_sistema = lanzar_aplicacion_usuario(datos.get("nombre", ""))
                    memoria_asistente = f"Ejecutando aplicación {datos.get('nombre', '')}."
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "APP")

                elif accion == "JUEGO":
                    resultado_sistema = lanzar_videojuego(datos.get("nombre", ""))
                    memoria_asistente = f"Iniciando {datos.get('nombre', '')}, Señor."
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "JUEGO")

                elif accion == "VISION":
                    memoria_asistente = analizar_entorno_vision()
                    resultado_sistema = True
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "VISION")

                if resultado_sistema:
                    self.historial.append({"role": "assistant", "content": memoria_asistente})
                    return memoria_asistente

            # Si fue una respuesta conversacional normal
            self.historial.append({"role": "assistant", "content": memoria_asistente})
            
            # Mantenimiento de ventana de memoria (últimas 10 interacciones)
            if len(self.historial) > 12:
                self.historial = [self.historial[0]] + self.historial[-10:]
            
            return texto_respuesta
            
        except Exception as e:
            print(f"❌ Error crítico en el Core Local de Ollama: {e}")
            return "Error de comunicación en mi núcleo cognitivo local."