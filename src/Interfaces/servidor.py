import os
import json
import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

conexiones_activas: set[WebSocket] = set()
loop_real_servidor = None


# Manejo moderno del ciclo de vida del servidor (Lifespan)
@asynccontextmanager
async def lifespan(app_fastapi: FastAPI):
    global loop_real_servidor
    loop_real_servidor = asyncio.get_running_loop()
    print("[Servidor Web]: Event Loop de FastAPI vinculado con éxito.")
    yield


app = FastAPI(lifespan=lifespan)

# Mapeo Absoluto Adaptado al Árbol de Trabajo Real
CARPETA_INTERFACES = os.path.dirname(os.path.abspath(__file__))
CARPETA_WEB = os.path.join(CARPETA_INTERFACES, "web")
RAIZ_SRC = os.path.dirname(CARPETA_INTERFACES)
CARPETA_STYLES = os.path.join(RAIZ_SRC, "Gui", "styles")

if os.path.exists(CARPETA_WEB):
    app.mount("/static", StaticFiles(directory=CARPETA_WEB), name="static")

if os.path.exists(CARPETA_STYLES):
    app.mount("/styles", StaticFiles(directory=CARPETA_STYLES), name="styles")


@app.get("/")
async def obtener_index():
    ruta_index = os.path.join(CARPETA_WEB, "index.html")
    if os.path.exists(ruta_index):
        with open(ruta_index, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content="<h1> Error: index.html no encontrado en src/Interfaces/web</h1>",
        status_code=404,
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global loop_real_servidor

    # Garantizar la captura del loop en el primer cliente que se conecta
    if loop_real_servidor is None:
        try:
            loop_real_servidor = asyncio.get_running_loop()
        except RuntimeError:
            pass

    await websocket.accept()
    conexiones_activas.add(websocket)
    print("[WebSocket]: Esfera 3D vinculada al canal de control.")

    try:
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        conexiones_activas.discard(websocket)
        print(" [WebSocket]: Esfera 3D desconectada.")


async def cambiar_estado_esfera(estado: str, color_hex: str):
    """Transmite el paquete JSON a todas las conexiones WebSocket vivas."""
    if not conexiones_activas:
        return

    # Se agregó "tipo": "estado" para que el frontend pueda distinguir este
    # paquete del nuevo canal de manipulación, sin romper lo que ya lee
    # (estado/color siguen presentes exactamente igual que antes).
    paquete = json.dumps({"tipo": "estado", "estado": estado, "color": color_hex})
    desconectados = set()

    for conexion in list(conexiones_activas):
        try:
            await conexion.send_text(paquete)
        except Exception:
            desconectados.add(conexion)

    # Limpieza de sockets muertos
    for ws in desconectados:
        conexiones_activas.discard(ws)


async def actualizar_manipulacion_esfera(rot_x: float, rot_y: float, escala: float):
    """
    Transmite rotación/escala calculadas a partir del tracking de mano
    (ver src/Camara/control_esfera_manos.py). Va en un paquete separado del
    de estado/color, distinguible por 'tipo': 'manipulacion'.
    """
    if not conexiones_activas:
        return

    paquete = json.dumps({"tipo": "manipulacion", "rotX": rot_x, "rotY": rot_y, "escala": escala})
    desconectados = set()

    for conexion in list(conexiones_activas):
        try:
            await conexion.send_text(paquete)
        except Exception:
            desconectados.add(conexion)

    for ws in desconectados:
        conexiones_activas.discard(ws)


def transmitir_desde_hilo_externo(estado: str, color_hex: str):
    """Puente ultra-seguro para inyectar estados desde cualquier hilo externo."""
    global loop_real_servidor

    # Reintento táctico de captura de loop si la llamada ocurrió muy temprano
    if loop_real_servidor is None:
        try:
            loop_real_servidor = asyncio.get_event_loop()
        except RuntimeError:
            pass

    if loop_real_servidor and loop_real_servidor.is_running():
        asyncio.run_coroutine_threadsafe(
            cambiar_estado_esfera(estado, color_hex), loop_real_servidor
        )
    else:
        print(
            f"[WebSocket Warn]: Se intentó enviar '{estado}' antes de que el servidor FastAPI estuviera listo."
        )


def transmitir_manipulacion_desde_hilo_externo(rot_x: float, rot_y: float, escala: float = 1.0):
    """Mismo patrón que transmitir_desde_hilo_externo, pero para el canal de manipulación por mano."""
    global loop_real_servidor

    if loop_real_servidor is None:
        try:
            loop_real_servidor = asyncio.get_event_loop()
        except RuntimeError:
            pass

    if loop_real_servidor and loop_real_servidor.is_running():
        asyncio.run_coroutine_threadsafe(
            actualizar_manipulacion_esfera(rot_x, rot_y, escala), loop_real_servidor
        )


def iniciar_servidor_ui():
    config = uvicorn.Config(
        app=app, host="127.0.0.1", port=8000, log_level="warning"
    )
    return uvicorn.Server(config)