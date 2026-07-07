#este archivo se encargara de logara la conexion con la base de datos de postgress
import psycopg2
from psycopg2 import sql
import os
from src.Database.conexion  import obtener_conexion,DB_CONFIG
from src.Database.tablas  import crear_tablas_si_no_existen

# ================= CREAR BD =================

def crear_bd_si_no_existe():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"]
        )
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (DB_CONFIG["dbname"],))
        existe = cur.fetchone()

        if not existe:
            cur.execute(
                sql.SQL("CREATE DATABASE {};").format(
                    sql.Identifier(DB_CONFIG["dbname"])
                )
            )
            print("✔ Base de datos creada correctamente")
        else:
            print("✔ Base de datos ya existe")

        cur.close()
    except Exception as e:
        print("Error creando base de datos:", e)
    finally:
        if conn:
            conn.close()

# ================= INICIALIZACIÓN =================

def inicializar_base_datos():
    crear_bd_si_no_existe()
    crear_tablas_si_no_existen(obtener_conexion())