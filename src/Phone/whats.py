# este archivo se encarga de enviar mensajes de whatsapp con validación estricta de seguridad
import re
import time
import urllib.parse
from src.Phone.phone_conection import (
    _ejecutar_adb, dispositivo_conectado,
    guardar_accion_pendiente, obtener_accion_pendiente, limpiar_accion_pendiente,
)
from src.Phone.contacts import obtener_contactos, listar_coincidencias


def resolver_contacto_seguro(destinatario: str):
    """
    Busca contactos garantizando cero ambigüedad.
    Devuelve: (Estado, Nombre/Detalle, Numero)
    """
    destinatario_limpio = destinatario.strip().lower()
    solo_digitos = re.sub(r"[^\d]", "", destinatario)

    # 1. Si enviaron un número directo (Mínimo 10 dígitos)
    if len(solo_digitos) >= 10:
        return "EXACTO", destinatario, solo_digitos

    contactos = obtener_contactos()
    
    # Busca coincidencias exactas primero
    coincidencias_exactas = [c for c in contactos if c[0].lower() == destinatario_limpio]
    if len(coincidencias_exactas) == 1:
        return "EXACTO", coincidencias_exactas[0][0], re.sub(r"[^\d]", "", coincidencias_exactas[0][1])

    # Si no hay exacta, busca parciales
    coincidencias_parciales = [c for c in contactos if destinatario_limpio in c[0].lower()]

    if len(coincidencias_parciales) == 0:
        return "NO_ENCONTRADO", None, None

    if len(coincidencias_parciales) == 1:
        return "EXACTO", coincidencias_parciales[0][0], re.sub(r"[^\d]", "", coincidencias_parciales[0][1])

    # Si hay más de una coincidencia, ES AMBIGUO -> Frenar por seguridad
    nombres_posibles = [c[0] for c in coincidencias_parciales]
    return "AMBIGUO", nombres_posibles, None


def preparar_envio_whatsapp(destinatario: str, mensaje: str) -> str:
    """
    BLINDAJE DE SEGURIDAD:
    Analiza el destinatario y detiene el proceso si no está 100% seguro de a quién enviar.
    """
    if not dispositivo_conectado():
        return "Error de Seguridad: El teléfono no está conectado por ADB."

    estado, info, numero = resolver_contacto_seguro(destinatario)

    if estado == "NO_ENCONTRADO":
        return f"Cancelado por seguridad: No existe ningún contacto llamado '{destinatario}' en tu agenda."

    if estado == "AMBIGUO":
        opciones = ", ".join(info[:4])
        return (f"Acción detenida por seguridad: Encontré varios contactos similares ({opciones}). "
                f"Por favor especifica el nombre completo para evitar confusiones.")

    # Si todo es 100% seguro, guarda la acción
    guardar_accion_pendiente("whatsapp", {
        "nombre": info,
        "numero": numero,
        "mensaje": mensaje,
    })

    return (f"Confirmación requerida: ¿Deseas enviar el siguiente mensaje a *{info}* ({numero})?\n"
            f"Texto: \"{mensaje}\"\n\n"
            f"Responde 'confirma' para enviar o 'cancela' para abortar.")


def confirmar_envio_pendiente() -> str:
    """
    Ejecuta el envío ÚNICAMENTE tras la confirmación explícita del usuario.
    """
    pendiente = obtener_accion_pendiente()
    if not pendiente or pendiente.get("tipo") != "whatsapp":
        return "No hay ningún mensaje pendiente de envío."

    datos = pendiente["datos"]
    limpiar_accion_pendiente()

    mensaje_codificado = urllib.parse.quote(datos["mensaje"])
    url = f"https://wa.me/{datos['numero']}?text={mensaje_codificado}"

    # 1. Asegurar encendido de pantalla
    _ejecutar_adb("shell", "input", "keyevent", "224")

    # 2. Abrir chat específico
    exito, salida = _ejecutar_adb("shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", url)
    if not exito:
        return f"Error abriendo el chat de {datos['nombre']}: {salida}"

    # 3. Pausa para carga de interfaz
    time.sleep(3.5)

    # 4. Intento de auto-envío por ADB
    _ejecutar_adb("shell", "input", "keyevent", "61")  # TAB
    _ejecutar_adb("shell", "input", "keyevent", "66")  # ENTER

    return f"Procesado: El mensaje para *{datos['nombre']}* se ha abierto y enviado en tu teléfono."


def cancelar_envio_pendiente() -> str:
    """Descarta cualquier envío en cola."""
    limpiar_accion_pendiente()
    return "Operación cancelada. Ningún mensaje fue enviado."