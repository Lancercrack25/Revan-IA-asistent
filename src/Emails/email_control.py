import os
import json
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def _cargar_credenciales() -> tuple[str, str]:
    """Busca y carga EMAIL_USER y EMAIL_PASSWORD desde el archivo JSON de configuración."""
    # Buscar el archivo json en la raíz del proyecto o en la carpeta config
    posibles_rutas = [
        os.path.join(os.path.dirname(__file__), "..", "..", "config.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "keys.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "config", "keys.json"),
        os.path.join(os.path.dirname(__file__), "..", "..", "config", "config.json"),
    ]

    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            try:
                with open(ruta, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    user = data.get("EMAIL_USER") or data.get("EMAIL") or data.get("REVAN_EMAIL_USER")
                    password = data.get("EMAIL_PASSWORD") or data.get("EMAIL_PASS") or data.get("REVAN_EMAIL_PASS")
                    if user and password:
                        return user, password
            except Exception as e:
                print(f"[EMAIL CONFIG ERROR]: Error al leer {ruta} -> {e}")

    # Si no se encuentra en JSON, intenta desde variables de entorno del sistema
    user_env = os.getenv("EMAIL_USER")
    pass_env = os.getenv("EMAIL_PASSWORD")
    return user_env or "", pass_env or ""


EMAIL_USER, EMAIL_PASS = _cargar_credenciales()


def enviar_correo(destinatario: str, asunto: str, cuerpo: str, ruta_adjunto: str = None) -> bool:
    """Envía un correo electrónico mediante el servidor SMTP de Google."""
    if not EMAIL_USER or not EMAIL_PASS:
        print("[EMAIL CONTROL]: Error -> No se encontraron EMAIL_USER o EMAIL_PASSWORD en el JSON de configuración.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = destinatario
        msg['Subject'] = asunto
        msg.attach(MIMEText(cuerpo, 'plain'))

        # Adjuntar archivo si existe (ej. la gráfica del Inspector)
        if ruta_adjunto and os.path.exists(ruta_adjunto):
            with open(ruta_adjunto, 'rb') as adj:
                parte = MIMEBase('application', 'octet-stream')
                parte.set_payload(adj.read())
                encoders.encode_base64(parte)
                parte.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(ruta_adjunto)}"')
                msg.attach(parte)

        # Conexión SSL por puerto 465
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, destinatario, msg.as_string())
        server.quit()

        print(f"[EMAIL CONTROL]: Correo enviado con éxito a {destinatario}.")
        return True

    except Exception as e:
        print(f"[EMAIL CONTROL ERROR]: Fallo al enviar correo -> {e}")
        return False


def leer_ultimos_correos(max_resultados: int = 3) -> list:
    """Lee los últimos mensajes no leídos vía IMAP."""
    if not EMAIL_USER or not EMAIL_PASS:
        return ["Error: Credenciales de correo no encontradas en la configuración."]

    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select('inbox')

        # Buscar correos sin leer
        _, status_data = mail.search(None, 'UNSEEN')
        id_list = status_data[0].split()

        if not id_list:
            return ["Señor, no tiene correos nuevos sin leer."]

        resumenes = []
        for num in id_list[-max_resultados:]:
            _, data = mail.fetch(num, '(RFC822)')
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)

            asunto = msg.get('Subject', 'Sin Asunto')
            remitente = msg.get('From', 'Desconocido')
            resumenes.append(f"De: {remitente} | Asunto: {asunto}")

        mail.logout()
        return resumenes

    except Exception as e:
        print(f"[EMAIL CONTROL ERROR]: Fallo al leer buzón -> {e}")
        return [f"Error de conexión: {e}"]


if __name__ == "__main__":
    print("Probando módulo de correo...")
    print("Usuario detectado:", EMAIL_USER if EMAIL_USER else "No detectado")
    correos = leer_ultimos_correos()
    for c in correos:
        print("-", c)