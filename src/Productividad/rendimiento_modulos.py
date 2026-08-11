#archivo que se encargara de mostrar el rendimiento de los modulos de manera mas detallada y con graficas, para poder ver el rendimiento de cada modulo y poder compararlos entre si, ademas de poder ver el rendimiento de cada modulo en diferentes momentos del dia, para poder ver si hay algun modulo que este teniendo un rendimiento bajo en algun momento del dia y poder tomar medidas al respecto.
"""
rendimiento_modulos.py — estadísticas reales de uso de TODOS los módulos
(WhatsApp, Correo, Word/Excel, Cámara, Red, Agenda, etc.), leyendo la
tabla historial_interacciones que YA se llena con cada llamada a
registrar_accion_sistema() en todo el proyecto.

Igual que rendimiento_agentes.py: no se agrega ninguna instrumentación
nueva, solo se consulta lo que ya se está guardando.
"""

from collections import Counter

from src.Database.conexion import obtener_conexion_pool, liberar_conexion


def obtener_rendimiento_modulos(limite_filas: int = 500) -> dict:
    """
    Cuenta cuántas veces se usó cada 'accion_ejecutada' en las últimas
    'limite_filas' interacciones registradas -da una foto de qué módulos
    se están usando más recientemente-.
    """
    conn = None
    try:
        conn = obtener_conexion_pool()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT accion_ejecutada, fecha
            FROM historial_interacciones
            ORDER BY fecha DESC
            LIMIT %s;
            """,
            (limite_filas,),
        )
        filas = cur.fetchall()
        cur.close()
    except Exception as e:
        print(f"[Rendimiento Módulos] Error consultando historial: {e}")
        return {}
    finally:
        if conn:
            liberar_conexion(conn)

    conteo = Counter(fila[0] or "DESCONOCIDO" for fila in filas)
    ultima_fecha_por_modulo = {}
    for accion, fecha in filas:
        clave = accion or "DESCONOCIDO"
        if clave not in ultima_fecha_por_modulo:
            ultima_fecha_por_modulo[clave] = fecha.isoformat() if fecha else None

    return {
        modulo: {"usos": cantidad, "ultimo_uso": ultima_fecha_por_modulo.get(modulo)}
        for modulo, cantidad in conteo.most_common()
    }