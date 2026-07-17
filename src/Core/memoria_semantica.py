#en este archivo se gestionará la memoria semántica del asistente
import os

try:
    from openai import OpenAI
except ImportError:
    print("[MemoriaSemantica]: Falta la librería 'openai'. Instálala con: pip install openai")
    raise

from src.Database.conexion import obtener_conexion_pool, liberar_conexion
from src.Core.Config_loader import cargar_ajustes

# Límite de caracteres antes de generar el embedding. El modelo tiene un
# máximo de 512 tokens de contexto (~4 caracteres por token en promedio),
# así que se deja margen para no pasarse y que la API corte o falle.
MAX_CARACTERES_EMBEDDING = 1800

_cliente_nim = None


def _obtener_cliente_nim():
    """Inicializa el cliente de NIM de forma perezosa (solo cuando se usa
    por primera vez), reutilizando la misma API key que ya usa NimClient."""
    global _cliente_nim
    if _cliente_nim is not None:
        return _cliente_nim

    ajustes = cargar_ajustes() or {}
    api_key = ajustes.get("NVIDIA_NIM_API_KEY", os.getenv("NVIDIA_NIM_API_KEY", ""))
    if not api_key:
        raise ValueError("Falta NVIDIA_NIM_API_KEY para generar embeddings de memoria semántica.")

    _cliente_nim = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
    return _cliente_nim


def _generar_embedding(texto: str, input_type: str = "passage"):
    texto = (texto or "").strip()
    if not texto:
        return None

    texto = texto[:MAX_CARACTERES_EMBEDDING]

    try:
        cliente = _obtener_cliente_nim()
        respuesta = cliente.embeddings.create(
            model="nvidia/nv-embedqa-e5-v5",
            input=texto,
            encoding_format="float",
            extra_body={"input_type": input_type},
        )
        return respuesta.data[0].embedding
    except Exception as e:
        print(f"[MemoriaSemantica]: Error al generar embedding: {e}")
        return None


def _vector_a_literal_pg(embedding: list) -> str:
    """Convierte una lista de floats de Python al formato de texto que
    pgvector espera para el cast '%s::vector' (ej: '[0.01,-0.02,...]')."""
    return "[" + ",".join(str(x) for x in embedding) + "]"


def guardar_intercambio(rol: str, contenido: str) -> bool:
    """
    Guarda un mensaje (de usuario o de REVAN) en la memoria semántica,
    junto con su embedding, para poder buscarlo después por significado.
    rol: "usuario" o "revan" (libre, es solo una etiqueta).
    """
    embedding = _generar_embedding(contenido, input_type="passage")
    if embedding is None:
        return False

    conn = obtener_conexion_pool()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO memoria_semantica (rol, contenido, embedding)
            VALUES (%s, %s, %s::vector);
            """,
            (rol, contenido, _vector_a_literal_pg(embedding)),
        )
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"[MemoriaSemantica]: Error al guardar intercambio: {e}")
        conn.rollback()
        return False
    finally:
        liberar_conexion(conn)


def buscar_memoria_semantica(consulta: str, top_k: int = 3, distancia_maxima: float = 0.5):
    embedding_consulta = _generar_embedding(consulta, input_type="query")
    if embedding_consulta is None:
        return []

    conn = obtener_conexion_pool()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT rol, contenido, fecha, embedding <=> %s::vector AS distancia
            FROM memoria_semantica
            ORDER BY distancia ASC
            LIMIT %s;
            """,
            (_vector_a_literal_pg(embedding_consulta), top_k),
        )
        filas = cur.fetchall()
        cur.close()

        resultados = [
            {"rol": rol, "contenido": contenido, "fecha": fecha, "distancia": distancia}
            for (rol, contenido, fecha, distancia) in filas
            if distancia <= distancia_maxima
        ]
        return resultados
    except Exception as e:
        print(f"[MemoriaSemantica]: Error al buscar: {e}")
        return []
    finally:
        liberar_conexion(conn)