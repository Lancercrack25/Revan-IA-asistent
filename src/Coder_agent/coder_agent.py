"""
Coder_agent: el módulo de programación de REVAN.

Genera código a partir de una descripción en lenguaje natural y lo
ejecuta en el sandbox de src/Security/sandbox.py (solo si es Python).
Pensado sobre todo para apoyar con programación del módulo de
Electronics (Arduino/ESP32/sensores), pero sirve para cualquier tarea de
scripting.

FORMATOS:
  - Python: se ejecuta en el sandbox (con confirmación condicional si toca
    red/archivos/hardware) y se guarda una copia en 'Escritorio/Codigos_REVAN'.
  - Arduino C++: se guarda como .ino para compilarlo desde el IDE (no se ejecuta localmente).

OPTIMIZACIÓN DE TOKENS:
  - System prompt condensado al mínimo necesario.
  - Temperatura baja (0.2) para precisión lógica y sintáctica.
"""

import re
import os
import time
import json
from pathlib import Path
from openai import OpenAI, RateLimitError, APIStatusError

from src.Security.sandbox import ejecutar_codigo_python
from src.Security.confirmation import GestorConfirmacion
from src.Security.rate_limiter import permitir_accion
from src.Security.auditoria import registrar_evento, NIVEL_INFO, NIVEL_ADVERTENCIA


def _cargar_env_desde_config_json():
    """Carga variables desde la carpeta 'config' asignando NVIDIA_NIM_API_KEY."""
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

_PATRONES_RIESGO = {
    "archivos": [r'\bopen\s*\(', r'\bos\.remove\b', r'\bos\.rmdir\b', r'\bshutil\.', r'\bos\.rename\b', r'\bos\.replace\b'],
    "red": [r'\bsocket\.', r'\brequests\.', r'\burllib\.', r'\bhttp\.client\b', r'\bftplib\b'],
    "hardware (serial/GPIO)": [r'\bserial\.', r'\bSerial\s*\(', r'\bpyserial\b', r'\bsmbus\b', r'\bRPi\.GPIO\b', r'\bboard\.', r'\bbusio\.'],
    "subprocesos": [r'\bsubprocess\.', r'\bos\.system\b', r'\bos\.popen\b'],
}

_PATRON_ARDUINO = (re.compile(r'\bvoid\s+setup\s*\('), re.compile(r'\bvoid\s+loop\s*\('))
_gestor_confirmacion_codigo = GestorConfirmacion(ttl_segundos=90)

# System prompt optimizado para consumir el mínimo de tokens posible
_SYSTEM_PROMPT_CODER = (
    "Eres el módulo Coder de REVAN. Genera código funcional y bien comentado.\n"
    "REGLAS:\n"
    "1. Responde ÚNICAMENTE con código ejecutable. NO agregues explicaciones ni bloques markdown (sin ```).\n"
    "2. Si es firmware para microcontroladores (Arduino/ESP32), usa C++ con setup()/loop(). Si es script para PC, usa Python.\n"
    "3. Declara pines, puertos y constantes ajustables al inicio como comentarios."
)


def _limpiar_codigo_generado(texto: str) -> str:
    """Quita envoltorios de markdown si el modelo los incluyó."""
    texto = (texto or "").strip()
    texto = re.sub(r'^```(?:python|cpp|c\+\+|ino)?\s*\n?', '', texto)
    texto = re.sub(r'\n?```$', '', texto)
    return texto.strip()


def generar_codigo(descripcion_tarea: str, api_key: str = None,
                   modelo: str = "meta/llama-3.1-70b-instruct") -> str:
    _cargar_env_desde_config_json()
    # Este agente consulta prioritariamente 'NVIDIA_NIM_API_KEY'
    api_key = api_key or os.getenv("NVIDIA_NIM_API_KEY", "")
    if not api_key:
        raise ValueError("Falta la API key de NVIDIA NIM en la configuración.")

    client = OpenAI(base_url="[https://integrate.api.nvidia.com/v1](https://integrate.api.nvidia.com/v1)", api_key=api_key)

    respuesta = client.chat.completions.create(
        model=modelo,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT_CODER},
            {"role": "user", "content": descripcion_tarea},
        ],
        temperature=0.2,
        max_tokens=1500,
    )

    codigo = respuesta.choices[0].message.content or ""
    return _limpiar_codigo_generado(codigo)


def detectar_riesgo(codigo: str):
    """Analiza el código Python buscando operaciones sensibles."""
    categorias_detectadas = []
    for categoria, patrones in _PATRONES_RIESGO.items():
        if any(re.search(p, codigo) for p in patrones):
            categorias_detectadas.append(categoria)

    return (len(categorias_detectadas) > 0), categorias_detectadas


def detectar_formato(codigo: str):
    """Determina si el código generado es Arduino C++ o Python."""
    patron_setup, patron_loop = _PATRON_ARDUINO
    if patron_setup.search(codigo) and patron_loop.search(codigo):
        return "arduino_cpp", ".ino"
    return "python", ".py"


def _slug_desde_tarea(descripcion_tarea: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', descripcion_tarea.strip().lower())
    return slug.strip('_')[:40] or "tarea"


def guardar_codigo_generado(codigo: str, descripcion_tarea: str, extension: str) -> str:
    """Guarda copia permanente en Escritorio/Codigos_REVAN."""
    from src.Services.os_service import obtener_ruta_escritorio

    carpeta_codigos = os.path.join(obtener_ruta_escritorio(), "Codigos_REVAN")
    os.makedirs(carpeta_codigos, exist_ok=True)

    nombre_archivo = f"{_slug_desde_tarea(descripcion_tarea)}_{time.strftime('%Y%m%d_%H%M%S')}{extension}"
    ruta_completa = os.path.join(carpeta_codigos, nombre_archivo)

    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(codigo)

    return ruta_completa


def _ejecutar_y_formatear(codigo: str, ruta_guardado: str) -> str:
    resultado_sandbox = ejecutar_codigo_python(codigo)
    registrar_evento(
        modulo="coder_agent",
        accion="ejecutar_codigo",
        resultado="éxito" if resultado_sandbox.exito else f"fallo: {resultado_sandbox.error}",
        nivel=NIVEL_INFO if resultado_sandbox.exito else NIVEL_ADVERTENCIA,
    )
    ubicacion = f"\n\nGuardado en: {ruta_guardado}" if ruta_guardado else ""
    if resultado_sandbox.exito:
        salida = resultado_sandbox.salida.strip() or "(sin salida impresa)"
        return f"Código ejecutado con éxito, Señor. Resultado:\n{salida}{ubicacion}"
    return f"El código se ejecutó pero terminó con error, Señor:\n{resultado_sandbox.error}{ubicacion}"


def ejecutar_tarea_codigo(descripcion_tarea: str, api_key: str = None) -> str:
    """Punto de entrada principal para la generación y ejecución de código."""
    if not permitir_accion("coder_agent"):
        return (
            "Señor, alcancé el límite de generación de código en el último minuto. "
            "Espere un momento antes de intentarlo de nuevo."
        )

    try:
        codigo = generar_codigo(descripcion_tarea, api_key=api_key)
    except RateLimitError:
        registrar_evento(
            modulo="coder_agent",
            accion="generar_codigo",
            resultado="Límite de solicitudes por minuto alcanzado (429)",
            nivel=NIVEL_ADVERTENCIA,
        )
        return (
            "Señor, alcancé el límite de solicitudes por minuto de la cuenta de NVIDIA NIM. "
            "Espere un momento e intente de nuevo."
        )
    except APIStatusError as e:
        registrar_evento(
            modulo="coder_agent",
            accion="generar_codigo",
            resultado=f"Error API NVIDIA NIM ({e.status_code}): {e}",
            nivel=NIVEL_ADVERTENCIA,
        )
        return f"NVIDIA NIM devolvió un error, Señor (código {e.status_code}): {e}"
    except Exception as e:
        registrar_evento(
            modulo="coder_agent",
            accion="generar_codigo",
            resultado=f"Error generando código: {e}",
            nivel=NIVEL_ADVERTENCIA,
        )
        return f"No pude generar el código, Señor: {e}"

    if not codigo.strip():
        return "El modelo no devolvió código utilizable, Señor. Intente reformular la tarea."

    formato, extension = detectar_formato(codigo)

    try:
        ruta_guardado = guardar_codigo_generado(codigo, descripcion_tarea, extension)
    except Exception as e:
        ruta_guardado = None
        registrar_evento(
            modulo="coder_agent",
            accion="guardar_codigo",
            resultado=f"No se pudo guardar la copia permanente: {e}",
            nivel=NIVEL_ADVERTENCIA,
        )

    if formato == "arduino_cpp":
        registrar_evento(
            modulo="coder_agent",
            accion="codigo_generado",
            resultado=f"Sketch Arduino generado para: '{descripcion_tarea[:80]}'",
            nivel=NIVEL_INFO,
        )
        ubicacion = f"\n{ruta_guardado}" if ruta_guardado else " (no se pudo guardar en disco)"
        return (
            f"Señor, escribí el sketch de Arduino y lo guardé en:{ubicacion}\n\n"
            f"Ábralo con el IDE de Arduino para compilarlo y subirlo a la placa."
        )

    necesita_confirmacion, categorias = detectar_riesgo(codigo)

    registrar_evento(
        modulo="coder_agent",
        accion="codigo_generado",
        resultado=f"Tarea: '{descripcion_tarea[:80]}' | Riesgo detectado: {categorias or 'ninguno'}",
        nivel=NIVEL_INFO,
    )

    if necesita_confirmacion:
        etiquetas = ", ".join(categorias)
        descripcion_para_confirmar = (
            f"ejecutar código que toca {etiquetas}. Aquí está completo:\n\n{codigo}"
        )
        return _gestor_confirmacion_codigo.solicitar(
            descripcion=descripcion_para_confirmar,
            callback_confirmar=lambda: _ejecutar_y_formatear(codigo, ruta_guardado),
        )
    
    return _ejecutar_y_formatear(codigo, ruta_guardado)


def procesar_confirmacion_codigo(texto_respuesta: str):
    return _gestor_confirmacion_codigo.procesar_respuesta(texto_respuesta)