import asyncio
import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

app = FastAPI()
conexion_interfaz = None

# Apuntamos dinámicamente a la carpeta 'web' que está al mismo nivel de este archivo
DIRECTORIO_WEB = os.path.join(os.path.dirname(__file__), "web")
app.mount("/static", StaticFiles(directory=DIRECTORIO_WEB), name="static")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global conexion_interfaz
    await websocket.accept()
    conexion_interfaz = websocket
    print("🛸 REVAN_CORE: Esfera neuronal 3D vinculada exitosamente.")
    try:
        while True:
            # Mantiene el pulso del WebSocket activo
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("❌ REVAN_CORE: Esfera neuronal 3D desconectada.")
        conexion_interfaz = None

async def cambiar_estado_esfera(estado: str, color_hex: str):
    """Envía de forma inmediata la instrucción de animación y color a la esfera web."""
    global conexion_interfaz
    if conexion_interfaz:
        payload = {
            "estado": estado.upper(),
            "color": color_hex
        }
        try:
            await conexion_interfaz.send_text(json.dumps(payload))
        except Exception as e:
            print(f"⚠️ Error al transmitir datos a la esfera: {e}")

def iniciar_servidor_ui():
    """Inicializa la configuración de Uvicorn para embeber el servidor en un hilo secundario."""
    import uvicorn
    # Levantamos el servidor en localhost puerto 8000
    config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="warning")
    return uvicorn.Server(config)