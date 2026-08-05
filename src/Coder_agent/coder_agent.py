"""
Coder_agent: el módulo de programación de REVAN.

Genera código Python a partir de una descripción en lenguaje natural y lo
ejecuta en el sandbox de src/Security/sandbox.py. Pensado sobre todo para
apoyar con programación del módulo de Electronics (Arduino/ESP32/sensores
vía puerto serial), pero sirve para cualquier tarea de scripting.

REGLA DE AUTONOMÍA (decidida explícitamente, no asumida):
  - Si el código generado NO toca archivos, red, ni hardware (puertos
    serie/USB, GPIO) -> se ejecuta DIRECTO en el sandbox, sin pedir
    confirmación. Es sandbox aislado + timeout + rate limit, ya es
    suficiente fricción invisible para algo de bajo riesgo real.
  - Si el código SÍ toca archivos, red, o hardware -> se pide confirmación
    explícita, mostrando el código completo ANTES de ejecutar nada.

Esto se decide con un análisis estático simple del texto del código (no es
un sandbox perfecto contra código adversario deliberadamente ofuscado),
pero el sandbox subyacente sigue aplicando sus propias protecciones
(timeout, subprocess aislado, sin shell) incluso si la detección de riesgo
se equivoca en algún caso límite.
"""
import re
import os
from openai import OpenAI
from src.Security.sandbox import ejecutar_codigo_python
from src.Security.confirmation import GestorConfirmacion
from src.Security.rate_limiter import permitir_accion
from src.Security.auditoria import registrar_evento, NIVEL_INFO, NIVEL_ADVERTENCIA

_PATRONES_RIESGO = {
    "archivos": [r'\bopen\s*\(', r'\bos\.remove\b', r'\bos\.rmdir\b', r'\bshutil\.', r'\bos\.rename\b', r'\bos\.replace\b'],
    "red": [r'\bsocket\.', r'\brequests\.', r'\burllib\.', r'\bhttp\.client\b', r'\bftplib\b'],
    "hardware (serial/GPIO)": [r'\bserial\.', r'\bSerial\s*\(', r'\bpyserial\b', r'\bsmbus\b', r'\bRPi\.GPIO\b', r'\bboard\.', r'\bbusio\.'],
    "subprocesos": [r'\bsubprocess\.', r'\bos\.system\b', r'\bos\.popen\b'],
}
_gestor_confirmacion_codigo = GestorConfirmacion(ttl_segundos=90)

_SYSTEM_PROMPT_CODER = (
    "Eres el módulo de programación de REVAN, un asistente de IA. Tu trabajo es escribir "
    "código Python funcional y bien comentado para lo que te pida el usuario -sobre todo "
    "apoyo de programación para electrónica (Arduino, ESP32, sensores, comunicación por "
    "puerto serial), pero también scripts y utilidades generales.\n\n"
    "REGLAS:\n"
    "- Responde ÚNICAMENTE con el código Python, sin explicación antes o después, y SIN usar "
    "bloques de markdown (nada de ```python ni ```).\n"
    "- El código debe ser autocontenido y ejecutable tal cual (incluye los imports que "
    "necesite).\n"
    "- Si la tarea requiere hardware (ej. Arduino por puerto serial), usa pyserial "
    "('import serial') y deja un comentario claro indicando que el puerto COM/tty es un "
    "ejemplo y el usuario debe ajustarlo a su equipo.\n"
    "- Comenta el código lo suficiente para que alguien aprendiendo electrónica/programación "
    "pueda seguirlo.\n"
    "- Si la tarea es ambigua, haz la suposición más razonable y coméntala en el código, no "
    "dejes de generar código por pedir aclaraciones.\n"
)


def _limpiar_codigo_generado(texto: str) -> str:
    """Quita los ``` de markdown si el modelo los incluyó a pesar de la instrucción."""
    texto = (texto or "").strip()
    texto = re.sub(r'^```(?:python)?\s*\n?', '', texto)
    texto = re.sub(r'\n?```$', '', texto)
    return texto.strip()


def generar_codigo(descripcion_tarea: str, api_key: str = None,
                    modelo: str = "meta/llama-3.1-70b-instruct") -> str:
    """
    Genera código Python a partir de una descripción en lenguaje natural.
    Usa el mismo endpoint de NVIDIA NIM que el resto de REVAN (NimClient),
    pero con un modelo más grande por defecto (70b en vez del 8b
    conversacional) porque generar código correcto exige más capacidad de
    razonamiento que responder una pregunta casual. Si tu cuenta de NIM no
    tiene acceso al 70b, pasa 'modelo=\"meta/llama-3.1-8b-instruct\"'.
    """
    api_key = api_key or os.getenv("NVIDIA_NIM_API_KEY", "")
    if not api_key:
        raise ValueError("Falta la API key de NVIDIA NIM.")

    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)

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
    """
    Analiza el TEXTO del código (no lo ejecuta) buscando patrones de
    archivos/red/hardware/subprocesos. Devuelve una tupla:
    (necesita_confirmacion: bool, categorias_detectadas: list[str]).
    """
    categorias_detectadas = []
    for categoria, patrones in _PATRONES_RIESGO.items():
        if any(re.search(p, codigo) for p in patrones):
            categorias_detectadas.append(categoria)

    return (len(categorias_detectadas) > 0), categorias_detectadas


def _ejecutar_y_formatear(codigo: str) -> str:
    resultado_sandbox = ejecutar_codigo_python(codigo)
    registrar_evento(
        modulo="coder_agent",
        accion="ejecutar_codigo",
        resultado="éxito" if resultado_sandbox.exito else f"fallo: {resultado_sandbox.error}",
        nivel=NIVEL_INFO if resultado_sandbox.exito else NIVEL_ADVERTENCIA,
    )
    if resultado_sandbox.exito:
        salida = resultado_sandbox.salida.strip() or "(sin salida impresa)"
        return f"Código ejecutado con éxito, Señor. Resultado:\n{salida}"
    return f"El código se ejecutó pero terminó con error, Señor:\n{resultado_sandbox.error}"


def ejecutar_tarea_codigo(descripcion_tarea: str, api_key: str = None) -> str:
    """
    Punto de entrada principal: genera código para la tarea pedida y lo
    ejecuta -directo si es de bajo riesgo, pidiendo confirmación si toca
    archivos, red, o hardware-.
    """
    if not permitir_accion("coder_agent"):
        return (
            "Señor, alcancé el límite de generación de código en el último minuto. "
            "Espere un momento antes de intentarlo de nuevo."
        )

    try:
        codigo = generar_codigo(descripcion_tarea, api_key=api_key)
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
            callback_confirmar=lambda: _ejecutar_y_formatear(codigo),
        )

    return _ejecutar_y_formatear(codigo)

def procesar_confirmacion_codigo(texto_respuesta: str):
    """
    Debe llamarse desde NimClient.generar_respuesta ANTES de procesar
    cualquier otra cosa, igual que ya se hace con procesar_confirmacion()
    de WhatsApp -mismo patrón, pieza de confirmación distinta-.
    """
    return _gestor_confirmacion_codigo.procesar_respuesta(texto_respuesta)