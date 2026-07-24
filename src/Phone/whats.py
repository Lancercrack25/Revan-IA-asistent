#este archivo se encarga de enviar mensajes de whatsapp a los contactos usando el telefono conectado
import re
import time
import urllib.parse
from src.Phone.phone_conection import (
    _ejecutar_adb, dispositivo_conectado,
    guardar_accion_pendiente, obtener_accion_pendiente, limpiar_accion_pendiente,
)
from src.Phone.contacts import buscar_contacto, listar_coincidencias


def _resolver_numero(destinatario: str):
    """Devuelve (nombre_mostrar, numero) o (None, None) si no se resuelve."""
    destinatario = destinatario.strip()
    solo_digitos = re.sub(r"[^\d]", "", destinatario)

    if len(solo_digitos) >= 7:
        return destinatario, solo_digitos

    resultado = buscar_contacto(destinatario)
    if resultado is None:
        return None, None

    nombre, numero = resultado
    return nombre, re.sub(r"[^\d]", "", numero)


def abrir_chat_con_mensaje(destinatario: str, mensaje: str) -> str:
    """
    Abre WhatsApp con el mensaje ya escrito, SIN enviarlo — versión 100%
    manual, tú tocas el botón en tu teléfono. Útil si prefieres revisar el
    mensaje en pantalla antes de que se mande, sin usar el flujo de
    confirmación por voz.
    """
    if not dispositivo_conectado():
        return "No detecto su teléfono conectado, Señor. Verifique el cable USB."

    nombre_mostrar, numero = _resolver_numero(destinatario)

    if numero is None:
        coincidencias = listar_coincidencias(destinatario)
        if len(coincidencias) > 1:
            return (f"Encontré varios contactos parecidos a '{destinatario}', Señor: "
                    f"{', '.join(coincidencias[:5])}. Sea más específico.")
        return f"No encontré ningún contacto llamado '{destinatario}' en su agenda, Señor."

    mensaje_codificado = urllib.parse.quote(mensaje)
    url = f"https://wa.me/{numero}?text={mensaje_codificado}"

    exito, salida = _ejecutar_adb(
        "shell", "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", url,
    )

    if not exito:
        return f"No pude abrir WhatsApp para {nombre_mostrar}, Señor. Detalle: {salida}"

    return f"Chat de WhatsApp con {nombre_mostrar} abierto con el mensaje listo, Señor. Confirme el envío en su teléfono."


def preparar_envio_whatsapp(destinatario: str, mensaje: str) -> str:
    """
    RECOMENDADO: prepara el mensaje pero NO lo manda todavía. Queda
    guardado como 'acción pendiente' hasta que el usuario diga "confirma"
    en un turno APARTE — recién ahí se abre WhatsApp y se envía solo, sin
    que tengas que tocar ni escribir nada en el teléfono.

    Esto te da lo mejor de los dos mundos: cero fricción manual en el
    celular (no tienes que tocar el botón de enviar), pero con una capa
    de seguridad real (nada se manda por una sola orden sin tu aprobación
    explícita en un mensaje separado).
    """
    if not dispositivo_conectado():
        return "No detecto su teléfono conectado, Señor. Verifique el cable USB."

    nombre_mostrar, numero = _resolver_numero(destinatario)

    if numero is None:
        coincidencias = listar_coincidencias(destinatario)
        if len(coincidencias) > 1:
            return (f"Encontré varios contactos parecidos a '{destinatario}', Señor: "
                    f"{', '.join(coincidencias[:5])}. Sea más específico.")
        return f"No encontré ningún contacto llamado '{destinatario}' en su agenda, Señor."

    guardar_accion_pendiente("whatsapp", {
        "nombre": nombre_mostrar,
        "numero": numero,
        "mensaje": mensaje,
    })

    return (f"Listo para enviar a {nombre_mostrar}: \"{mensaje}\". "
            f"Diga 'confirma' para enviarlo, o 'cancela' para descartarlo, Señor.")


def confirmar_envio_pendiente() -> str:
    """
    Ejecuta de verdad el envío que quedó pendiente de confirmación: abre
    WhatsApp y manda el 'Enter' automático, sin que toques el teléfono.

    Nota honesta sobre el auto-envío: el keyevent de Enter para confirmar
    el mensaje en WhatsApp no está garantizado al 100% en todos los
    modelos de teléfono/versiones de WhatsApp — en la gran mayoría de
    casos sí funciona (WhatsApp normalmente respeta Enter como enviar
    cuando el foco está en el campo de texto), pero si en tu teléfono
    específico no llegara a mandarlo, el mensaje se queda escrito y
    visible, listo para que lo mandes tú con un toque — nunca falla en
    silencio sin que lo notes.
    """
    pendiente = obtener_accion_pendiente()
    if not pendiente or pendiente.get("tipo") != "whatsapp":
        return "No hay ningún mensaje de WhatsApp pendiente de confirmar, Señor."

    datos = pendiente["datos"]
    limpiar_accion_pendiente()

    mensaje_codificado = urllib.parse.quote(datos["mensaje"])
    url = f"https://wa.me/{datos['numero']}?text={mensaje_codificado}"

    exito, salida = _ejecutar_adb(
        "shell", "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", url,
    )
    if not exito:
        return f"No pude abrir WhatsApp para {datos['nombre']}, Señor. Detalle: {salida}"

    time.sleep(3.0)  # esperar a que WhatsApp cargue el chat y el teclado

    exito2, _ = _ejecutar_adb("shell", "input", "keyevent", "66")  # KEYCODE_ENTER
    if not exito2:
        return f"Mensaje abierto para {datos['nombre']}, pero no pude confirmar el envío automático. Revíselo en su teléfono."

    return f"Mensaje enviado a {datos['nombre']}, Señor. Verifique en su teléfono que se haya mandado bien."


def cancelar_envio_pendiente() -> str:
    """Descarta el mensaje pendiente sin enviarlo."""
    pendiente = obtener_accion_pendiente()
    if not pendiente or pendiente.get("tipo") != "whatsapp":
        return "No había ningún mensaje pendiente, Señor."
    limpiar_accion_pendiente()
    return "Envío de WhatsApp cancelado, Señor."