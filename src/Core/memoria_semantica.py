import os
import json
import math

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
    """
    Genera el vector de embedding para un texto.
    input_type="passage" -> para el contenido que se está GUARDANDO.
    input_type="query"   -> para el texto de BÚSQUEDA (nv-embedqa-e5-v5
    trata estos dos casos de forma distinta internamente, ya que está
    optimizado para retrieval asimétrico pregunta/respuesta).
    """
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


def _similitud_coseno(vec_a: list, vec_b: list) -> float:
    """
    Similitud coseno pura en Python (sin numpy, para no agregar otra
    dependencia): 1.0 = idénticos, 0.0 = sin relación, -1.0 = opuestos.
    """
    producto_punto = sum(a * b for a, b in zip(vec_a, vec_b))
    norma_a = math.sqrt(sum(a * a for a in vec_a))
    norma_b = math.sqrt(sum(b * b for b in vec_b))
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return producto_punto / (norma_a * norma_b)


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
            VALUES (%s, %s, %s::jsonb);
            """,
            (rol, contenido, json.dumps(embedding)),
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


def buscar_memoria_semantica(consulta: str, top_k: int = 3, similitud_minima: float = 0.75):
    """
    Busca en la memoria pasada los 'top_k' intercambios más parecidos por
    SIGNIFICADO a 'consulta', no por coincidencia exacta de palabras.

    Trae TODOS los embeddings guardados y calcula la similitud coseno en
    Python (nada de SQL vectorial). Para el volumen de un asistente
    personal (cientos/pocos miles de registros) esto es rápido; si algún
    día la tabla creciera a cientos de miles de filas, esto se volvería
    lento y ahí sí valdría la pena migrar a pgvector.

    'similitud_minima' filtra resultados poco relacionados (más alto =
    más estricto). Devuelve una lista de dicts ordenada de más a menos
    parecido: [{"rol": ..., "contenido": ..., "fecha": ..., "similitud": ...}, ...]
    """
    embedding_consulta = _generar_embedding(consulta, input_type="query")
    if embedding_consulta is None:
        return []

    conn = obtener_conexion_pool()
    if not conn:
        return []

    try:
        cur = conn.cursor()
        cur.execute("SELECT rol, contenido, fecha, embedding FROM memoria_semantica;")
        filas = cur.fetchall()
        cur.close()

        candidatos = []
        for rol, contenido, fecha, embedding_guardado in filas:
            # psycopg2 ya devuelve JSONB como lista/dict de Python directamente
            similitud = _similitud_coseno(embedding_consulta, embedding_guardado)
            if similitud >= similitud_minima:
                candidatos.append({
                    "rol": rol,
                    "contenido": contenido,
                    "fecha": fecha,
                    "similitud": similitud,
                })

        candidatos.sort(key=lambda x: x["similitud"], reverse=True)
        return candidatos[:top_k]

    except Exception as e:
        print(f"[MemoriaSemantica]: Error al buscar: {e}")
        return []
    finally:
        liberar_conexion(conn)