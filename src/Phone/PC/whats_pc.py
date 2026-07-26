import urllib.parse

def preparar_envio_pc(destinatario: str, mensaje: str) -> dict:
    """Prepara el esquema URI para WhatsApp Desktop o Web en Windows."""
    if not destinatario or not mensaje:
        return {"exito": False, "error": "Destinatario o mensaje vacíos."}

    telefono_clean = ''.join(filter(str.isdigit, str(destinatario)))
    mensaje_encoded = urllib.parse.quote(mensaje)
    
    if telefono_clean:
        url_app = f"whatsapp://send?phone={telefono_clean}&text={mensaje_encoded}"
    else:
        # Fallback por nombre si no es un número directo
        url_app = f"whatsapp://send?text={mensaje_encoded}"

    return {
        "exito": True,
        "canal": "pc",
        "contacto_nombre": destinatario,
        "mensaje": mensaje,
        "url_app": url_app
    }