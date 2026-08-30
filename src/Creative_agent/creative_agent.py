"""
Creative_agent: El módulo creativo y conceptual de REVAN.

Capacidades:
  1. Generación de texto creativo (historias, descripciones, lluvia de ideas).
  2. Generación de imágenes (intentando NVIDIA NIM API de SD3 con Fallback
     automático a motor de reserva para evitar errores 404/Not Found).

Guarda automáticamente las salidas en 'Escritorio/Creatividad_REVAN'.
"""

import re
import os
import time
import json
import base64
from pathlib import Path
import requests
from openai import OpenAI, RateLimitError, APIStatusError

from src.Security.rate_limiter import permitir_accion
from src.Security.auditoria import registrar_evento, NIVEL_INFO, NIVEL_ADVERTENCIA


def _cargar_env_desde_config_json():
    """Carga variables desde archivos JSON situados en 'config' hacia os.environ."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    carpeta_config = base_dir / "config"
    
    if carpeta_config.exists() and carpeta_config.is_dir():
        for archivo in carpeta_config.glob("*.json"):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                    if isinstance(datos, dict):
                        for clave, valor in datos.items():
                            if valor and isinstance(valor, str):
                                os.environ[clave] = valor.strip()
            except Exception:
                pass

_cargar_env_desde_config_json()
_SYSTEM_PROMPT_CREATIVE = (
    "Eres el módulo creativo de REVAN. Genera ideas, historias, conceptos "
    "o textos creativos según la solicitud del usuario. Sé original, conciso y "
    "ve directo al grano sin introducciones innecesarias ni rellenos."
    "no hables la ruta de la carpeta ni de la ubicación del archivo, solo entrega el contenido generado."
)

def generar_contenido_creativo(descripcion_tarea: str, api_key: str = None,
                               modelo: str = "meta/llama-3.1-70b-instruct") -> str:
    """Genera texto creativo consumiendo el mínimo de tokens."""
    _cargar_env_desde_config_json()
    api_key = api_key or os.getenv("NVIDIA_NIM_API_KEY", "")
    if not api_key:
        raise ValueError("Falta la API key de NVIDIA NIM en la configuración.")

    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)

    respuesta = client.chat.completions.create(
        model=modelo,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT_CREATIVE},
            {"role": "user", "content": descripcion_tarea},
        ],
        temperature=0.7,
        max_tokens=1500,
    )

    return (respuesta.choices[0].message.content or "").strip()

def _generar_imagen_nvidia(prompt_imagen: str, api_key: str) -> str:
    """Intenta generar la imagen utilizando el endpoint de NVIDIA NIM (SD3)."""
    url = "https://ai.api.nvidia.com/v1/genai/stabilityai/stable-diffusion-3-medium"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt_imagen,
        "mode": "text-to-image",
        "aspect_ratio": "1:1",
        "model": "sd3",
        "output_format": "jpeg"
    }

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    
    if response.status_code == 200:
        datos = response.json()
        image_b64 = datos.get("image") or (datos.get("artifacts", [{}])[0].get("base64") if datos.get("artifacts") else None)
        if image_b64:
            return image_b64

    raise Exception(f"HTTP {response.status_code}: {response.text}")

def _generar_imagen_fallback(prompt_imagen: str) -> bytes:
    """Motor de respaldo instantáneo cuando la API de NVIDIA no tiene activa la función."""
    prompt_encoded = requests.utils.quote(prompt_imagen)
    url_fallback = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=1024&nologo=true&seed=42"
    
    resp = requests.get(url_fallback, timeout=40)
    if resp.status_code == 200 and len(resp.content) > 1000:
        return resp.content
    raise Exception(f"Fallback HTTP {resp.status_code}")

def generar_imagen(prompt_imagen: str, api_key: str = None) -> str:
    if not permitir_accion("creative_agent"):
        return "Señor, alcancé el límite de generación creativa en el último minuto."

    _cargar_env_desde_config_json()
    api_key = api_key or os.getenv("CREATIVE_API_KEY", "")
    
    # Limpiar el prompt de comandos comunes como "revan crea una imagen de..."
    prompt_limpio = re.sub(r'^(revan\s+)?(crea|genera|dibuja)\s+(una\s+imagen\s+de|un\s+dibujo\s+de|imagen\s+de)\s*', '', prompt_imagen, flags=re.IGNORECASE).strip()
    if not prompt_limpio:
        prompt_limpio = prompt_imagen

    contenido_bytes = None
    metodo_usado = ""
    # Intento 1: NVIDIA NIM
    if api_key:
        try:
            image_b64 = _generar_imagen_nvidia(prompt_limpio, api_key)
            contenido_bytes = base64.b64decode(image_b64)
            metodo_usado = "NVIDIA NIM (Stable Diffusion 3)"
        except Exception as e:
            registrar_evento(
                modulo="creative_agent",
                accion="generar_imagen_nvidia_failed",
                resultado=f"Fallo NVIDIA API ({e}). Usando motor de respaldo...",
                nivel=NIVEL_ADVERTENCIA,
            )
    # Intento 2: Fallback (si el intento 1 falló o no había API Key)
    if not contenido_bytes:
        try:
            contenido_bytes = _generar_imagen_fallback(prompt_limpio)
            metodo_usado = "Engine Respaldo (Pollinations AI)"
        except Exception as e:
            registrar_evento(
                modulo="creative_agent",
                accion="generar_imagen_fallback_failed",
                resultado=f"Error en fallback: {e}",
                nivel=NIVEL_ADVERTENCIA,
            )
            return f"Señor, no fue posible sintetizar la imagen en este momento: {e}"
    # Guardar en disco
    try:
        ruta_guardado = guardar_bytes_imagen(contenido_bytes, prompt_limpio)
        registrar_evento(
            modulo="creative_agent",
            accion="generar_imagen",
            resultado=f"Imagen generada con {metodo_usado} para '{prompt_limpio[:40]}'",
            nivel=NIVEL_INFO,
        )
        return f"Señor, la imagen de '{prompt_limpio}' fue sintetizada con éxito [{metodo_usado}] y guardada en:\n{ruta_guardado}"
    except Exception as e:
        return f"La imagen se generó pero hubo un error al guardar en disco: {e}"

def _slug_desde_tarea(descripcion_tarea: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', descripcion_tarea.strip().lower())
    return slug.strip('_')[:40] or "creacion"


def guardar_texto_generado(contenido: str, descripcion_tarea: str) -> str:
    from src.Services.os_service import obtener_ruta_escritorio

    carpeta_destino = os.path.join(obtener_ruta_escritorio(), "Creatividad_REVAN")
    os.makedirs(carpeta_destino, exist_ok=True)

    nombre_archivo = f"{_slug_desde_tarea(descripcion_tarea)}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    ruta_completa = os.path.join(carpeta_destino, nombre_archivo)

    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(contenido)

    return ruta_completa

def guardar_bytes_imagen(contenido_bytes: bytes, prompt_imagen: str) -> str:
    """Guarda directamente los bytes de la imagen en formato PNG/JPG en el Escritorio."""
    from src.Services.os_service import obtener_ruta_escritorio

    carpeta_destino = os.path.join(obtener_ruta_escritorio(), "Creatividad_REVAN")
    os.makedirs(carpeta_destino, exist_ok=True)

    nombre_archivo = f"img_{_slug_desde_tarea(prompt_imagen)}_{time.strftime('%Y%m%d_%H%M%S')}.png"
    ruta_completa = os.path.join(carpeta_destino, nombre_archivo)

    with open(ruta_completa, "wb") as f:
        f.write(contenido_bytes)

    return ruta_completa

def ejecutar_tarea_creativa(descripcion_tarea: str, api_key: str = None) -> str:
    """Punto de entrada principal para tareas creativas de texto."""
    if not permitir_accion("creative_agent"):
        return "Señor, alcancé el límite de generación creativa en el último minuto."

    try:
        contenido = generar_contenido_creativo(descripcion_tarea, api_key=api_key)
    except RateLimitError:
        return "Señor, alcancé el límite de solicitudes por minuto de NVIDIA NIM."
    except APIStatusError as e:
        return f"NVIDIA NIM devolvió un error, Señor (código {e.status_code}): {e}"
    except Exception as e:
        return f"No pude procesar la tarea creativa, Señor: {e}"

    if not contenido:
        return "El modelo no devolvió ningún contenido, Señor."

    try:
        ruta_guardado = guardar_texto_generado(contenido, descripcion_tarea)
    except Exception:
        ruta_guardado = None
    ubicacion = f"\n\n(Guardado en: {ruta_guardado})" if ruta_guardado else ""
    return f"{contenido}{ubicacion}"