import psycopg2
from psycopg2 import sql
from psycopg2 import pool as pg_pool
import os
import sys
from dotenv import load_dotenv

# BUG ANTERIOR: buscaba en src/.env (dirname(__file__) + '..'), pero el archivo
# real vive en src/Database/.env, junto a este mismo módulo. Se corrige la ruta.
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
sys.dont_write_bytecode = True  # Evita la creación de archivos

# ================= CONFIGURACIÓN =================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "dbname": os.getenv("DB_NAME", "asistente_revan"),
}

# ================= CONEXIÓN DIRECTA (uso puntual) =================
# Pensada para cosas que pasan una sola vez, como crear las tablas al arrancar.
def obtener_conexion():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        print("Error de conexión:", e)
        return None

_pool = None

def _obtener_pool():
    global _pool
    if _pool is None:
        try:
            _pool = pg_pool.ThreadedConnectionPool(1, 5, **DB_CONFIG)
        except psycopg2.Error as e:
            print("Error al crear el pool de conexiones:", e)
            _pool = None
    return _pool

def obtener_conexion_pool():
    """Toma una conexión reutilizable del pool. Debe devolverse con liberar_conexion()."""
    p = _obtener_pool()
    if not p:
        return None
    try:
        return p.getconn()
    except psycopg2.Error as e:
        print("Error al tomar conexión del pool:", e)
        return None

def liberar_conexion(conn):
    """Devuelve la conexión al pool en vez de cerrarla físicamente."""
    if conn is None:
        return
    p = _obtener_pool()
    if p:
        try:
            p.putconn(conn)
        except psycopg2.Error:
            pass