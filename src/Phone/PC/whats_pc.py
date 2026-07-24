# este archivo se encarga de enviar mensajes usando la App de WhatsApp de escritorio de la PC
import os
import time
import urllib.parse
import pyautogui


def enviar_mensaje_pc(numero: str, mensaje: str) -> str:
    """
    Abre WhatsApp Desktop en Windows con el chat del número indicado y presiona Enter.
    """
    try:
        mensaje_codificado = urllib.parse.quote(mensaje)
        # Enlace del protocolo nativo de la app de escritorio de WhatsApp
        url_app = f"whatsapp://send?phone={numero}&text={mensaje_codificado}"

        # 1. Abrir WhatsApp Desktop
        os.startfile(url_app)

        # 2. Dar 3 segundos para que la ventana tome foco y cargue la conversación
        time.sleep(3.0)

        # 3. Presionar Enter en la PC automáticamente
        pyautogui.press("enter")

        return f"Mensaje enviado con éxito vía WhatsApp Desktop (PC)."
    except Exception as e:
        return f"Error al intentar enviar desde WhatsApp de PC: {e}"