import os
import json
import re
import time

try:
    from openai import OpenAI
except ImportError:
    print("Falta la librería 'openai'. Instálala con: pip install openai")
    raise

# Mismas funciones de ejecución de acciones que usa Ollama_client.py
from src.Services.os_service import (
    analizar_entorno_vision,
    abrir_carpeta_sistema,
    crear_carpeta_sistema,
    obtener_ruta_actual,
    registrar_accion_sistema
)
from src.Automation.System_commands import (
    desplegar_monitores_windows,
    ejecutar_aplicacion_office,
    reproducir_video_brave,
    lanzar_aplicacion_usuario,
    lanzar_videojuego
)


class NimClient:
    """
    Cliente para NVIDIA NIM (mistral-nemotron), como reemplazo de OllamaClient
    para el módulo de acciones.

    DECISIÓN DE DISEÑO PARA AHORRAR TOKENS:
    A diferencia de OllamaClient (que acumula todo el historial de la
    conversación y lo reenvía completo en cada llamada), este cliente es
    STATELESS: cada llamada manda solo [system, user], sin arrastrar turnos
    anteriores. Para clasificar/ejecutar una acción física no hace falta
    memoria de conversación, y así el costo por llamada se mantiene
    constante sin importar cuánto lleves usando REVAN en la sesión, en vez
    de ir creciendo turno a turno.
    """

    PALABRAS_ACCION = [
        "carpeta", "word", "excel", "documento",
        "navegador", "video", "busca", "reproduce", "brave",
        "app", "aplicación", "aplicacion", "juego",
        "monitor", "recursos"
    ]

    def __init__(self, api_key: str = None, modelo: str = "mistralai/mistral-nemotron"):
        # 1. Si no se pasó api_key por parámetro, intentamos leer config/credentials.json
        if not api_key:
            ruta_credenciales = os.path.join("config", "credentials.json")
            if os.path.exists(ruta_credenciales):
                try:
                    with open(ruta_credenciales, "r", encoding="utf-8") as f:
                        credenciales = json.load(f)
                        # Busca la api key bajo distintos nombres comunes en tu JSON
                        api_key = (
                            credenciales.get("nvidia_api_key") or 
                            credenciales.get("NVIDIA_API_KEY") or 
                            credenciales.get("NVIDIA_NIM_API_KEY") or
                            credenciales.get("api_key")
                        )
                except Exception as e:
                    print(f"[NimClient] Error al leer {ruta_credenciales}: {e}")

        # 2. Si no se encontró en el JSON, busca en las variables de entorno
        self.api_key = api_key or os.getenv("NVIDIA_NIM_API_KEY", "")

        # 3. Si sigue sin existir, lanza el error
        if not self.api_key:
            raise ValueError(
                "Falta la API key de NVIDIA NIM. Asegúrate de configurar correctamente "
                "el archivo 'config/credentials.json' o define la variable de entorno NVIDIA_NIM_API_KEY."
            )

        self.modelo = modelo
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=self.api_key,
        )

        # Prompt recortado a lo esencial
        self.system_prompt = (
            "Eres REVAN, asistente tipo Jarvis para el sistema operativo.\n"
            "Si el usuario pide una acción física (crear/abrir carpetas, archivos, apps, cámara), "
            "responde SOLO con el JSON correspondiente, sin texto ni bloques de código.\n"
            "Si no especifica nombre para una carpeta, usa 'Contenedor_Táctico'.\n\n"
            "JSON válidos:\n"
            "{\"accion\":\"VISION\"}\n"
            "{\"accion\":\"MONITOR\"}\n"
            "{\"accion\":\"CREAR_CARPETA\",\"ruta\":\"actual\",\"nombre\":\"Proyecto\"}\n"
            "{\"accion\":\"CREAR_CARPETA\",\"ruta\":\"escritorio\",\"nombre\":\"Fotos\"}  (solo si dice 'escritorio')\n"
            "{\"accion\":\"CREAR_CARPETA\",\"ruta\":\"documentos\",\"nombre\":\"Tareas\"}  (solo si dice 'documentos')\n"
            "{\"accion\":\"ABRIR_CARPETA\",\"nombre\":\"nombre\"}\n"
            "{\"accion\":\"OFFICE\",\"app\":\"word\",\"nombre_archivo\":\"nombre\",\"destino\":\"actual\"}\n"
            "{\"accion\":\"VIDEO\",\"busqueda\":\"query\"}\n"
            "{\"accion\":\"APP\",\"nombre\":\"nombre_app\"}\n"
            "{\"accion\":\"JUEGO\",\"nombre\":\"nombre_juego\"}\n\n"
            "Si es conversación normal, responde en texto plano, máximo 25 palabras."
        )

    def _extraer_json(self, texto: str):
        texto = texto.strip()
        try:
            return json.loads(texto)
        except json.JSONDecodeError:
            pass

        sin_fences = re.sub(r'```(?:json)?', '', texto, flags=re.IGNORECASE).strip()
        if sin_fences != texto:
            try:
                return json.loads(sin_fences)
            except json.JSONDecodeError:
                texto = sin_fences

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

    def _llamar_modelo(self, mensajes, max_tokens=200):
        respuesta = self.client.chat.completions.create(
            model=self.modelo,
            messages=mensajes,
            temperature=0.3,
            top_p=0.7,
            max_tokens=max_tokens,
            stream=False,
        )
        return respuesta.choices[0].message.content.strip()

    def _forzar_json_accion(self, orden_usuario: str):
        try:
            mensaje_forzado = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": (
                    f'Orden del usuario: "{orden_usuario}"\n'
                    "Responde EXCLUSIVAMENTE con el JSON de acción correspondiente."
                )}
            ]
            texto = self._llamar_modelo(mensaje_forzado, max_tokens=150)
            return self._extraer_json(texto)
        except Exception as e:
            print(f"[NimClient]: Falló el reintento forzado de JSON: {e}")
            return None

    def generar_respuesta(self, orden_usuario: str) -> str:
        try:
            orden_clean = orden_usuario.lower().strip()

            # Cámara: igual que Ollama_client, se resuelve local (llava)
            if any(k in orden_clean for k in ["camara", "cámara", "que ves", "qué ves", "ver entorno"]):
                memoria_asistente = analizar_entorno_vision()
                registrar_accion_sistema(orden_usuario, memoria_asistente, "VISION")
                return memoria_asistente

            t0 = time.time()
            texto_respuesta = self._llamar_modelo([
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": orden_usuario},
            ])
            print(f"[NIM] Tiempo: {time.time() - t0:.2f}s")

            memoria_asistente = texto_respuesta
            datos = self._extraer_json(texto_respuesta)

            if (not datos or "accion" not in datos) and any(p in orden_clean for p in self.PALABRAS_ACCION):
                print("[NimClient]: Orden con palabra de acción pero sin JSON. Reintentando forzado...")
                datos_retry = self._forzar_json_accion(orden_usuario)
                if datos_retry and isinstance(datos_retry, dict) and "accion" in datos_retry:
                    datos = datos_retry

            if datos and isinstance(datos, dict) and "accion" in datos:
                accion = datos.get("accion")
                print(f"[NimClient]: Acción detectada -> {accion}")

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
                    memoria_asistente = "No reconocí bien esa instrucción, Señor. ¿Puede repetirla de otra forma?"
                    registrar_accion_sistema(orden_usuario, memoria_asistente, "ACCION_DESCONOCIDA")

            return memoria_asistente

        except Exception as e:
            print(f"Error crítico en NimClient: {e}")
            return "Error de comunicación con el núcleo cognitivo en la nube."


if __name__ == "__main__":
    # Prueba rápida y aislada
    cliente = NimClient()
    pruebas = [
        "crea una carpeta llamada Prueba en el escritorio",
        "crea una carpeta",
        "puedes crear dentro de esa carpeta un archivo de word",
        "abre una ventana en el navegador sobre minecraft",
        "hola revan como estas",
    ]
    for p in pruebas:
        print(f"\n--- Orden: {p} ---")
        print(cliente.generar_respuesta(p))