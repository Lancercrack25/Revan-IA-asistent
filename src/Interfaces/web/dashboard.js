// Conexión WebSocket
const ws = new WebSocket(`ws://${window.location.host}/ws`);

ws.onopen = () => {
    console.log("[Command Center]: Conectado al servidor WebSocket.");
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Respuesta de Revan:", data);
};

ws.onerror = (error) => {
    console.error("Error en WebSocket:", error);
};

// Cambiar entre la Vista Táctica y la Esfera 3D
function switchView(viewName, btn) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById(`view-${viewName}`).classList.add('active');
    btn.classList.add('active');
}

// Enviar comandos por texto
function sendCommand() {
    const input = document.getElementById('text-command');
    const message = input.value.trim();
    if (message) {
        ws.send(JSON.stringify({ type: "text_command", content: message }));
        input.value = "";
    }
}

// Capturar la tecla Enter en el input de texto
function handleKeyPress(e) {
    if (e.key === 'Enter') {
        sendCommand();
    }
}