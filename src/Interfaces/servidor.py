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
manejador_comando_texto_callback = None


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


# --- FUNCIÓN AUXILIAR PARA SERVIR HTMLs ---

def servir_html_modulo(nombre_archivo: str):
    """Carga y retorna un archivo HTML existente en la carpeta web."""
    ruta_archivo = os.path.join(CARPETA_WEB, nombre_archivo)
    if os.path.exists(ruta_archivo):
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content=f"<h1> Error: {nombre_archivo} no encontrado en src/Interfaces/web</h1>",
        status_code=404,
    )


# --- RUTAS DE NAVEGACIÓN ---

@app.get("/")
async def obtener_dashboard():
    """Ruta Principal: Carga el Dashboard Táctico (Command Center)"""
    return servir_html_modulo("dashboard.html")


@app.get("/esfera")
async def obtener_index():
    """Ruta secundaria: Carga la esfera 3D dentro del iframe del Dashboard"""
    return servir_html_modulo("index.html")


# --- RUTAS DE INFORMACIÓN DE MÓDULOS ---

@app.get("/modulos/databases")
async def info_databases():
    return servir_html_modulo("info_databases.html")


@app.get("/modulos/mails")
async def info_mails():
    return servir_html_modulo("info_mails.html")


@app.get("/modulos/network")
async def info_network():
    return servir_html_modulo("info_network.html")


@app.get("/modulos/phone")
async def info_phone():
    return servir_html_modulo("info_phone.html")


@app.get("/modulos/sounds")
async def info_sounds():
    return servir_html_modulo("info_sounds.html")


@app.get("/modulos/training")
async def info_training():
    return servir_html_modulo("info_training.html")


# --- REGISTRO DE MANEJADORES ---

def registrar_manejador_comando_texto(callback):
    """Permite a main.py registrar la función que procesará los textos enviados desde la web UI."""
    global manejador_comando_texto_callback
    manejador_comando_texto_callback = callback


# --- WEBSOCKET UNIFICADO ---

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global loop_real_servidor

    if loop_real_servidor is None:
        try:
            loop_real_servidor = asyncio.get_running_loop()
        except RuntimeError:
            pass

    await websocket.accept()
    conexiones_activas.add(websocket)
    print("[WebSocket]: Cliente (Dashboard/Esfera) conectado al canal de control.")

    try:
        while True:
            data_raw = await websocket.receive_text()
            try:
                data = json.loads(data_raw)
                
                # Procesa comando de texto enviado desde el input del Dashboard
                if data.get("type") in ["text_command", "comando_texto"]:
                    prompt = data.get("content") or data.get("texto")
                    print(f"[WebSocket Text]: Orden recibida desde UI -> '{prompt}'")
                    
                    if manejador_comando_texto_callback and prompt:
                        manejador_comando_texto_callback(prompt)

            except json.JSONDecodeError:
                pass

    except (WebSocketDisconnect, Exception):
        pass
    finally:
        conexiones_activas.discard(websocket)
        print("[WebSocket]: Cliente desconectado.")


# --- TRANSMISIONES BROADCAST ---

async def cambiar_estado_esfera(estado: str, color_hex: str):
    if not conexiones_activas:
        return

    paquete = json.dumps({"tipo": "estado", "estado": estado, "color": color_hex})
    desconectados = set()

    for conexion in list(conexiones_activas):
        try:
            await conexion.send_text(paquete)
        except Exception:
            desconectados.add(conexion)

    for ws in desconectados:
        conexiones_activas.discard(ws)


async def actualizar_manipulacion_esfera(rot_x: float, rot_y: float, escala: float):
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


async def actualizar_chat_dashboard(rol: str, texto: str):
    """Envía mensajes del historial de conversación al Dashboard web."""
    if not conexiones_activas:
        return

    paquete = json.dumps({"tipo": "chat", "rol": rol, "texto": texto})
    desconectados = set()

    for conexion in list(conexiones_activas):
        try:
            await conexion.send_text(paquete)
        except Exception:
            desconectados.add(conexion)

    for ws in desconectados:
        conexiones_activas.discard(ws)


# --- PUENTES MULTIHILO EXTERNOS ---

def transmitir_desde_hilo_externo(estado: str, color_hex: str):
    global loop_real_servidor

    if loop_real_servidor is None:
        try:
            loop_real_servidor = asyncio.get_event_loop()
        except RuntimeError:
            pass

    if loop_real_servidor and loop_real_servidor.is_running():
        asyncio.run_coroutine_threadsafe(
            cambiar_estado_esfera(estado, color_hex), loop_real_servidor
        )


def transmitir_manipulacion_desde_hilo_externo(rot_x: float, rot_y: float, escala: float = 1.0):
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


def transmitir_chat_desde_hilo_externo(rol: str, texto: str):
    """Puente multihilo para enviar mensajes del chat hacia la interfaz web."""
    global loop_real_servidor

    if loop_real_servidor is None:
        try:
            loop_real_servidor = asyncio.get_event_loop()
        except RuntimeError:
            pass

    if loop_real_servidor and loop_real_servidor.is_running():
        asyncio.run_coroutine_threadsafe(
            actualizar_chat_dashboard(rol, texto), loop_real_servidor
        )


def iniciar_servidor_ui():
    config = uvicorn.Config(
        app=app, host="127.0.0.1", port=8000, log_level="warning"
    )
    return uvicorn.Server(config)