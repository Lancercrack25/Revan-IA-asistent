import os
import re
import urllib.parse
import unicodedata
import subprocess
from dotenv import load_dotenv

_CARPETA_PHONE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(_CARPETA_PHONE, '.env'))

def quitar_acentos(texto: str) -> str:
    if not texto:
        return ""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def filtrar_numero(numero_raw: str) -> str:
    if not numero_raw:
        return ""
    return re.sub(r'\D', '', str(numero_raw))

def obtener_numero_contacto(nombre: str) -> str:
    nombre_limpio = quitar_acentos(nombre).upper().strip().replace(" ", "_")
    var_env = f"CONTACTO_{nombre_limpio}"
    numero_raw = os.getenv(var_env)
    return filtrar_numero(numero_raw)

def preparar_envio_pc(destinatario: str, mensaje: str) -> dict:
    try:
        mensaje_encoded = urllib.parse.quote(mensaje)
        numero = obtener_numero_contacto(destinatario)

        if numero:
            url_app = f"whatsapp://send?phone={numero}&text={mensaje_encoded}"
            print(f"[WhatsApp PC]: Contacto '{destinatario}' resuelto como +{numero}.")
        else:
            url_app = f"whatsapp://send?text={mensaje_encoded}"
            print(f"[WhatsApp PC]: Contacto '{destinatario}' no encontrado en .env.")

        return {
            "exito": True,
            "canal": "pc",
            "contacto_nombre": destinatario,
            "url_app": url_app,
            "mensaje": mensaje
        }
    except Exception as e:
        return {
            "exito": False,
            "error": f"Error al preparar WhatsApp PC: {str(e)}"
        }

def ejecutar_abrir_whatsapp(url_app: str):
    """Ejecuta la apertura directa del protocolo en Windows"""
    try:
        subprocess.Popen(["cmd", "/c", "start", "", url_app], shell=False)
    except Exception as e:
        print(f"Error al abrir WhatsApp: {e}")