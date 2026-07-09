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
    print("La librería 'ollama' no está instalada. Ejecuta: pip install ollama")

from src.Automation.System_commands import (
    desplegar_monitores_windows, 
    ejecutar_aplicacion_office, 
    reproducir_video_brave,
    lanzar_aplicacion_usuario,
    lanzar_videojuego
)

class OllamaClient:
    # Si el usuario menciona alguna de estas palabras pero el modelo NO
    # devuelve un JSON de acción, se asume que "se le olvidó" y se hace un
    # reintento forzado y aislado (ver _forzar_json_accion)
    PALABRAS_ACCION = [
        "carpeta", "word", "excel", "documento",
        "navegador", "video", "busca", "reproduce", "brave",
        "app", "aplicación", "aplicacion", "juego",
        "monitor", "recursos"
    ]

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
                    "- Crear carpeta nueva: {\"accion\": \"CREAR_CARPETA\", \"ruta\": \"actual|escritorio|documentos\", \"nombre\": \"USAR_NOMBRE_DICTADO\"}\n"
                    "  (usa 'escritorio' o 'documentos' SOLO si el usuario lo menciona explícitamente; si no dijo nada, usa 'actual')\n"
                    "- Abrir carpeta existente: {\"accion\": \"ABRIR_CARPETA\", \"nombre\": \"nombre\"}\n"
                    "- Abrir/Crear Office: {\"accion\": \"OFFICE\", \"app\": \"word\", \"nombre_archivo\": \"nombre\", \"destino\": \"actual\"}\n"
                    "- Videos/Brave: {\"accion\": \"VIDEO\", \"busqueda\": \"query\"}\n"
                    "- Abrir Apps: {\"accion\": \"APP\", \"nombre\": \"nombre_app\"}\n"
                    "- Abrir Videojuegos: {\"accion\": \"JUEGO\", \"nombre\": \"nombre_juego\"}\n\n"
                )
            }
        ]

    def _extraer_json(self, texto: str):
        """Extrae de forma segura un objeto JSON del texto devuelto por la IA."""
        texto = texto.strip()

        # 1. Intentar parseo directo
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            pass

        # 2. Quitar fences de markdown
        sin_fences = re.sub(r'```(?:json)?', '', texto, flags=re.IGNORECASE).strip()
        if sin_fences != texto:
            try:
                return json.loads(sin_fences)
            except json.JSONDecodeError:
                texto = sin_fences

        # 3. Decodificar desde la primera llave encontrada
        decoder = json.JSONDecoder()
        for i, ch in enumerate(texto):
            if ch != "{":
                continue
            try:
                objeto, _ = decoder.raw_decode(texto[i:])
                return objeto
            except json.JSONDecodeError:
                continue

        return None

    def _recortar_historial(self):
        """Mantiene el historial dentro de un límite sin romper la alternancia User/Assistant."""
        if len(self.historial) <= 12:
            return

        system_msg = self.historial[0]
        mensajes_recientes = self.historial[-10:]

        # Asegurar que el primer mensaje tras el system prompt sea del 'user'
        while mensajes_recientes and mensajes_recientes[0].get("role") != "user":
            mensajes_recientes.pop(0)

        self.historial = [system_msg] + mensajes_recientes

    def _forzar_json_accion(self, orden_usuario: str):
        """
        Reintento aislado: si el usuario mencionó una palabra de acción clara
        (word, navegador, video, etc.) pero el modelo respondió con texto
        conversacional en vez de JSON, se hace UNA llamada extra, fuera del
        historial normal (para no arrastrar la conversación que ya lo
        "despistó"), pidiendo EXCLUSIVAMENTE el JSON de acción.

        Esto no es una solución perfecta: sigue siendo el mismo modelo chico
        y puede volver a fallar. Pero reduce los casos donde una orden clara
        se pierde en una respuesta puramente conversacional.
        """
        try:
            mensaje_forzado = [
                self.historial[0],  # mismo system prompt
                {"role": "user", "content": (
                    f'Orden del usuario: "{orden_usuario}"\n'
                    "Responde EXCLUSIVAMENTE con el JSON de acción correspondiente, "
                    "sin texto adicional, sin explicaciones, sin bloques de código."
                )}
            ]
            respuesta = ollama.chat(model=self.modelo, messages=mensaje_forzado)
            texto = respuesta['message']['content'].strip()
            return self._extraer_json(texto)
        except Exception as e:
            print(f"[OllamaClient]: Falló el reintento forzado de JSON: {e}")
            return None

    def generar_respuesta(self, orden_usuario: str) -> str:
        try:
            orden_clean = orden_usuario.lower().strip()

            # INTERCEPTOR 1: Disparo directo para visión y cámara
            if any(k in orden_clean for k in ["camara", "cámara", "enciende la camara", "enciende la cámara", "que ves", "qué ves", "ver entorno"]):
                print("[OllamaClient]: Intercepción directa del sensor óptico...")
                memoria_asistente = analizar_entorno_vision()
                registrar_accion_sistema(orden_usuario, memoria_asistente, "VISION")
                
                self.historial.append({"role": "user", "content": orden_usuario})
                self.historial.append({"role": "assistant", "content": memoria_asistente})
                self._recortar_historial()
                return memoria_asistente

            # Registrar entrada del usuario
            self.historial.append({"role": "user", "content": orden_usuario})
            
            respuesta = ollama.chat(
                model=self.modelo,
                messages=self.historial
            )

            total_ns = respuesta.get("total_duration")
            eval_ns = respuesta.get("eval_duration")
            if total_ns is not None:
                print(f"[Ollama] Tiempo total: {total_ns/1e9:.2f}s | Solo inferencia: {(eval_ns or 0)/1e9:.2f}s")
            
            texto_respuesta = respuesta['message']['content'].strip()
            memoria_asistente = texto_respuesta

            # Evaluar si la respuesta contiene un comando JSON
            datos = self._extraer_json(texto_respuesta)

            # Si el usuario claramente pidió una acción (mencionó una de las
            # PALABRAS_ACCION) pero el modelo no devolvió JSON, se reintenta
            # UNA vez de forma forzada y aislada antes de rendirse y contestar
            # de forma conversacional.
            if (not datos or "accion" not in datos) and any(p in orden_clean for p in self.PALABRAS_ACCION):
                print("[OllamaClient]: Orden con palabra de acción pero sin JSON. Reintentando forzado...")
                datos_retry = self._forzar_json_accion(orden_usuario)
                if datos_retry and isinstance(datos_retry, dict) and "accion" in datos_retry:
                    print(f"[OllamaClient]: Reintento exitoso -> {datos_retry}")
                    datos = datos_retry

            if datos and isinstance(datos, dict) and "accion" in datos:
                accion = datos.get("accion")
                print(f"[OllamaClient]: Acción detectada -> {accion}")

                if accion == "MONITOR":
                    desplegar_monitores_windows()
                    memoria_asistente = "Monitores tácticos del sistema desplegados, Señor."
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "MONITOR")

                elif accion == "CREAR_CARPETA":
                    nombre_c = datos.get("nombre", "Contenedor_Táctico")
                    if str(nombre_c).lower() in ["usar_nombre_dictado", ""] or not nombre_c:
                        nombre_c = "Contenedor_Táctico"
                    ruta_c = datos.get("ruta", "actual")

                    memoria_asistente = crear_carpeta_sistema(nombre_c, ruta_c)
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "CREAR_CARPETA")

                elif accion == "ABRIR_CARPETA":
                    nombre_target = datos.get("nombre", "")
                    memoria_asistente = abrir_carpeta_sistema(nombre_target)
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
                    
                    # Ejecutar la app (es mejor dejar que el proceso abra el documento o plantilla)
                    ejecutar_aplicacion_office(app_tipo)
                    nombre_directorio_actual = os.path.basename(ruta_final)
                    memoria_asistente = f"¡Listo, Señor! Abriendo {app_tipo.capitalize()} para el documento en '{nombre_directorio_actual}'."
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "OFFICE")

                elif accion == "VIDEO":
                    reproducir_video_brave(datos.get("busqueda", ""))
                    memoria_asistente = f"Reproduciendo contenido sobre '{datos.get('busqueda', '')}' en Brave."
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "VIDEO")

                elif accion == "APP":
                    lanzar_aplicacion_usuario(datos.get("nombre", ""))
                    memoria_asistente = f"Ejecutando aplicación {datos.get('nombre', '')}."
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "APP")

                elif accion == "JUEGO":
                    lanzar_videojuego(datos.get("nombre", ""))
                    memoria_asistente = f"Iniciando {datos.get('nombre', '')}, Señor."
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "JUEGO")

                elif accion == "VISION":
                    memoria_asistente = analizar_entorno_vision()
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "VISION")

                else:
                    print(f"[OllamaClient]: Acción desconocida recibida del modelo: {accion!r}")
                    memoria_asistente = "No reconocí bien esa instrucción, Señor. ¿Puede repetirla de otra forma?"
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "ACCION_DESCONOCIDA")

            # Guardar en memoria y retornar respuesta hablable (evita retornar cadenas JSON)
            self.historial.append({"role": "assistant", "content": memoria_asistente})
            self._recortar_historial()

            return memoria_asistente
            
        except Exception as e:
            print(f"Error crítico en el Core Local de Ollama: {e}")
            return "Error de comunicación en mi núcleo cognitivo local."