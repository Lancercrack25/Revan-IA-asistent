"""
Sandbox de ejecución para código/comandos generados por IA — pensado
específicamente para cuando implementes Coder_agent.

Esto NO es un sandbox de nivel-contenedor (para eso se necesitaría Docker
o una VM); es la línea base mínima antes de dejar que un LLM ejecute algo
en tu equipo:

  - Nunca usa shell=True. Todo se ejecuta con subprocess y listas de
    argumentos, nunca con un string interpolado.
  - Timeout obligatorio en toda ejecución: nada de procesos colgados ni
    loops infinitos generados por el modelo.
  - El código Python se corre como SUBPROCESO independiente, nunca con
    exec()/eval() dentro del proceso de REVAN — así un error o algo
    malicioso en el código generado no puede tocar la memoria ni el
    estado del asistente principal.
  - El script vive en un directorio temporal exclusivo que se borra al
    terminar, para no dejar residuos ni permitir que el código toque el
    resto del sistema de archivos por accidente.
  - Cualquier argumento externo pasa por el validador de
    src/Security/sanitizador.py antes de construir el comando.

Recomendación para cuando integres Coder_agent: antes de llamar a
ejecutar_codigo_python(), pasa el código generado por el modelo por
GestorConfirmacion (src/Security/confirmacion.py) para que el usuario
apruebe explícitamente qué se va a correr.
"""

import os
import subprocess
import tempfile
import shutil
import uuid

from src.Security.sanitizador import sanitizar_o_rechazar, EntradaNoSeguraError
from src.Security.auditoria import registrar_evento, NIVEL_INFO, NIVEL_ADVERTENCIA, NIVEL_CRITICO

TIMEOUT_SEGUNDOS_DEFAULT = 15
LIMITE_SALIDA_CARACTERES = 4000

# Lista blanca de ejecutables permitidos en ejecutar_comando_sistema. Esto es
# MÁS estricto que solo filtrar caracteres peligrosos (sanitizador.py): en
# vez de "prohíbo lo que reconozco como malo", es "permito solo lo que
# reconozco como necesario". Para algo que va a ejecutar comandos elegidos
# por un LLM (Coder_agent), lista blanca es bastante más seguro que lista
# negra. Amplía esta lista solo con lo que realmente vayas a necesitar.
COMANDOS_PERMITIDOS = {
    "git", "python", "python3", "pip", "pip3", "node", "npm", "npx",
}


class ResultadoSandbox:
    def __init__(self, exito: bool, salida: str, error: str, codigo_salida: int):
        self.exito = exito
        self.salida = salida
        self.error = error
        self.codigo_salida = codigo_salida

    def __str__(self) -> str:
        if self.exito:
            return self.salida or "(el script se ejecutó sin salida)"
        return f"Error (código {self.codigo_salida}): {self.error}"


def ejecutar_codigo_python(codigo: str, timeout_segundos: int = TIMEOUT_SEGUNDOS_DEFAULT) -> ResultadoSandbox:
    """
    Ejecuta un fragmento de código Python en un subproceso aislado dentro
    de un directorio temporal exclusivo (que se borra al terminar, exista
    o no error), con timeout obligatorio.
    """
    if not codigo or not codigo.strip():
        return ResultadoSandbox(False, "", "No se proporcionó código para ejecutar.", -1)

    directorio_temporal = tempfile.mkdtemp(prefix="revan_sandbox_")
    ruta_script = os.path.join(directorio_temporal, f"script_{uuid.uuid4().hex[:8]}.py")

    try:
        with open(ruta_script, "w", encoding="utf-8") as f:
            f.write(codigo)

        proceso = subprocess.run(
            ["python", ruta_script],
            cwd=directorio_temporal,
            capture_output=True,
            text=True,
            timeout=timeout_segundos,
            shell=False,
        )

        resultado = ResultadoSandbox(
            exito=(proceso.returncode == 0),
            salida=(proceso.stdout or "")[:LIMITE_SALIDA_CARACTERES],
            error=(proceso.stderr or "")[:LIMITE_SALIDA_CARACTERES],
            codigo_salida=proceso.returncode,
        )
        registrar_evento(
            modulo="sandbox",
            accion="ejecutar_codigo_python",
            resultado="éxito" if resultado.exito else f"fallo (código {resultado.codigo_salida})",
            nivel=NIVEL_INFO if resultado.exito else NIVEL_ADVERTENCIA,
            detalles={"longitud_codigo": len(codigo)},
        )
        return resultado

    except subprocess.TimeoutExpired:
        registrar_evento(
            modulo="sandbox",
            accion="ejecutar_codigo_python",
            resultado=f"timeout tras {timeout_segundos}s",
            nivel=NIVEL_ADVERTENCIA,
        )
        return ResultadoSandbox(
            False, "",
            f"El script excedió el límite de {timeout_segundos} segundos y fue detenido.",
            -1,
        )
    except Exception as e:
        registrar_evento(
            modulo="sandbox",
            accion="ejecutar_codigo_python",
            resultado=f"excepción: {e}",
            nivel=NIVEL_CRITICO,
        )
        return ResultadoSandbox(False, "", f"Error al ejecutar el sandbox: {e}", -1)
    finally:
        shutil.rmtree(directorio_temporal, ignore_errors=True)


def ejecutar_comando_sistema(comando: list, timeout_segundos: int = TIMEOUT_SEGUNDOS_DEFAULT) -> ResultadoSandbox:
    """
    Ejecuta un comando de sistema como LISTA de argumentos — nunca como
    string con shell=True. Cada argumento pasa por el validador de
    sanitizador.py antes de construir el comando.

    Uso correcto:
        ejecutar_comando_sistema(["git", "status"])

    Esto NO acepta strings tipo "git status && rm -rf /" — ni siquiera
    llega a intentar ejecutarlo, se rechaza en la validación de tipo.
    """
    if not isinstance(comando, list) or not comando:
        return ResultadoSandbox(False, "", "El comando debe ser una lista de argumentos, no un string.", -1)

    # Lista blanca: el ejecutable (comando[0]) tiene que estar en
    # COMANDOS_PERMITIDOS. Se compara por el nombre base, sin ruta ni
    # extensión, para que tanto "python" como "/usr/bin/python3.11" o
    # "python.exe" sean reconocidos.
    ejecutable = os.path.basename(str(comando[0])).lower()
    ejecutable_sin_extension = ejecutable.rsplit(".", 1)[0] if "." in ejecutable else ejecutable

    if ejecutable_sin_extension not in COMANDOS_PERMITIDOS:
        registrar_evento(
            modulo="sandbox",
            accion="ejecutar_comando_sistema",
            resultado=f"rechazado: '{ejecutable}' no está en la lista blanca de comandos permitidos",
            nivel=NIVEL_ADVERTENCIA,
            detalles={"comando_completo": comando},
        )
        return ResultadoSandbox(
            False, "",
            f"'{comando[0]}' no está en la lista de comandos permitidos "
            f"({', '.join(sorted(COMANDOS_PERMITIDOS))}). Si de verdad lo necesitas, "
            f"agrégalo a COMANDOS_PERMITIDOS en src/Security/sandbox.py.",
            -1,
        )

    try:
        comando_validado = [sanitizar_o_rechazar(str(arg), contexto="argumento de comando") for arg in comando]
    except EntradaNoSeguraError as e:
        return ResultadoSandbox(False, "", str(e), -1)

    try:
        proceso = subprocess.run(
            comando_validado,
            capture_output=True,
            text=True,
            timeout=timeout_segundos,
            shell=False,
        )
        resultado = ResultadoSandbox(
            exito=(proceso.returncode == 0),
            salida=(proceso.stdout or "")[:LIMITE_SALIDA_CARACTERES],
            error=(proceso.stderr or "")[:LIMITE_SALIDA_CARACTERES],
            codigo_salida=proceso.returncode,
        )
        registrar_evento(
            modulo="sandbox",
            accion=f"ejecutar_comando_sistema({ejecutable_sin_extension})",
            resultado="éxito" if resultado.exito else f"fallo (código {resultado.codigo_salida})",
            nivel=NIVEL_INFO if resultado.exito else NIVEL_ADVERTENCIA,
        )
        return resultado
    except subprocess.TimeoutExpired:
        registrar_evento(
            modulo="sandbox",
            accion=f"ejecutar_comando_sistema({ejecutable_sin_extension})",
            resultado=f"timeout tras {timeout_segundos}s",
            nivel=NIVEL_ADVERTENCIA,
        )
        return ResultadoSandbox(False, "", f"El comando excedió el límite de {timeout_segundos} segundos.", -1)
    except FileNotFoundError:
        return ResultadoSandbox(False, "", f"No se encontró el ejecutable '{comando_validado[0]}'.", -1)
    except Exception as e:
        registrar_evento(
            modulo="sandbox",
            accion=f"ejecutar_comando_sistema({ejecutable_sin_extension})",
            resultado=f"excepción: {e}",
            nivel=NIVEL_CRITICO,
        )
        return ResultadoSandbox(False, "", f"Error al ejecutar el comando: {e}", -1)