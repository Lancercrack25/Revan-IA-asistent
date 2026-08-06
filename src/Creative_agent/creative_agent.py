"""
Creative_agent: generación de imágenes de REVAN.

Genera imágenes a partir de una descripción en texto. Proveedor
principal: NVIDIA NIM (mismo catálogo y MISMA API key que ya usa
NimClient para el LLM -NVIDIA_NIM_API_KEY-, no hace falta una cuenta
nueva). Si por algún motivo NVIDIA no está disponible pero sí tienes una
key de Hugging Face configurada, cae a ese proveedor como respaldo.

Sin confirmación, a propósito: es una acción local y reversible -genera
un archivo de imagen y lo abre-, mismo criterio que ya se aplicó a
carpetas/Word/Excel (la confirmación se reserva para lo irreversible y
externo, como WhatsApp o correo).

*** AVISO HONESTO ***
El formato exacto del endpoint de NVIDIA NIM para imágenes se armó según
la documentación pública (https://docs.api.nvidia.com/nim/reference/
stabilityai-stable-diffusion-3-medium-infer), pero no se pudo probar
contra la API real con una key válida. Si al usarlo el error menciona un
campo del JSON que no reconoce, es cuestión de ajustar
_construir_payload_nvidia()/_extraer_imagen_nvidia() a como responda tu
cuenta real -la lógica general (guardar, abrir, auditar, rate limit) no
cambia.
"""
import os
import re
import time
import base64
import requests

from src.Security.rate_limiter import permitir_accion
from src.Security.auditoria import registrar_evento, NIVEL_INFO, NIVEL_ADVERTENCIA

NVIDIA_IMG_URL = "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium"
NVIDIA_MODELO_DEFAULT = "stabilityai/stable-diffusion-3-medium"

HF_INFERENCE_URL = "https://api-inference.huggingface.co/models/{modelo}"
HF_MODELO_DEFAULT = "stabilityai/stable-diffusion-xl-base-1.0"

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


def _finalizar_imagen(contenido_bytes: bytes, prompt: str, proveedor: str) -> str:
    try:
        ruta_guardado = _guardar_imagen(contenido_bytes, prompt)
    except Exception as e:
        registrar_evento(
            modulo="creative_agent", accion="guardar_imagen",
            resultado=f"Error guardando: {e}", nivel=NIVEL_ADVERTENCIA,
        )
        return f"Generé la imagen ({proveedor}) pero no pude guardarla en disco, Señor: {e}"

    try:
        os.startfile(ruta_guardado)
    except Exception:
        pass  # No crítico si falla abrir la imagen; ya quedó guardada.

    registrar_evento(
        modulo="creative_agent", accion="generar_imagen",
        resultado=f"Imagen generada ({proveedor}) y guardada en {ruta_guardado}", nivel=NIVEL_INFO,
    )
    return f"Imagen generada y abierta, Señor. Guardada en:\n{ruta_guardado}"

def _generar_imagen_nvidia(prompt: str, api_key: str) -> tuple:
    """
    Devuelve (bytes_imagen, error_o_None). Si error_o_None no es None,
    bytes_imagen es None y el string trae el mensaje para el usuario.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "cfg_scale": 5,
        "aspect_ratio": "1:1",
        "seed": 0,
        "steps": 30,
    }

    try:
        respuesta = requests.post(NVIDIA_IMG_URL, headers=headers, json=payload, timeout=TIMEOUT_SEGUNDOS)
    except requests.RequestException as e:
        return None, f"No pude contactar a NVIDIA NIM, Señor: {e}"

    if respuesta.status_code == 401:
        return None, "Señor, la API key de NVIDIA NIM fue rechazada para el servicio de imágenes."

    if respuesta.status_code != 200:
        registrar_evento(
            modulo="creative_agent", accion="generar_imagen_nvidia",
            resultado=f"HTTP {respuesta.status_code}: {respuesta.text[:300]}",
            nivel=NIVEL_ADVERTENCIA,
        )
        return None, (
            f"NVIDIA NIM devolvió un error (código {respuesta.status_code}), Señor: "
            f"{respuesta.text[:200]}"
        )

    try:
        datos = respuesta.json()
    except Exception:
        return None, "NVIDIA NIM no devolvió una respuesta JSON válida, Señor."
    b64_imagen = datos.get("image") or (datos.get("artifacts") or [{}])[0].get("base64")

    if not b64_imagen:
        registrar_evento(
            modulo="creative_agent", accion="generar_imagen_nvidia",
            resultado=f"Respuesta sin imagen reconocible: {str(datos)[:300]}",
            nivel=NIVEL_ADVERTENCIA,
        )
        return None, "NVIDIA NIM respondió pero no encontré la imagen en el formato esperado, Señor."

    try:
        return base64.b64decode(b64_imagen), None
    except Exception as e:
        return None, f"No pude decodificar la imagen recibida de NVIDIA NIM, Señor: {e}"

def _generar_imagen_huggingface(prompt: str, api_key: str, modelo: str = HF_MODELO_DEFAULT) -> tuple:
    url = HF_INFERENCE_URL.format(modelo=modelo)
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        respuesta = requests.post(url, headers=headers, json={"inputs": prompt}, timeout=TIMEOUT_SEGUNDOS)
    except requests.RequestException as e:
        return None, f"No pude contactar a Hugging Face, Señor: {e}"

    if respuesta.status_code == 503:
        try:
            tiempo_estimado = int(respuesta.json().get("estimated_time", 20))
        except Exception:
            tiempo_estimado = 20
        return None, (
            f"El modelo de imágenes se está inicializando en Hugging Face, Señor "
            f"(~{tiempo_estimado}s). Intente de nuevo en un momento."
        )

    if respuesta.status_code == 401:
        return None, "Señor, la API key de Hugging Face fue rechazada."

    if respuesta.status_code != 200:
        return None, f"Error generando la imagen en Hugging Face, Señor (código {respuesta.status_code})."

    if "image" not in respuesta.headers.get("content-type", ""):
        return None, "Señor, Hugging Face no devolvió una imagen válida."

    return respuesta.content, None

def generar_imagen(prompt: str, api_key_nvidia: str = None, api_key_hf: str = None) -> str:
    if not permitir_accion("creative_agent"):
        return (
            "Señor, alcancé el límite de generación de imágenes en el último minuto. "
            "Espere un momento antes de intentarlo de nuevo."
        )

    if not prompt or not prompt.strip():
        return "Señor, necesito una descripción de qué imagen generar."

    api_key_nvidia = api_key_nvidia or os.getenv("NVIDIA_NIM_API_KEY", "")
    api_key_hf = api_key_hf or os.getenv("HUGGINGFACE_API_KEY", "")

    if not api_key_nvidia and not api_key_hf:
        return (
            "Señor, no tengo ninguna API key configurada para generar imágenes. Con "
            "NVIDIA_NIM_API_KEY (la misma que ya usa el resto de REVAN) basta, no hace "
            "falta una cuenta nueva."
        )

    if api_key_nvidia:
        contenido, error = _generar_imagen_nvidia(prompt, api_key_nvidia)
        if contenido:
            return _finalizar_imagen(contenido, prompt, proveedor="NVIDIA NIM")

        if not api_key_hf:
            registrar_evento(
                modulo="creative_agent", accion="generar_imagen",
                resultado=f"Falló NVIDIA y no hay respaldo de Hugging Face: {error}",
                nivel=NIVEL_ADVERTENCIA,
            )
            return error

    contenido, error = _generar_imagen_huggingface(prompt, api_key_hf)
    if contenido:
        return _finalizar_imagen(contenido, prompt, proveedor="Hugging Face")

    registrar_evento(
        modulo="creative_agent", accion="generar_imagen",
        resultado=f"Fallaron ambos proveedores. Último error: {error}",
        nivel=NIVEL_ADVERTENCIA,
    )
    return error