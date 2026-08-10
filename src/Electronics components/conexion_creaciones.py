"""
Electronics components — comunicación serial en vivo con una placa ya
programada (Arduino/ESP32).

Complementa a Coder_agent: una vez que la placa YA tiene un sketch
subido (vía el IDE de Arduino -REVAN no sube firmware, ver
Coder_agent-), estas funciones permiten leer lo que la placa envía por
el puerto serie (ej. datos de un sensor) o mandarle un comando de texto.

Enviar comandos SÍ requiere confirmación explícita (puede accionar algo
físico real, como encender un motor o un relé); leer datos es de solo
lectura y no la requiere.
"""

import time
import serial

from src.Security.confirmation import GestorConfirmacion
from src.Security.rate_limiter import permitir_accion
from src.Security.auditoria import registrar_evento, NIVEL_INFO, NIVEL_ADVERTENCIA

TIMEOUT_SEGUNDOS_DEFAULT = 5

_gestor_confirmacion_serial = GestorConfirmacion(ttl_segundos=45)


def _resolver_puerto(puerto: str = None) -> str:
    """Si no se especifica puerto, usa el más probable detectado automáticamente."""
    if puerto:
        return puerto
    from importlib import import_module
    import sys, os
    # Import por ruta directa porque el nombre de carpeta tiene espacio
    # ("Electronics components") y no es un paquete Python válido para
    # 'from src.Electronics components import functionality'.
    ruta_modulo = os.path.join(os.path.dirname(__file__), "functionality.py")
    spec = import_module("importlib.util").spec_from_file_location("electronics_functionality", ruta_modulo)
    mod = import_module("importlib.util").module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.obtener_puerto_mas_probable()


def leer_datos_serial(puerto: str = None, baudrate: int = 9600, duracion_segundos: float = 3.0) -> str:
    """
    Abre el puerto, escucha durante 'duracion_segundos' lo que la placa
    envía, y devuelve el texto capturado. Solo lectura, sin confirmación.
    """
    if not permitir_accion("electronics"):
        return "Señor, alcancé el límite de operaciones de electrónica en el último minuto."

    puerto_real = _resolver_puerto(puerto)
    if not puerto_real:
        return "Señor, no detecté ningún dispositivo conectado. Verifique el cable USB o especifique el puerto manualmente."

    try:
        with serial.Serial(puerto_real, baudrate=baudrate, timeout=TIMEOUT_SEGUNDOS_DEFAULT) as conexion:
            tiempo_inicio = time.time()
            lineas = []
            while (time.time() - tiempo_inicio) < duracion_segundos:
                if conexion.in_waiting:
                    try:
                        linea = conexion.readline().decode("utf-8", errors="replace").strip()
                        if linea:
                            lineas.append(linea)
                    except Exception:
                        continue

        registrar_evento(
            modulo="electronics", accion=f"leer_serial({puerto_real})",
            resultado=f"{len(lineas)} líneas recibidas", nivel=NIVEL_INFO,
        )

        if not lineas:
            return f"No recibí datos de {puerto_real} en {duracion_segundos:.0f} segundos, Señor. Verifique que la placa esté enviando algo por Serial."

        print(f"[Electronics] Datos recibidos de {puerto_real}:\n" + "\n".join(lineas))
        return f"Recibí {len(lineas)} líneas de {puerto_real}, Señor. Revise la consola de REVAN para verlas completas."

    except serial.SerialException as e:
        registrar_evento(
            modulo="electronics", accion=f"leer_serial({puerto_real})",
            resultado=f"Error: {e}", nivel=NIVEL_ADVERTENCIA,
        )
        return f"No pude abrir el puerto {puerto_real}, Señor: {e}"


def _enviar_comando_real(puerto: str, comando: str, baudrate: int) -> str:
    try:
        with serial.Serial(puerto, baudrate=baudrate, timeout=TIMEOUT_SEGUNDOS_DEFAULT) as conexion:
            conexion.write((comando + "\n").encode("utf-8"))
            time.sleep(0.5)
        registrar_evento(
            modulo="electronics", accion=f"enviar_serial({puerto})",
            resultado=f"Comando '{comando}' enviado", nivel=NIVEL_INFO,
        )
        return f"Comando '{comando}' enviado a {puerto}, Señor."
    except serial.SerialException as e:
        registrar_evento(
            modulo="electronics", accion=f"enviar_serial({puerto})",
            resultado=f"Error: {e}", nivel=NIVEL_ADVERTENCIA,
        )
        return f"No pude enviar el comando a {puerto}, Señor: {e}"


def enviar_comando_serial(comando: str, puerto: str = None, baudrate: int = 9600) -> str:
    """
    Envía un comando de texto por el puerto serie (ej. 'ON', 'OFF', un
    valor). SIEMPRE pide confirmación primero -puede accionar algo físico
    real, mismo criterio que WhatsApp/correo: irreversible-ish y con
    efecto fuera de la PC-.
    """
    if not permitir_accion("electronics"):
        return "Señor, alcancé el límite de operaciones de electrónica en el último minuto."

    puerto_real = _resolver_puerto(puerto)
    if not puerto_real:
        return "Señor, no detecté ningún dispositivo conectado. Verifique el cable USB o especifique el puerto manualmente."

    return _gestor_confirmacion_serial.solicitar(
        descripcion=f"enviar el comando '{comando}' al dispositivo en {puerto_real}",
        callback_confirmar=lambda: _enviar_comando_real(puerto_real, comando, baudrate),
    )


def procesar_confirmacion_serial(texto_respuesta: str):
    """Debe llamarse desde NimClient.generar_respuesta, mismo patrón que WhatsApp/Coder_agent."""
    return _gestor_confirmacion_serial.procesar_respuesta(texto_respuesta)