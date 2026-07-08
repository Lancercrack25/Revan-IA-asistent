# este archivo se encargara de inicializar las tablas de la base de datos de postgres
import psycopg2
from psycopg2 import sql
import os
import sys

sys.dont_write_bytecode = True  # Evita la creación de archivos .pyc

def crear_tablas_si_no_existen(conn):
    """
    Recibe la conexión activa a la base de datos de REVAN y crea
    las tablas tácticas de forma automática si no existen.
    """
    if conn is None:
        print("Error: No se puede inicializar tablas sin una conexión activa.")
        return

    try:
        cur = conn.cursor()

        # TABLA 1: HISTORIAL DE INTERACCIONES Y COMANDOS
        query_historial = """
        CREATE TABLE IF NOT EXISTS historial_interacciones (
            id SERIAL PRIMARY KEY,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            orden_usuario TEXT NOT NULL,
            respuesta_revan TEXT NOT NULL,
            accion_ejecutada VARCHAR(100) DEFAULT 'CONVERSACION'
        );
        """

        # TABLA 2: MEMORIA DE LARGO PLAZO (SISTEMA DE RECUERDOS)
        query_memoria = """
        CREATE TABLE IF NOT EXISTS memoria_largo_plazo (
            id SERIAL PRIMARY KEY,
            clave VARCHAR(150) UNIQUE NOT NULL,
            valor TEXT NOT NULL,
            fecha_guardado TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        # TABLA 3: ESTADO DEL SISTEMA (FOCO Y RUTA ACTIVA EN TIEMPO REAL)
        # Permite saber en qué carpeta está trabajando el usuario para crear subcarpetas o archivos ahí.
        query_estado = """
        CREATE TABLE IF NOT EXISTS estado_sistema (
            clave VARCHAR(50) PRIMARY KEY,
            valor TEXT NOT NULL,
            actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        # Ejecutamos las consultas SQL
        cur.execute(query_historial)
        cur.execute(query_memoria)
        cur.execute(query_estado)

        # INSERTAR ESTADO INICIAL (RUTA DEL ESCRITORIO POR DEFECTO)
        ruta_escritorio = os.path.join(os.path.expanduser("~"), "Desktop")
        query_inicial_ruta = """
        INSERT INTO estado_sistema (clave, valor)
        VALUES ('ultima_ruta', %s)
        ON CONFLICT (clave) DO NOTHING;
        """
        cur.execute(query_inicial_ruta, (ruta_escritorio,))
        
        # Guardamos los cambios de forma permanente en el disco duro
        conn.commit()
        print("[REVAN DB]: Tablas e infraestructura de estado inicializadas correctamente.")
        
        cur.close()
    except psycopg2.Error as e:
        print("Error de PostgreSQL al crear las tablas:", e)
        # En caso de fallo, revertimos la transacción para no corromper la BD
        conn.rollback()
    finally:
        if conn:
            conn.close()