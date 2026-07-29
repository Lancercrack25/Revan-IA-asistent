#se encarga de conectarse a la cuenta de ggogle con una api y asi poder proceder con lo demas.
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Permisos requeridos para Gmail y Google Calendar
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar'
]
# Rutas de credenciales
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

def obtener_credenciales():
    """Maneja el flujo de autenticación OAuth2 y devuelve las credenciales activas."""
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Falta el archivo 'credentials.json' en {BASE_DIR}. "
                    "Descárgalo desde Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # Guardar token para futuras sesiones
        with open(TOKEN_PATH, 'w', encoding='utf-8') as token_file:
            token_file.write(creds.to_json())
    return creds

def obtener_servicio_gmail():
    """Devuelve el cliente construido para la API de Gmail."""
    creds = obtener_credenciales()
    return build('gmail', 'v1', credentials=creds)

def obtener_servicio_calendar():
    """Devuelve el cliente construido para la API de Google Calendar."""
    creds = obtener_credenciales()
    return build('calendar', 'v3', credentials=creds)

if __name__ == "__main__":
    print("[GOOGLE CONNECTION]: Verificando autenticación...")
    try:
        credenciales = obtener_credenciales()
        print("[GOOGLE CONNECTION]: Autenticación exitosa y token activo.")
    except Exception as e:
        print(f"[GOOGLE CONNECTION]: Error -> {e}")