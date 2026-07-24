# este archivo decide automáticamente si enviar el mensaje por Android (USB) o por la PC
from src.Phone.Android.phone_conection import dispositivo_conectado
from src.Phone.Android.whats import (
    preparar_envio_whatsapp as preparar_android,
    confirmar_envio_pendiente as confirmar_android,
    cancelar_envio_pendiente as cancelar_android,
)
from src.Phone.Android.phone_conection import (
    guardar_accion_pendiente,
    obtener_accion_pendiente,
    limpiar_accion_pendiente,
)
from src.Phone.Android.contacts import buscar_contacto, listar_coincidencias
from src.Phone.PC.whats_pc import enviar_mensaje_pc
import re


def _resolver_destinatario(destinatario: str):
    """Resuelve el contacto usando la agenda de Android o el número directo."""
    destinatario_limpio = destinatario.strip()
    solo_digitos = re.sub(r"[^\d]", "", destinatario_limpio)

    if len(solo_digitos) >= 10:
        return destinatario_limpio, solo_digitos

    # Intentar resolver usando la agenda
    resultado = buscar_contacto(destinatario_limpio)
    if resultado:
        nombre, numero = resultado
        return nombre, re.sub(r"[^\d]", "", numero)

    return None, None


def enviar_mensaje_whatsapp(destinatario: str, mensaje: str) -> str:
    """
    Función principal de envío:
    Detecta si hay teléfono por USB. Si está, usa Android; si no, conmuta a la PC.
    """
    nombre, numero = _resolver_destinatario(destinatario)

    if not numero:
        coincidencias = listar_coincidencias(destinatario)
        if len(coincidencias) > 1:
            return f"Encontré varias coincidencias: {', '.join(coincidencias[:4])}. Especifica el nombre exacto."
        return f"No se encontró al contacto '{destinatario}'."

    # DECISIÓN AUTOMÁTICA DE VÍA
    if dispositivo_conectado():
        # Vía 1: Teléfono Android conectado por USB
        from src.Phone.Android.whats import abrir_chat_con_mensaje
        return abrir_chat_con_mensaje(numero, mensaje)
    else:
        # Vía 2: WhatsApp App de Escritorio en PC
        print("[WhatsApp Service]: Teléfono no detectado por USB. Conmutando a App de PC...")
        return enviar_mensaje_pc(numero, mensaje)


def preparar_envio_inteligente(destinatario: str, mensaje: str) -> str:
    """
    Prepara el mensaje con la confirmación de seguridad y determina
    por qué vía se enviará cuando se diga 'confirma'.
    """
    via_uso = "Android (USB)" if dispositivo_conectado() else "WhatsApp PC"
    nombre, numero = _resolver_destinatario(destinatario)

    if not numero:
        return f"No se pudo resolver el contacto '{destinatario}'."

    # Guardar la acción pendiente especificando la vía a utilizar
    guardar_accion_pendiente("whatsapp", {
        "nombre": nombre,
        "numero": numero,
        "mensaje": mensaje,
        "via": "android" if dispositivo_conectado() else "pc"
    })

    return (f"Listo para enviar por vía [{via_uso}] a *{nombre}* ({numero}):\n"
            f"\"{mensaje}\"\n\n"
            f"Diga 'confirma' para enviar o 'cancela' para abortar, Señor.")


def confirmar_envio_inteligente() -> str:
    """Ejecuta el envío confirmado en la plataforma que se determinó previamente."""
    pendiente = obtener_accion_pendiente()
    if not pendiente or pendiente.get("tipo") != "whatsapp":
        return "No hay ningún mensaje pendiente de confirmar, Señor."

    datos = pendiente["datos"]
    limpiar_accion_pendiente()

    if datos.get("via") == "android" and dispositivo_conectado():
        return confirmar_android()
    else:
        # Si era para PC o si se desconectó el USB entre la preparación y la confirmación
        return enviar_mensaje_pc(datos["numero"], datos["mensaje"])