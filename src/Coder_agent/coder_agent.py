"""
Coder_agent: El módulo de programación de REVAN (Soporte Multilenguaje).

Genera código en Python, C++, C#, Java, Rust, Go, JS, etc.
  - Python: Se ejecuta en sandbox y se guarda como .py.
  - Lenguajes compilados/web (C++, C#, Rust, JS, etc.): Se guardan con su extensión
    correspondiente en 'Escritorio/Codigos_REVAN/'.
"""
import re
import os
import time
import json
from pathlib import Path
import requests
from src.Security.sandbox import ejecutar_codigo_python
from src.Security.confirmation import GestorConfirmacion
from src.Security.rate_limiter import permitir_accion
from src.Security.auditoria import registrar_evento, NIVEL_INFO, NIVEL_ADVERTENCIA

def _cargar_env_desde_config_json():
    """Carga variables desde la carpeta 'config' asignando las API Keys."""
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

_gestor_confirmacion_codigo = GestorConfirmacion(ttl_segundos=90)

_SYSTEM_PROMPT_CODER = (
    "Eres el módulo Coder de REVAN, un programador experto políglota.\n"
    "REGLAS ESTRICTAS:\n"
    "1. Responde ÚNICAMENTE con el código ejecutable solicitado (Python, C++, C#, Java, Rust, Go, JS, etc.).\n"
    "2. NO agregues explicaciones, ni textos introductorios, ni bloques markdown (sin ```).\n"
    "3. Incluye comentarios claros dentro del código explicando la lógica básica."
    "no hables la ruta de la carpeta ni de la ubicación del archivo, solo entrega el contenido generado."
)

def _obtener_api_key() -> str:
    """Obtiene únicamente la API Key configurada para el Coder Agent."""
    _cargar_env_desde_config_json()
    return os.getenv("CODER_API_KEY", "").strip()

def _limpiar_codigo_generado(texto: str) -> str:
    """Quita envoltorios de markdown si el modelo los incluyó por error."""
    texto = (texto or "").strip()
    texto = re.sub(r'^```(?:python|cpp|c\+\+|cs|csharp|java|rust|go|javascript|js|html|php|ino)?\s*\n?', '', texto)
    texto = re.sub(r'\n?```$', '', texto)
    return texto.strip()

def generar_codigo(descripcion_tarea: str, api_key: str = None,
                   modelo: str = "meta/llama-3.1-8b-instruct") -> str:
    """Genera código mediante llamada REST limpia usando Llama 3.3 70B Instruct."""
    api_key = api_key or _obtener_api_key()
    if not api_key:
        raise ValueError("Falta la 'CODER_API_KEY' en el archivo de configuración JSON.")

    # ✅ URL CORREGIDA Y LIMPIA
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT_CODER},
            {"role": "user", "content": descripcion_tarea}
        ],
        "temperature": 0.2,
        "max_tokens": 2000
    }

    response = requests.post(url, headers=headers, json=payload, timeout=40)

    if response.status_code == 200:
        datos = response.json()
        codigo = datos["choices"][0]["message"]["content"]
        return _limpiar_codigo_generado(codigo)
    else:
        raise Exception(f"Error HTTP {response.status_code}: {response.text}")

def detectar_formato(codigo: str):
    """Determina la sintaxis y extensión adecuada para el lenguaje generado."""
    c_str = codigo.lower()
    
    # Arduino / ESP32
    if "void setup()" in c_str and "void loop()" in c_str:
        return "Arduino C++", ".ino"
    # C# (.NET)
    elif "using system;" in c_str or "namespace " in c_str or "console.writeline" in c_str:
        return "C#", ".cs"
    # C++ Estándar
    elif "#include <iostream>" in c_str or "std::cout" in c_str or "int main(" in c_str:
        return "C++", ".cpp"
    # Java
    elif "public class " in c_str or "system.out.println" in c_str:
        return "Java", ".java"
    # Rust
    elif "fn main()" in c_str or "println!" in c_str:
        return "Rust", ".rs"
    # Go
    elif "package main" in c_str or "fmt.println" in c_str:
        return "Go", ".go"
    # JavaScript / Node.js
    elif "console.log(" in c_str or "const " in c_str or "function " in c_str:
        return "JavaScript", ".js"
    # HTML / Web
    elif "<!doctype html>" in c_str or "<html" in c_str:
        return "HTML", ".html"
    
    # Por defecto, se asume Python
    return "Python", ".py"

def detectar_riesgo(codigo: str):
    """Analiza el código Python buscando operaciones sensibles."""
    categorias_detectadas = []
    for categoria, patrones in _PATRONES_RIESGO.items():
        if any(re.search(p, codigo) for p in patrones):
            categorias_detectadas.append(categoria)

    return (len(categorias_detectadas) > 0), categorias_detectadas

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

    lenguaje, extension = detectar_formato(codigo)

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

    # Si es cualquier lenguaje distinto a Python, se guarda y se le notifica al usuario
    if lenguaje != "Python":
        registrar_evento(
            modulo="coder_agent",
            accion="codigo_generado",
            resultado=f"Código {lenguaje} generado para: '{descripcion_tarea[:80]}'",
            nivel=NIVEL_INFO,
        )
        ubicacion = f"\n{ruta_guardado}" if ruta_guardado else ""
        return (
            f"Señor, generé el programa en **{lenguaje}** y lo guardé en:{ubicacion}\n\n"
            f"Puede compilarlo o ejecutarlo con su entorno habitual de {lenguaje}."
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