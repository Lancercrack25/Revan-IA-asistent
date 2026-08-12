import smtplib
import imaplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# Importación del cargador de credenciales del proyecto
from src.Core.Config_loader import cargar_credenciales
# Variable global en memoria para pausar envíos hasta confirmación explícita
borrador_correo_pendiente = None

def enviar_correo(destinatario: str, asunto: str, cuerpo: str) -> bool:
    """Envía un correo electrónico mediante SMTP usando las credenciales cargadas."""
    try:
        credenciales = cargar_credenciales() or {}
        remitente = credenciales.get("EMAIL_USER", "")
        password = credenciales.get("EMAIL_PASSWORD", "")

        if not remitente or not password:
            print("[Email Error]: Falta EMAIL_USER o EMAIL_PASSWORD en las credenciales/configuración.")
            return False

        msg = MIMEMultipart()
        msg['From'] = remitente
        msg['To'] = destinatario
        msg['Subject'] = asunto
        msg.attach(MIMEText(cuerpo, 'plain', 'utf-8'))

        # Configuración por defecto para servidores SMTP SSL/TLS (ej. Gmail)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remitente, password)
        server.send_message(msg)
        server.quit()

        print(f"[Email]: Correo enviado con éxito a {destinatario}")
        return True
    except Exception as e:
        print(f"[Email Error]: Falló el envío del correo: {e}")
        return False


def contar_correos_sin_leer() -> int:
    """Conecta por IMAP y devuelve la cantidad exacta de correos NO leídos (UNSEEN)."""
    try:
        credenciales = cargar_credenciales() or {}
        usuario = credenciales.get("EMAIL_USER", "")
        password = credenciales.get("EMAIL_PASSWORD", "")

        if not usuario or not password:
            return -1

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(usuario, password)
        mail.select("inbox")

        status, response = mail.search(None, 'UNSEEN')
        if status == 'OK':
            unread_ids = response[0].split()
            mail.logout()
            return len(unread_ids)

        mail.logout()
        return 0
    except Exception as e:
        print(f"[IMAP Error - Contar]: {e}")
        return -1


def leer_ultimos_correos(max_resultados: int = 3) -> list:
    """Lee el remitente y asunto de los últimos correos recibidos."""
    resumenes = []
    try:
        credenciales = cargar_credenciales() or {}
        usuario = credenciales.get("EMAIL_USER", "")
        password = credenciales.get("EMAIL_PASSWORD", "")

        if not usuario or not password:
            return ["No se encontraron las credenciales configuradas para consultar el correo."]

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(usuario, password)
        mail.select("inbox")

        status, response = mail.search(None, 'ALL')
        if status == 'OK':
            ids = response[0].split()
            ultimos_ids = ids[-max_resultados:]

            for msg_id in reversed(ultimos_ids):
                _, msg_data = mail.fetch(msg_id, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Decodificación del asunto
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")
                        
                        from_ = msg.get("From", "Desconocido")
                        resumenes.append(f"De {from_} con asunto: {subject}.")

        mail.logout()
        if not resumenes:
            return ["No tiene correos recientes en su bandeja."]
        return resumenes

    except Exception as e:
        print(f"[IMAP Error - Leer]: {e}")
        return ["Hubo un problema al intentar conectar con el servidor de correo."]
    
def preparar_borrador_correo(destinatario: str, asunto: str, cuerpo: str) -> str:
    """Almacena temporalmente los datos del correo sin realizar el envío."""
    global borrador_correo_pendiente
    borrador_correo_pendiente = {
        "destinatario": destinatario,
        "asunto": asunto,
        "cuerpo": cuerpo
    }
    return f"Tengo listo el borrador para {destinatario}, con asunto '{asunto}'. El contenido es: '{cuerpo}'. ¿Desea que proceda con el envío, Señor?"


def confirmar_envio_correo() -> str:
    """Ejecuta el envío definitivo del borrador almacenado tras la orden explícita."""
    global borrador_correo_pendiente
    if not borrador_correo_pendiente:
        return "No hay ningún borrador de correo pendiente por enviar, Señor."

    datos = borrador_correo_pendiente
    exito = enviar_correo(datos["destinatario"], datos["asunto"], datos["cuerpo"])
    borrador_correo_pendiente = None 

    if exito:
        return f"Correo entregado exitosamente a {datos['destinatario']}."
    else:
        return "No se pudo entregar el correo. Por favor revise la conexión o sus credenciales."

def cancelar_borrador_correo() -> str:
    """Elimina el borrador en espera de confirmación."""
    global borrador_correo_pendiente
    if borrador_correo_pendiente:
        borrador_correo_pendiente = None
        return "Borrador de correo cancelado y descartado."
    return "No había ningún correo pendiente por cancelar."