import time
import os
from src.Phone.Android.whats import preparar_envio_android, confirmar_envio_android
from src.Phone.PC.whats_pc import preparar_envio_pc

ACCION_PENDIENTE = None
TTL_CONFIRMACION = 60  # Límite de 60 segundos antes de expirar

def preparar_envio_inteligente(destinatario: str, mensaje: str) -> str:
    global ACCION_PENDIENTE
    # 1. Intentar canal Android (ADB)
    datos_preparacion = preparar_envio_android(destinatario, mensaje)
    # 2. Fallback a PC si no hay ADB disponible
    if not datos_preparacion.get("exito"):
        datos_preparacion = preparar_envio_pc(destinatario, mensaje)

    if not datos_preparacion.get("exito"):
        return datos_preparacion.get("error", "No se pudo preparar el mensaje, Señor.")
    # 3. Guardar estado con timestamp para TTL
    ACCION_PENDIENTE = {
        "tipo": "whatsapp",
        "datos": datos_preparacion,
        "timestamp": time.time()
    }

    return (
        f"Señor, he preparado el mensaje para *{datos_preparacion['contacto_nombre']}*:\n"
        f"» \"{mensaje}\"\n\n"
        f"¿Desea que proceda? Responda 'Confirma' o 'Cancela'."
    )

def confirmar_envio_inteligente() -> str:
    """Ejecuta la acción de confirmación si hay algo pendiente y dentro del TTL."""
    global ACCION_PENDIENTE
    if not ACCION_PENDIENTE:
        return "No hay ninguna acción pendiente por confirmar, Señor."

    tiempo_transcurrido = time.time() - ACCION_PENDIENTE["timestamp"]
    if tiempo_transcurrido > TTL_CONFIRMACION:
        ACCION_PENDIENTE = None
        return "Señor, la confirmación pendiente ha expirado por razones de seguridad."
    datos = ACCION_PENDIENTE["datos"]
    ACCION_PENDIENTE = None

    if datos["canal"] == "android":
        return confirmar_envio_android(datos)
    else:
        os.system(f'start "" "{datos["url_app"]}"')
        return f"Señor, he desplegado WhatsApp PC con el chat de *{datos['contacto_nombre']}* y el borrador listo. Por seguridad, haga clic en Enviar."

def cancelar_envio_pendiente() -> str:
    global ACCION_PENDIENTE
    if not ACCION_PENDIENTE:
        return "No hay ninguna acción pendiente que cancelar, Señor."
    
    ACCION_PENDIENTE = None
    return "Acción cancelada, Señor. El borrador ha sido descartado."

def procesar_confirmacion(orden: str) -> str:
    """Mantiene compatibilidad cuando el usuario responde por texto completo (ej. 'si, hazlo')."""
    global ACCION_PENDIENTE
    
    if not ACCION_PENDIENTE:
        return None

    orden_clean = orden.lower().strip()
    # Interceptación por palabras clave
    if any(k in orden_clean for k in ["confirma", "confirmar"]):
        return confirmar_envio_inteligente()

    elif any(k in orden_clean for k in ["cancela", "cancelar"]):
        return cancelar_envio_pendiente()

    return None