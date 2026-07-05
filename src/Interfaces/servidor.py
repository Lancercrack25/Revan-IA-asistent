import os
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI()

# 🛠️ CORRECCIÓN DE RUTAS TÁCTICAS:
# os.path.abspath(__file__) -> src/Interfaces/servidor.py
# os.path.dirname(...)       -> src/Interfaces/
CARPETA_INTERFACES = os.path.dirname(os.path.abspath(__file__))

# Bajamos directo a la carpeta 'web' que está ahí al lado
CARPETA_WEB = os.path.join(CARPETA_INTERFACES, "web")

# Subimos dos niveles para llegar a 'src' y luego entramos a 'Gui/styles'
BASE_DIR = os.path.dirname(os.path.dirname(CARPETA_INTERFACES))
CARPETA_STYLES = os.path.join(BASE_DIR, "src", "Gui", "styles")

# Montamos los recursos estáticos con las rutas corregidas
app.mount("/static", StaticFiles(directory=CARPETA_WEB), name="static")
app.mount("/styles", StaticFiles(directory=CARPETA_STYLES), name="styles")

@app.get("/")
async def obtener_index():
    ruta_index = os.path.join(CARPETA_WEB, "index.html")
    if os.path.exists(ruta_index):
        with open(ruta_index, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content=f"<h1>⚠️ Error: index.html no encontrado en: {CARPETA_WEB}</h1>", status_code=404)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(data)
    except Exception:
        pass