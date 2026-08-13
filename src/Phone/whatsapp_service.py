import subprocess
from src.Phone.Android.whats import preparar_envio_android, confirmar_envio_android
from src.Phone.PC.whats_pc import preparar_envio_pc
from src.Security.confirmation import GestorConfirmacion

_gestor_whatsapp = GestorConfirmacion(ttl_segundos=60)

def _ejecutar_envio(datos_preparacion: dict):
    if datos_preparacion["canal"] == "android":
        return confirmar_envio_android(datos_preparacion)
    # Ejecutado sin shell=True: el protocolo whatsapp:// ya viene con el
    # texto codificado por urllib.parse.quote en whats_pc.py.
    subprocess.Popen(["cmd", "/c", "start", "", datos_preparacion["url_app"]], shell=False)
    return (
        f"Señor, he desplegado WhatsApp PC con el chat de *{datos_preparacion['contacto_nombre']}* "
        f"y el borrador listo. Por seguridad, haga clic en Enviar."
    )

def preparar_envio_inteligente(destinatario: str, mensaje: str) -> str:
    # 1. Intentar canal Android (ADB)
    datos_preparacion = preparar_envio_android(destinatario, mensaje)
    # 2. Fallback a PC si no hay ADB disponible
    if not datos_preparacion.get("exito"):
        datos_preparacion = preparar_envio_pc(destinatario, mensaje)

    if not datos_preparacion.get("exito"):
        return datos_preparacion.get("error", "No se pudo preparar el mensaje, Señor.")

    descripcion = f"enviar por WhatsApp a {datos_preparacion['contacto_nombre']}: \"{mensaje}\""
    return _gestor_whatsapp.solicitar(
        descripcion,
        callback_confirmar=lambda: _ejecutar_envio(datos_preparacion),
        callback_cancelar=lambda: "Acción cancelada, Señor. El borrador ha sido descartado.",
    )


def confirmar_envio_inteligente() -> str:
    """Ejecuta la acción de confirmación si hay algo pendiente y dentro del TTL."""
    return _gestor_whatsapp.confirmar_manual()


def cancelar_envio_pendiente() -> str:
    return _gestor_whatsapp.cancelar_manual()


def procesar_confirmacion(orden: str) -> str:
    """Mantiene compatibilidad cuando el usuario responde por texto completo (ej. 'si, hazlo')."""
    return _gestor_whatsapp.procesar_respuesta(orden)