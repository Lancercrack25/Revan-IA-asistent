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
manejador_comando_coder_callback = None
manejador_comando_creative_callback = None
# Contador global de actividad por agente/módulo
METRICAS_AGENTES = {
    "coder": 0,
    "creative": 0,
    "system": 0,
    "orchestrator": 0
}

def registrar_actividad_agente(agente: str):
    """Incrementa el contador de llamadas cuando un agente procesa un comando."""
    clave = agente.lower()
    if clave in METRICAS_AGENTES:
        METRICAS_AGENTES[clave] += 1

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
CARPETA_SOUNDS = os.path.join(RAIZ_SRC, "Sounds") 

if os.path.exists(CARPETA_WEB):
    app.mount("/static", StaticFiles(directory=CARPETA_WEB), name="static")

if os.path.exists(CARPETA_STYLES):
    app.mount("/styles", StaticFiles(directory=CARPETA_STYLES), name="styles")

if os.path.exists(CARPETA_SOUNDS):
    app.mount("/src/Sounds", StaticFiles(directory=CARPETA_SOUNDS), name="sounds")

# --- FUNCIÓN AUXILIAR PARA SERVIR HTMLs ---
def servir_html_modulo(nombre_archivo: str):
    """Carga y retorna un archivo HTML existente en la carpeta web."""
    ruta_archivo = os.path.join(CARPETA_WEB, nombre_archivo)
    if os.path.exists(ruta_archivo):
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(
        content=f"<h1>Error: {nombre_archivo} no encontrado en src/Interfaces/web</h1>",
        status_code=404,
    )

# --- RUTAS PRINCIPALES DE NAVEGACIÓN ---
@app.get("/")
async def obtener_dashboard():
    return servir_html_modulo("dashboard.html")

@app.get("/esfera")
async def obtener_index():
    return servir_html_modulo("index.html")

@app.get("/coder")
async def obtener_coder():
    return servir_html_modulo("coder_interface.html")

@app.get("/creative")
async def obtener_creative():
    return servir_html_modulo("creative_interface.html")

@app.get("/coder_interface.html")
async def obtener_coder_interface():
    return servir_html_modulo("coder_interface.html")

@app.get("/creative_interface.html")
async def obtener_creative_interface():
    return servir_html_modulo("creative_interface.html")

# --- RUTAS DE INFORMACIÓN DE MÓDULOS ---
@app.get("/modulos/camera")
async def info_camera(): return servir_html_modulo("info_camara.html")

@app.get("/modulos/databases")
async def info_databases(): return servir_html_modulo("info_databases.html")

@app.get("/modulos/mails")
async def info_mails(): return servir_html_modulo("info_mails.html")

@app.get("/modulos/network")
async def info_network(): return servir_html_modulo("info_network.html")

@app.get("/modulos/phone")
async def info_phone(): return servir_html_modulo("info_phone.html")

@app.get("/modulos/sounds")
async def info_sounds(): return servir_html_modulo("info_sounds.html")

@app.get("/modulos/training")
async def info_training(): return servir_html_modulo("info_training.html")

@app.get("/modulos/automation")
async def info_automation(): return servir_html_modulo("info_automation.html")

@app.get("/modulos/security")
async def info_security(): return servir_html_modulo("info_security.html")

@app.get("/modulos/social")
async def info_social(): return servir_html_modulo("info_social.html")

@app.get("/modulos/inspector")
async def info_inspector(): return servir_html_modulo("info_inspector.html")

@app.get("/modulos/electronics")
async def info_electronics(): return servir_html_modulo("info_electronics.html")

# --- REGISTRO DE MANEJADORES ---
def registrar_manejador_comando_texto(callback):
    """Permite a main.py registrar la función que procesará los textos enviados desde el chat del Dashboard."""
    global manejador_comando_texto_callback
    manejador_comando_texto_callback = callback

def registrar_manejador_comando_coder(callback):
    """Registra la función que procesa comandos escritos en la terminal de la página dedicada del Coder Agent (/coder)."""
    global manejador_comando_coder_callback
    manejador_comando_coder_callback = callback

def registrar_manejador_comando_creative(callback):
    """Registra la función que procesa prompts escritos en la página dedicada del Creative Agent (/creative)."""
    global manejador_comando_creative_callback
    manejador_comando_creative_callback = callback

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
    print("[WebSocket]: Cliente (Dashboard/Esfera/Coder/Creative/Productividad) conectado al canal de control.")

    try:
        while True:
            data_raw = await websocket.receive_text()
            try:
                data = json.loads(data_raw)
                tipo_mensaje = data.get("type")

                # Comando de texto enviado desde el chat general del Dashboard
                if tipo_mensaje in ["text_command", "comando_texto"]:
                    prompt = data.get("content") or data.get("texto")
                    print(f"[WebSocket Text]: Orden recibida desde UI -> '{prompt}'")

                    if manejador_comando_texto_callback and prompt:
                        if asyncio.iscoroutinefunction(manejador_comando_texto_callback):
                            asyncio.create_task(manejador_comando_texto_callback(prompt))
                        else:
                            manejador_comando_texto_callback(prompt)
                # Comando escrito en la terminal dedicada del Coder Agent (/coder)
                elif tipo_mensaje == "coder_command":
                    prompt = data.get("content")
                    print(f"[WebSocket Coder]: Orden recibida desde UI dedicada -> '{prompt}'")
                    registrar_actividad_agente("coder")

                    if manejador_comando_coder_callback and prompt:
                        if asyncio.iscoroutinefunction(manejador_comando_coder_callback):
                            asyncio.create_task(manejador_comando_coder_callback(prompt))
                        else:
                            manejador_comando_coder_callback(prompt)

                # Prompt escrito en la terminal dedicada del Creative Agent (/creative)
                elif tipo_mensaje == "creative_command":
                    prompt = data.get("content")
                    print(f"[WebSocket Creative]: Orden recibida desde UI dedicada -> '{prompt}'")
                    registrar_actividad_agente("creative")

                    if manejador_comando_creative_callback and prompt:
                        if asyncio.iscoroutinefunction(manejador_comando_creative_callback):
                            asyncio.create_task(manejador_comando_creative_callback(prompt))
                        else:
                            manejador_comando_creative_callback(prompt)

            except json.JSONDecodeError:
                pass

    except (WebSocketDisconnect, Exception):
        pass
    finally:
        conexiones_activas.discard(websocket)
        print("[WebSocket]: Cliente desconectado.")

# --- TRANSMISIONES BROADCAST ---
async def cambiar_estado_esfera(estado: str, color_hex: str):
    if not conexiones_activas: return
    paquete = json.dumps({"tipo": "estado", "estado": estado, "color": color_hex})
    for ws in list(conexiones_activas):
        try: await ws.send_text(paquete)
        except Exception: conexiones_activas.discard(ws)

async def actualizar_manipulacion_esfera(rot_x: float, rot_y: float, escala: float):
    if not conexiones_activas: return
    paquete = json.dumps({"tipo": "manipulacion", "rotX": rot_x, "rotY": rot_y, "escala": escala})
    for ws in list(conexiones_activas):
        try: await ws.send_text(paquete)
        except Exception: conexiones_activas.discard(ws)

async def actualizar_chat_dashboard(rol: str, texto: str):
    """Envía mensajes del historial de conversación al Dashboard web."""
    if not conexiones_activas: return
    paquete = json.dumps({"tipo": "chat", "rol": rol, "texto": texto})
    for ws in list(conexiones_activas):
        try: await ws.send_text(paquete)
        except Exception: conexiones_activas.discard(ws)

async def enviar_respuesta_coder(texto: str):
    """Envía el resultado del Coder Agent de vuelta a la terminal de /coder."""
    if not conexiones_activas: return
    paquete = json.dumps({"tipo": "coder_response", "texto": texto})
    for ws in list(conexiones_activas):
        try: await ws.send_text(paquete)
        except Exception: conexiones_activas.discard(ws)

async def enviar_respuesta_creative(texto: str):
    """Envía el resultado del Creative Agent de vuelta al canvas de /creative."""
    if not conexiones_activas: return
    paquete = json.dumps({"tipo": "creative_response", "texto": texto})
    for ws in list(conexiones_activas):
        try: await ws.send_text(paquete)
        except Exception: conexiones_activas.discard(ws)

async def actualizar_rendimiento(datos: dict):
    """Envía el snapshot de rendimiento (hardware/agentes/módulos) al dashboard."""
    if not conexiones_activas: return
    paquete = json.dumps({"tipo": "rendimiento_update", "datos": datos})
    for ws in list(conexiones_activas):
        try: await ws.send_text(paquete)
        except Exception: conexiones_activas.discard(ws)

# --- PUENTES MULTIHILO EXTERNOS ---
def transmitir_desde_hilo_externo(estado: str, color_hex: str):
    global loop_real_servidor
    if loop_real_servidor and loop_real_servidor.is_running():
        asyncio.run_coroutine_threadsafe(cambiar_estado_esfera(estado, color_hex), loop_real_servidor)

def transmitir_manipulacion_desde_hilo_externo(rot_x: float, rot_y: float, escala: float = 1.0):
    global loop_real_servidor
    if loop_real_servidor and loop_real_servidor.is_running():
        asyncio.run_coroutine_threadsafe(actualizar_manipulacion_esfera(rot_x, rot_y, escala), loop_real_servidor)

def transmitir_chat_desde_hilo_externo(rol: str, texto: str):
    """Puente multihilo para enviar respuestas de los agentes hacia la interfaz web."""
    global loop_real_servidor
    if loop_real_servidor and loop_real_servidor.is_running():
        asyncio.run_coroutine_threadsafe(actualizar_chat_dashboard(rol, texto), loop_real_servidor)

def transmitir_respuesta_coder_desde_hilo_externo(texto: str):
    global loop_real_servidor
    if loop_real_servidor and loop_real_servidor.is_running():
        asyncio.run_coroutine_threadsafe(enviar_respuesta_coder(texto), loop_real_servidor)

def transmitir_respuesta_creative_desde_hilo_externo(texto: str):
    global loop_real_servidor
    if loop_real_servidor and loop_real_servidor.is_running():
        asyncio.run_coroutine_threadsafe(enviar_respuesta_creative(texto), loop_real_servidor)

def transmitir_rendimiento_desde_hilo_externo(datos: dict):
    global loop_real_servidor
    if loop_real_servidor and loop_real_servidor.is_running():
        asyncio.run_coroutine_threadsafe(actualizar_rendimiento(datos), loop_real_servidor)

def iniciar_servidor_ui():
    config = uvicorn.Config(app=app, host="127.0.0.1", port=8000, log_level="warning")
    return uvicorn.Server(config)