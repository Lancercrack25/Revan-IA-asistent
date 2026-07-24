# este archivo se encarga de establecer y verificar la conexion con el telefono via ADB
import subprocess
import shutil

# Guardado en memoria para confirmación de acciones sensibles
_accion_pendiente = None


def adb_disponible() -> bool:
    """Verifica que el comando 'adb' esté instalado y en el PATH del sistema."""
    return shutil.which("adb") is not None


def _ejecutar_adb(*args, timeout: int = 10):
    """
    Ejecuta un comando adb y devuelve (exito: bool, salida: str).
    """
    if not adb_disponible():
        return False, "ADB no está instalado o no está en el PATH del sistema."
    try:
        resultado = subprocess.run(
            ["adb"] + list(args),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if resultado.returncode != 0:
            return False, resultado.stderr.strip() or resultado.stdout.strip()
        return True, resultado.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "El comando adb tardó demasiado en responder."
    except Exception as e:
        return False, str(e)


def dispositivo_conectado() -> bool:
    """Verifica que haya al menos un dispositivo Android conectado y autorizado."""
    exito, salida = _ejecutar_adb("devices")
    if not exito:
        return False

    lineas = salida.splitlines()[1:]
    for linea in lineas:
        if linea.strip().endswith("device"):
            return True
    return False


def estado_conexion() -> str:
    """Devuelve un diagnóstico en texto del estado de la conexión ADB."""
    if not adb_disponible():
        return (
            "No tengo ADB instalado, Señor. Necesita instalar Android "
            "Platform Tools y agregarlo al PATH del sistema."
        )

    exito, salida = _ejecutar_adb("devices")
    if not exito:
        return f"No pude comunicarme con ADB, Señor. Detalle: {salida}"

    lineas = [l.strip() for l in salida.splitlines()[1:] if l.strip()]

    if not lineas:
        return (
            "No detecto ningún teléfono conectado, Señor. Verifique el cable "
            "USB y que la depuración esté activada."
        )

    for linea in lineas:
        if linea.endswith("unauthorized"):
            return (
                "Su teléfono está conectado pero aun no esta autorizado, Señor. "
                "Revise la pantalla del celular y acepte la solicitud de depuración USB."
            )
        if linea.endswith("offline"):
            return "Su teléfono aparece como desconectado, Señor. Intente reconectar el cable USB."
        if linea.endswith("device"):
            return "Teléfono conectado y listo, Señor."

    return "Estado de conexión del teléfono Fallida, Señor."


# --- GESTIÓN DE ACCIONES PENDIENTES ---

def guardar_accion_pendiente(tipo: str, datos: dict):
    global _accion_pendiente
    _accion_pendiente = {"tipo": tipo, "datos": datos}


def obtener_accion_pendiente():
    return _accion_pendiente


def limpiar_accion_pendiente():
    global _accion_pendiente
    _accion_pendiente = None


def hay_accion_pendiente() -> bool:
    return _accion_pendiente is not None


if __name__ == "__main__":
    print(estado_conexion())