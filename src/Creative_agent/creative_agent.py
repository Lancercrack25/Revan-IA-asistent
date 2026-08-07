"""
Creative_agent: el módulo creativo y conceptual de REVAN.

Diseñado para lluvia de ideas, redacción, generación de historias, diseño
de conceptos o respuestas narrativas/artísticas donde se busca variabilidad
y exploración temática.

OPTIMIZACIÓN DE TOKENS:
  - System prompt condensado al mínimo sin perder directivas clave.
  - Temperatura más alta (0.7) para fomentar variabilidad y creatividad.
  - Guarda automáticamente el contenido generado en 'Escritorio/Creatividad_REVAN'.
"""

import re
import os
import time
import json
from pathlib import Path
from openai import OpenAI, RateLimitError, APIStatusError

from src.Security.rate_limiter import permitir_accion
from src.Security.auditoria import registrar_evento, NIVEL_INFO, NIVEL_ADVERTENCIA


def _cargar_env_desde_config_json():
    """Carga variables desde archivos JSON en 'config' a os.environ."""
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
                                os.environ[clave] = valor
            except Exception:
                pass


_cargar_env_desde_config_json()

# System prompt optimizado al máximo para reducir uso de tokens de entrada
_SYSTEM_PROMPT_CREATIVE = (
    "Eres el módulo creativo de REVAN. Genera ideas, historias, conceptos,imagenes "
    "o textos creativos según la solicitud del usuario. Sé original, conciso y "
    "ve directo al grano sin introducciones innecesarias ni rellenos."
)


def generar_contenido_creativo(descripcion_tarea: str, api_key: str = None,
                               modelo: str = "meta/llama-3.1-70b-instruct") -> str:
    """Invoca la API con una temperatura mayor (0.7) para favorecer la creatividad."""
    _cargar_env_desde_config_json()
    api_key = api_key or os.getenv("GEMINI_API_KEY", "")
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


def _slug_desde_tarea(descripcion_tarea: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', descripcion_tarea.strip().lower())
    return slug.strip('_')[:40] or "creacion"


def guardar_texto_generado(contenido: str, descripcion_tarea: str) -> str:
    """Guarda el texto generado en la carpeta 'Creatividad_REVAN' del Escritorio."""
    from src.Services.os_service import obtener_ruta_escritorio

    carpeta_destino = os.path.join(obtener_ruta_escritorio(), "Creatividad_REVAN")
    os.makedirs(carpeta_destino, exist_ok=True)

    nombre_archivo = f"{_slug_desde_tarea(descripcion_tarea)}_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    ruta_completa = os.path.join(carpeta_destino, nombre_archivo)

    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(contenido)

    return ruta_completa


def ejecutar_tarea_creativa(descripcion_tarea: str, api_key: str = None) -> str:
    """
    Punto de entrada principal para tareas creativas.
    Verifica rate limit, genera contenido, guarda copia local y retorna respuesta.
    """
    if not permitir_accion("creative_agent"):
        return (
            "Señor, alcancé el límite de generación creativa en el último minuto. "
            "Espere un momento antes de intentarlo de nuevo."
        )

    try:
        contenido = generar_contenido_creativo(descripcion_tarea, api_key=api_key)
    except RateLimitError:
        registrar_evento(
            modulo="creative_agent",
            accion="generar_contenido",
            resultado="Límite de solicitudes por minuto alcanzado (429)",
            nivel=NIVEL_ADVERTENCIA,
        )
        return (
            "Señor, alcancé el límite de solicitudes por minuto de la cuenta de NVIDIA NIM. "
            "Espere un momento e intente de nuevo."
        )
    except APIStatusError as e:
        registrar_evento(
            modulo="creative_agent",
            accion="generar_contenido",
            resultado=f"Error API NVIDIA NIM ({e.status_code}): {e}",
            nivel=NIVEL_ADVERTENCIA,
        )
        return f"NVIDIA NIM devolvió un error, Señor (código {e.status_code}): {e}"
    except Exception as e:
        registrar_evento(
            modulo="creative_agent",
            accion="generar_contenido",
            resultado=f"Error generando contenido: {e}",
            nivel=NIVEL_ADVERTENCIA,
        )
        return f"No pude procesar la tarea creativa, Señor: {e}"

    if not contenido:
        return "El modelo no devolvió ningún contenido, Señor. Intente reformular la tarea."

    # Guardar copia en disco
    try:
        ruta_guardado = guardar_texto_generado(contenido, descripcion_tarea)
    except Exception as e:
        ruta_guardado = None
        registrar_evento(
            modulo="creative_agent",
            accion="guardar_texto",
            resultado=f"Error al guardar copia permanente: {e}",
            nivel=NIVEL_ADVERTENCIA,
        )

    registrar_evento(
        modulo="creative_agent",
        accion="contenido_generado",
        resultado=f"Tarea creativa completada para: '{descripcion_tarea[:80]}'",
        nivel=NIVEL_INFO,
    )

    ubicacion = f"\n\n(Guardado en: {ruta_guardado})" if ruta_guardado else ""
    return f"{contenido}{ubicacion}"