#este archivo se encarga de enviar mensajes de whatsapp a los contactos usando el telefono conectado
import re
import time
import urllib.parse
from src.Phone.phone_conection import _ejecutar_adb, dispositivo_conectado
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


def enviar_mensaje_whatsapp_experimental(destinatario: str, mensaje: str, espera_seg: float = 3.0) -> str:
    """
    ⚠️ EXPERIMENTAL — léelo antes de usarlo.

    Intenta lo mismo que abrir_chat_con_mensaje(), pero además manda un
    keyevent de "Enter" para intentar enviar el mensaje automáticamente,
    sin que toques el teléfono.

    Esto NO es confiable de forma garantizada: depende de tu modelo de
    teléfono, la versión de WhatsApp, y de que el chat cargue dentro del
    tiempo de espera (espera_seg). En algunos teléfonos funciona, en
    otros el mensaje se queda escrito sin enviar (mismo resultado que la
    versión segura), y en otros podría no hacer nada visible. Pruébalo
    primero con un mensaje de prueba a ti mismo antes de confiar en él
    para algo importante — no te voy a decir que esto "seguro funciona"
    porque genuinamente depende de tu dispositivo específico.
    """
    resultado_apertura = abrir_chat_con_mensaje(destinatario, mensaje)

    if "No detecto" in resultado_apertura or "No encontré" in resultado_apertura or "varios contactos" in resultado_apertura:
        return resultado_apertura  # no se pudo ni abrir, no tiene caso intentar el envío

    time.sleep(espera_seg)  # dar tiempo a que WhatsApp cargue el chat y el teclado

    exito, salida = _ejecutar_adb("shell", "input", "keyevent", "66")  # KEYCODE_ENTER

    if not exito:
        return resultado_apertura + " (No pude intentar el envío automático.)"

    return resultado_apertura.replace(
        "Confirme el envío en su teléfono.",
        "Intenté enviarlo automáticamente — verifique en su teléfono si de verdad se envió."
    )