import subprocess
import urllib.parse
from src.Phone.Android.contacts import buscar_contacto

def _ejecutar_adb(*args) -> str:
    """Ejecuta comandos ADB de bajo nivel."""
    try:
        cmd = ["adb"] + list(args)
        resultado = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return resultado.stdout.strip()
    except Exception as e:
        return f"Error ADB: {e}"

def preparar_envio_android(destinatario: str, mensaje: str, lista_contactos: dict = None) -> dict:
    """Valida la presencia del contacto en Android y prepara el paquete URI."""
    if not destinatario or not mensaje:
        return {"exito": False, "error": "Destinatario o mensaje vacíos."}
    dispositivos = _ejecutar_adb("devices")
    lineas_dispositivo = [
        linea for linea in dispositivos.splitlines()
        if linea.strip() and not linea.startswith("List of devices")
        and linea.split()[-1] == "device"
    ]
    if not lineas_dispositivo:
        return {"exito": False, "error": "Dispositivo Android no detectado por ADB."}

    # Si se pasa lista de contactos, usar la búsqueda normalizada
    telefono = destinatario
    nombre_contacto = destinatario

    if lista_contactos:
        coincidencias = buscar_contacto(destinatario, lista_contactos)
        if not coincidencias:
            return {"exito": False, "error": f"No se encontró a '{destinatario}' en sus contactos."}
        if len(coincidencias) > 1:
            nombres = ", ".join([c[0] for c in coincidencias])
            return {"exito": False, "error": f"Existe ambigüedad con: {nombres}. Especifique mejor."}
        
        nombre_contacto, datos = coincidencias[0]
        telefono = datos.get("telefono", destinatario)
    elif not any(c.isdigit() for c in destinatario):
        return {"exito": False, "error": f"Sin lista de contactos de Android cargada; no se puede resolver el nombre '{destinatario}' por este canal."}

    # Limpiar número de teléfono
    telefono_clean = ''.join(filter(str.isdigit, str(telefono)))
    mensaje_encoded = urllib.parse.quote(mensaje)
    uri = f"https://api.whatsapp.com/send?phone={telefono_clean}&text={mensaje_encoded}"

    return {
        "exito": True,
        "canal": "android",
        "contacto_nombre": nombre_contacto,
        "telefono": telefono_clean,
        "mensaje": mensaje,
        "uri": uri
    }

def confirmar_envio_android(datos: dict) -> str:
    """Abre el intent del mensaje en el teléfono sin mentir sobre el envío final."""
    try:
        cmd = f'shell am start -a android.intent.action.VIEW -d "{datos["uri"]}"'
        _ejecutar_adb(cmd)
        return (
            f"Señor, el chat de *{datos['contacto_nombre']}* se ha abierto en su teléfono "
            f"con el borrador listo. Por seguridad, presione el botón Enviar en pantalla."
        )
    except Exception as e:
        return f"Error al abrir la conversación en el teléfono: {e}"