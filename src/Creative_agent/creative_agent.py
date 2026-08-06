import os
import re
import time
import requests

from src.Security.rate_limiter import permitir_accion
from src.Security.auditoria import registrar_evento, NIVEL_INFO, NIVEL_ADVERTENCIA

HF_INFERENCE_URL = "https://api-inference.huggingface.co/models/{modelo}"
MODELO_DEFAULT = "stabilityai/stable-diffusion-xl-base-1.0"
TIMEOUT_SEGUNDOS = 60

def _slug_desde_prompt(prompt: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', prompt.strip().lower())
    return slug.strip('_')[:40] or "imagen"


def _guardar_imagen(contenido_bytes: bytes, prompt: str) -> str:
    """
    Guarda la imagen generada en una carpeta fija 'Imagenes_REVAN' dentro
    del Escritorio real del usuario (mismo patrón que Codigos_REVAN de
    Coder_agent: obtener_ruta_escritorio() detecta si el Escritorio está
    redirigido por OneDrive).
    """
    from src.Services.os_service import obtener_ruta_escritorio

    carpeta_imagenes = os.path.join(obtener_ruta_escritorio(), "Imagenes_REVAN")
    os.makedirs(carpeta_imagenes, exist_ok=True)

    nombre_archivo = f"{_slug_desde_prompt(prompt)}_{time.strftime('%Y%m%d_%H%M%S')}.png"
    ruta_completa = os.path.join(carpeta_imagenes, nombre_archivo)

    with open(ruta_completa, "wb") as f:
        f.write(contenido_bytes)

    return ruta_completa


def generar_imagen(prompt: str, api_key: str = None, modelo: str = MODELO_DEFAULT) -> str:
    """
    Genera una imagen a partir de 'prompt' con la API de inferencia de
    Hugging Face, la guarda en el Escritorio ('Imagenes_REVAN') y la abre
    automáticamente. Devuelve el texto que REVAN debe decir/mostrar.
    """
    if not permitir_accion("creative_agent"):
        return (
            "Señor, alcancé el límite de generación de imágenes en el último minuto. "
            "Espere un momento antes de intentarlo de nuevo."
        )

    api_key = api_key or os.getenv("HUGGINGFACE_API_KEY", "")
    if not api_key:
        return (
            "Señor, no tengo configurada la API key de Hugging Face todavía. Agréguela "
            "como HUGGINGFACE_API_KEY en las credenciales o variables de entorno."
        )

    if not prompt or not prompt.strip():
        return "Señor, necesito una descripción de qué imagen generar."

    url = HF_INFERENCE_URL.format(modelo=modelo)
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        respuesta = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=TIMEOUT_SEGUNDOS)
    except requests.RequestException as e:
        registrar_evento(
            modulo="creative_agent", accion="generar_imagen",
            resultado=f"Error de red: {e}", nivel=NIVEL_ADVERTENCIA,
        )
        return f"No pude contactar a Hugging Face, Señor: {e}"

    if respuesta.status_code == 503:
        try:
            tiempo_estimado = int(respuesta.json().get("estimated_time", 20))
        except Exception:
            tiempo_estimado = 20
        registrar_evento(
            modulo="creative_agent", accion="generar_imagen",
            resultado="Modelo cargando en Hugging Face (503)", nivel=NIVEL_ADVERTENCIA,
        )
        return (
            f"El modelo de imágenes se está inicializando en los servidores de Hugging Face, "
            f"Señor (tarda ~{tiempo_estimado} segundos la primera vez). Intente de nuevo en "
            f"un momento."
        )

    if respuesta.status_code == 401:
        return "Señor, la API key de Hugging Face fue rechazada. Verifique que sea correcta."

    if respuesta.status_code != 200:
        registrar_evento(
            modulo="creative_agent", accion="generar_imagen",
            resultado=f"HTTP {respuesta.status_code}: {respuesta.text[:200]}",
            nivel=NIVEL_ADVERTENCIA,
        )
        return f"Error generando la imagen, Señor (código {respuesta.status_code})."

    if "image" not in respuesta.headers.get("content-type", ""):
        # A veces la API devuelve JSON con un error aunque el status sea
        # 200 (poco común, pero pasa) -mejor validar el contenido real
        # antes de intentar guardarlo como imagen.
        registrar_evento(
            modulo="creative_agent", accion="generar_imagen",
            resultado=f"Respuesta inesperada (no es imagen): {respuesta.text[:200]}",
            nivel=NIVEL_ADVERTENCIA,
        )
        return "Señor, Hugging Face no devolvió una imagen válida. Intente reformular la descripción."

    try:
        ruta_guardado = _guardar_imagen(respuesta.content, prompt)
    except Exception as e:
        registrar_evento(
            modulo="creative_agent", accion="guardar_imagen",
            resultado=f"Error guardando: {e}", nivel=NIVEL_ADVERTENCIA,
        )
        return f"Generé la imagen pero no pude guardarla en disco, Señor: {e}"

    try:
        os.startfile(ruta_guardado)
    except Exception:
        pass  # No crítico si falla abrir la imagen; ya quedó guardada.

    registrar_evento(
        modulo="creative_agent", accion="generar_imagen",
        resultado=f"Imagen generada y guardada en {ruta_guardado}", nivel=NIVEL_INFO,
    )
    return f"Imagen generada y abierta, Señor. Guardada en:\n{ruta_guardado}"