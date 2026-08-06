"""
Coder_agent: el módulo de programación de REVAN.

Genera código a partir de una descripción en lenguaje natural y lo
ejecuta en el sandbox de src/Security/sandbox.py (solo si es Python).
Pensado sobre todo para apoyar con programación del módulo de
Electronics (Arduino/ESP32/sensores), pero sirve para cualquier tarea de
scripting.

DOS FORMATOS POSIBLES, detectados automáticamente sobre el código YA
GENERADO (no se le pregunta al modelo qué generó, se verifica el
resultado real):
  - Python: se ejecuta en el sandbox (con confirmación condicional, ver
    abajo) y además se guarda una copia permanente.
  - Arduino C++ (firmware real para la placa, con setup()/loop()): NO se
    ejecuta -eso correría en esta PC, no en el microcontrolador, no tiene
    sentido intentarlo-. Se guarda como .ino y se le dice al usuario que
    lo abra con el IDE de Arduino para subirlo a la placa.

ALMACENAMIENTO PERMANENTE:
  Todo código generado -se ejecute o no, sea Python o Arduino- se guarda
  en una carpeta fija en el Escritorio: 'Codigos_REVAN'. Antes, el código
  que corría en el sandbox vivía en una carpeta temporal que se borraba
  automáticamente al terminar -no quedaba ningún rastro después-.

REGLA DE AUTONOMÍA para código Python (decidida explícitamente):
  - Si NO toca archivos, red, ni hardware (puertos serie/USB, GPIO) ->
    se ejecuta DIRECTO en el sandbox, sin pedir confirmación.
  - Si SÍ toca archivos, red, o hardware -> se pide confirmación
    explícita, mostrando el código completo ANTES de ejecutar nada.

Esto se decide con un análisis estático simple del texto del código (no
es un sandbox perfecto contra código adversario deliberadamente
ofuscado), pero el sandbox subyacente sigue aplicando sus propias
protecciones (timeout, subprocess aislado, sin shell) incluso si la
detección de riesgo se equivoca en algún caso límite.
"""

import re
import os
import time
from openai import OpenAI, RateLimitError, APIStatusError

from src.Security.sandbox import ejecutar_codigo_python
from src.Security.confirmation import GestorConfirmacion
from src.Security.rate_limiter import permitir_accion
from src.Security.auditoria import registrar_evento, NIVEL_INFO, NIVEL_ADVERTENCIA

# Patrones que, si aparecen en código PYTHON, lo marcan como "toca
# archivos/red/hardware" -> requiere confirmación antes de ejecutarse.
_PATRONES_RIESGO = {
    "archivos": [r'\bopen\s*\(', r'\bos\.remove\b', r'\bos\.rmdir\b', r'\bshutil\.', r'\bos\.rename\b', r'\bos\.replace\b'],
    "red": [r'\bsocket\.', r'\brequests\.', r'\burllib\.', r'\bhttp\.client\b', r'\bftplib\b'],
    "hardware (serial/GPIO)": [r'\bserial\.', r'\bSerial\s*\(', r'\bpyserial\b', r'\bsmbus\b', r'\bRPi\.GPIO\b', r'\bboard\.', r'\bbusio\.'],
    "subprocesos": [r'\bsubprocess\.', r'\bos\.system\b', r'\bos\.popen\b'],
}

# Firma típica de un sketch de Arduino/ESP32: ambas funciones son
# obligatorias en todo sketch válido, así que su presencia conjunta es
# una señal confiable de que el código es C++ para un microcontrolador,
# no Python.
_PATRON_ARDUINO = (re.compile(r'\bvoid\s+setup\s*\('), re.compile(r'\bvoid\s+loop\s*\('))

# Confirmación con TTL más largo que WhatsApp (90s en vez de 60s): revisar
# código toma más tiempo que decidir si mandar un mensaje.
_gestor_confirmacion_codigo = GestorConfirmacion(ttl_segundos=90)

_SYSTEM_PROMPT_CODER = (
    "Eres el módulo de programación de REVAN, un asistente de IA. Tu trabajo es escribir "
    "código funcional y bien comentado para lo que te pida el usuario -sobre todo apoyo de "
    "programación para electrónica (Arduino, ESP32, sensores), pero también scripts y "
    "utilidades generales en Python.\n\n"
    "REGLAS:\n"
    "- Responde ÚNICAMENTE con el código, sin explicación antes o después, y SIN usar bloques "
    "de markdown (nada de ```python, ```cpp, ni ```).\n"
    "- El código debe ser autocontenido y ejecutable/compilable tal cual (incluye los imports "
    "o #include que necesite).\n"
    "- MUY IMPORTANTE: si la tarea es el FIRMWARE que corre directamente en una placa "
    "Arduino/ESP32 (el sketch en sí, lo que se sube a la placa), escribe código Arduino en "
    "C++ con la estructura estándar setup()/loop() -NO Python, un sketch real no es Python-. "
    "Si en cambio la tarea es un script que corre en la PC y se comunica con una placa YA "
    "programada por puerto serial, entonces sí escribe Python usando pyserial "
    "('import serial').\n"
    "- Si usas pines, valores de calibración, o el puerto COM/tty, dejalos como constantes "
    "comentadas al inicio del código, indicando claramente que son ejemplos a ajustar.\n"
    "- Comenta el código lo suficiente para que alguien aprendiendo electrónica/programación "
    "pueda seguirlo.\n"
    "- Si la tarea es ambigua, haz la suposición más razonable y coméntala en el código, no "
    "dejes de generar código por pedir aclaraciones.\n"
)


def _limpiar_codigo_generado(texto: str) -> str:
    """Quita los ``` de markdown si el modelo los incluyó a pesar de la instrucción."""
    texto = (texto or "").strip()
    texto = re.sub(r'^```(?:python|cpp|c\+\+|ino)?\s*\n?', '', texto)
    texto = re.sub(r'\n?```$', '', texto)
    return texto.strip()


def generar_codigo(descripcion_tarea: str, api_key: str = None,
                    modelo: str = "meta/llama-3.1-70b-instruct") -> str:
    """
    Genera código a partir de una descripción en lenguaje natural (Python
    o Arduino C++, según lo que pida la tarea -ver _SYSTEM_PROMPT_CODER-).
    Usa el mismo endpoint de NVIDIA NIM que el resto de REVAN (NimClient),
    pero con un modelo más grande por defecto (70b en vez del 8b
    conversacional) porque generar código correcto exige más capacidad de
    razonamiento que responder una pregunta casual. Si tu cuenta de NIM no
    tiene acceso al 70b, pasa 'modelo="meta/llama-3.1-8b-instruct"'.
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
    Analiza el TEXTO del código Python (no lo ejecuta) buscando patrones
    de archivos/red/hardware/subprocesos. Devuelve una tupla:
    (necesita_confirmacion: bool, categorias_detectadas: list[str]).
    """
    categorias_detectadas = []
    for categoria, patrones in _PATRONES_RIESGO.items():
        if any(re.search(p, codigo) for p in patrones):
            categorias_detectadas.append(categoria)

    return (len(categorias_detectadas) > 0), categorias_detectadas


def detectar_formato(codigo: str):
    """
    Heurística sobre el código YA GENERADO (más confiable que adivinar
    por la descripción de la tarea): si tiene la firma típica de un
    sketch de Arduino (setup()/loop()), se trata como Arduino C++.
    Cualquier otra cosa se asume Python. Devuelve (formato, extension).
    """
    patron_setup, patron_loop = _PATRON_ARDUINO
    if patron_setup.search(codigo) and patron_loop.search(codigo):
        return "arduino_cpp", ".ino"
    return "python", ".py"


def _slug_desde_tarea(descripcion_tarea: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9]+', '_', descripcion_tarea.strip().lower())
    return slug.strip('_')[:40] or "tarea"


def guardar_codigo_generado(codigo: str, descripcion_tarea: str, extension: str) -> str:
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
    """
    Punto de entrada principal: genera código para la tarea pedida,
    SIEMPRE guarda una copia permanente, y:
      - si es Arduino C++: no lo ejecuta (no tiene sentido en esta PC),
        solo avisa dónde quedó guardado para subirlo con el IDE de Arduino.
      - si es Python de bajo riesgo: se ejecuta directo en el sandbox.
      - si es Python que toca archivos/red/hardware: pide confirmación
        antes de ejecutar.
    """
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
            resultado="Límite de solicitudes por minuto de la cuenta de NVIDIA alcanzado (429)",
            nivel=NIVEL_ADVERTENCIA,
        )
        return (
            "Señor, alcancé el límite de solicitudes por minuto de la cuenta de NVIDIA NIM "
            "-se comparte entre el chat, la generación de código y de imágenes-. Espere un "
            "momento e intente de nuevo."
        )
    except APIStatusError as e:
        registrar_evento(
            modulo="coder_agent",
            accion="generar_codigo",
            resultado=f"Error de la API de NVIDIA NIM (código {e.status_code}): {e}",
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
        ubicacion = f"\n{ruta_guardado}" if ruta_guardado else " (no se pudo guardar en disco, revise permisos)"
        return (
            f"Señor, escribí el sketch de Arduino y lo guardé en:{ubicacion}\n\n"
            f"Ábralo con el IDE de Arduino para compilarlo y subirlo a la placa -no lo "
            f"ejecuté aquí, eso requiere el hardware conectado y el IDE-."
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
    """
    Debe llamarse desde NimClient.generar_respuesta ANTES de procesar
    cualquier otra cosa, igual que ya se hace con procesar_confirmacion()
    de WhatsApp -mismo patrón, pieza de confirmación distinta-.
    """
    return _gestor_confirmacion_codigo.procesar_respuesta(texto_respuesta)