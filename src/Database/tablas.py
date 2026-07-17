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

        # Confirmamos ESTA transacción (las 3 tablas originales + estado
        # inicial) ANTES de intentar pgvector. Así, si pgvector falla más
        # abajo, su rollback solo afecta a esa parte, sin deshacer lo de
        # aquí arriba (que ya quedó guardado en disco con este commit).
        conn.commit()
        print("[REVAN DB]: Tablas e infraestructura de estado inicializadas correctamente.")

        # EXTENSIÓN + TABLA 4: MEMORIA SEMÁNTICA (búsqueda por significado)
        # Requiere que pgvector esté instalado en el servidor de Postgres.
        # Va en su propia transacción independiente, con su propio commit,
        # para que un fallo aquí no afecte nada de lo anterior.
        # Dimensión 1024 fija: es la que devuelve nvidia/nv-embedqa-e5-v5.
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS memoria_semantica (
                    id SERIAL PRIMARY KEY,
                    rol VARCHAR(20) NOT NULL,
                    contenido TEXT NOT NULL,
                    embedding vector(1024) NOT NULL,
                    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            print("[REVAN DB]: Memoria semántica (pgvector) inicializada correctamente.")
        except psycopg2.Error as e:
            print(f"[REVAN DB]: No se pudo inicializar la memoria semántica (¿pgvector instalado?): {e}")
            conn.rollback()

        cur.close()
    except psycopg2.Error as e:
        print("Error de PostgreSQL al crear las tablas:", e)
        print("Revisar la configuración de la base de datos y los permisos del usuario.")
        # En caso de fallo, revertimos la transacción para no corromper la BD
        conn.rollback()
    finally:
        if conn:
            conn.close()