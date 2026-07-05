import os
import json
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# Mapeo Absoluto Adaptado al Árbol de Trabajo Real
CARPETA_INTERFACES = os.path.dirname(os.path.abspath(__file__))
CARPETA_WEB = os.path.join(CARPETA_INTERFACES, "web")
RAIZ_SRC = os.path.dirname(CARPETA_INTERFACES)
CARPETA_STYLES = os.path.join(RAIZ_SRC, "Gui", "styles")

# Montura de Alias Virtuales de Red
app.mount("/static", StaticFiles(directory=CARPETA_WEB), name="static")
app.mount("/styles", StaticFiles(directory=CARPETA_STYLES), name="styles")

conexiones_activas = []

@app.get("/")
async def obtener_index():
    ruta_index = os.path.join(CARPETA_WEB, "index.html")
    if os.path.exists(ruta_index):
        with open(ruta_index, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content=f"<h1>⚠️ Error: index.html no encontrado</h1>", status_code=404)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    conexiones_activas.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        conexiones_activas.remove(websocket)
    except Exception:
        if websocket in conexiones_activas:
            conexiones_activas.remove(websocket)

async def cambiar_estado_esfera(estado: str, color_hex: str):
    """Enruta y distribuye los estados hacia el cliente JavaScript en tiempo real."""
    if not conexiones_activas:
        return
        
    paquete = {
        "estado": estado,
        "color": color_hex
    }
    
    for conexion in conexiones_activas:
        try:
            await conexion.send_text(json.dumps(paquete))
        except Exception:
            pass

def iniciar_servidor_ui():
    config = uvicorn.Config(
        app=app, 
        host="127.0.0.1", 
        port=8000, 
        log_level="warning"
    )
    return uvicorn.Server(config)