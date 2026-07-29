#se encargara de gestionar y controlar los corrreos auqney se nececita seguridad lo mas importante.,n
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from src.Emails.account_conection import obtener_servicio_gmail


def leer_ultimos_correos(max_resultados: int = 5) -> list:
    """Obtiene un resumen de los últimos correos no leídos."""
    try:
        service = obtener_servicio_gmail()
        results = service.users().messages().list(
            userId='me', q='is:unread', maxResults=max_resultados
        ).execute()
        
        messages = results.get('messages', [])
        lista_resumen = []

        if not messages:
            return ["No tienes correos nuevos sin leer."]

        for msg in messages:
            txt = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = txt['payload']['headers']
            
            asunto = next((h['value'] for h in headers if h['name'].lower() == 'subject'), "Sin Asunto")
            remitente = next((h['value'] for h in headers if h['name'].lower() == 'from'), "Desconocido")
            snippet = txt.get('snippet', '')

            lista_resumen.append(f"De: {remitente} | Asunto: {asunto} | Resumen: {snippet[:80]}...")

        return lista_resumen

    except Exception as e:
        print(f"[EMAIL CONTROL]: Error al leer correos -> {e}")
        return [f"Error al conectar con Gmail: {e}"]


def enviar_correo(destinatario: str, asunto: str, cuerpo: str, ruta_adjunto: str = None) -> bool:
    """Envía un correo electrónico con soporte para archivos adjuntos."""
    try:
        service = obtener_servicio_gmail()
        mensaje = MIMEMultipart()
        mensaje['to'] = destinatario
        mensaje['subject'] = asunto

        mensaje.attach(MIMEText(cuerpo, 'plain'))

        # Adjuntar archivo si existe (ej. reporte del Inspector)
        if ruta_adjunto and os.path.exists(ruta_adjunto):
            with open(ruta_adjunto, 'rb') as adj:
                parte = MIMEBase('application', 'octet-stream')
                parte.set_payload(adj.read())
                encoders.encode_base64(parte)
                parte.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(ruta_adjunto)}"')
                mensaje.attach(parte)

        raw_message = base64.urlsafe_b64encode(mensaje.as_bytes()).decode('utf-8')
        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        
        print(f"[EMAIL CONTROL]: Correo enviado exitosamente a {destinatario}.")
        return True

    except Exception as e:
        print(f"[EMAIL CONTROL]: Error al enviar correo -> {e}")
        return False


if __name__ == "__main__":
    print("Prueba de lectura de correos...")
    correos = leer_ultimos_correos(3)
    for c in correos:
        print("-", c)