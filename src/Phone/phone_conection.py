#en este modulo se implementara lo de la conexion que se hara del asistente al telefono
#este archivo se encarga de establecer y verificar la conexion con el telefono via ADB
import subprocess
import shutil


def adb_disponible() -> bool:
    """Verifica que el comando 'adb' esté instalado y en el PATH del sistema."""
    return shutil.which("adb") is not None


def _ejecutar_adb(*args, timeout: int = 10):
    """
    Ejecuta un comando adb y devuelve (exito: bool, salida: str).
    Centralizado aquí para no repetir el manejo de errores en cada archivo
    (callings.py, contacts.py, whats.py) que necesite hablar con el teléfono.
    """
    if not adb_disponible():
        return False, "ADB no está instalado o no está en el PATH del sistema."

    try:
        resultado = subprocess.run(
            ["adb"] + list(args),
            capture_output=True, text=True, timeout=timeout,
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

    # La salida de 'adb devices' es algo como:
    #   List of devices attached
    #   ABC123XYZ    device
    # Buscamos alguna línea que termine en "device" (no "unauthorized" ni "offline")
    lineas = salida.splitlines()[1:]  # saltar el encabezado
    for linea in lineas:
        if linea.strip().endswith("device"):
            return True
    return False


def estado_conexion() -> str:
    """
    Versión hablable del estado de conexión, con diagnóstico específico
    de qué falta (para no dejar al usuario adivinando por qué no funciona).
    """
    if not adb_disponible():
        return ("No tengo ADB instalado, Señor. Necesita instalar Android "
                "Platform Tools y agregarlo al PATH del sistema.")

    exito, salida = _ejecutar_adb("devices")
    if not exito:
        return f"No pude comunicarme con ADB, Señor. Detalle: {salida}"

    lineas = salida.splitlines()[1:]
    lineas = [l.strip() for l in lineas if l.strip()]

    if not lineas:
        return ("No detecto ningún teléfono conectado, Señor. Verifique el cable "
                "USB y que la depuración esté activada.")

    for linea in lineas:
        if linea.endswith("unauthorized"):
            return ("Su teléfono está conectado pero no autorizado, Señor. "
                    "Revise la pantalla del celular y acepte la solicitud de depuración USB.")
        if linea.endswith("offline"):
            return "Su teléfono aparece como desconectado, Señor. Intente reconectar el cable USB."
        if linea.endswith("device"):
            return "Teléfono conectado y listo, Señor."

    return "Estado de conexión del teléfono no reconocido, Señor."


if __name__ == "__main__":
    print(estado_conexion())