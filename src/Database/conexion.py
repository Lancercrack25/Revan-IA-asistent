import psycopg2
from psycopg2 import sql
import os
import sys
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
#esta funcion carga las variables de entorno desde el archivo .env, cada uno tiene contraseñas y datos de conexión diferentes, por eso no se sube a github
load_dotenv()
sys.dont_write_bytecode = True  # Evita la creación de archivos .pyc
# ================= CONFIGURACIÓN =================
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "dbname": os.getenv("DB_NAME"),
}

# ================= CONEXIÓN =================
def obtener_conexion():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print("❌ Error de conexión:", e)
        return None