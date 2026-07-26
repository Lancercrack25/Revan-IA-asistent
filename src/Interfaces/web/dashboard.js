let ws = null;

document.addEventListener("DOMContentLoaded", () => {
    initParticles();
    conectarWebSocket();
    setupInputEvents();
});

// --- INICIALIZAR LIBRERÍA DE PARTÍCULAS (PARTICLES.JS) ---
function initParticles() {
    particlesJS("particles-js", {
        particles: {
            number: { value: 65, density: { enable: true, value_area: 800 } },
            color: { value: "#00f0ff" },
            shape: { type: "circle" },
            opacity: { value: 0.25, random: true },
            size: { value: 2.5, random: true },
            line_linked: {
                enable: true,
                distance: 140,
                color: "#00f0ff",
                opacity: 0.15,
                width: 1
            },
            move: {
                enable: true,
                speed: 1.2,
                direction: "none",
                random: true,
                out_mode: "out"
            }
        },
        interactivity: {
            detect_on: "canvas",
            events: {
                onhover: { enable: true, mode: "grab" },
                onclick: { enable: true, mode: "push" }
            },
            modes: {
                grab: { distance: 160, line_linked: { opacity: 0.4 } }
            }
        },
        retina_detect: true
    });
}

// --- CONEXIÓN WEBSOCKET Y SINCRONIZACIÓN ---
function conectarWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        addLog("Conexión de red establecida con el núcleo.", "system");
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.tipo === "chat") {
                const tipoLog = data.rol === "usuario" ? "user" : "revan";
                addLog(`[${data.rol.toUpperCase()}]: ${data.texto}`, tipoLog);
            }
        } catch (e) {
            console.error("Error al decodificar mensaje WS:", e);
        }
    };

    ws.onclose = () => {
        addLog("Conexión perdida. Reintentando enlace...", "system");
        setTimeout(conectarWebSocket, 3000);
    };
}

// --- CAMBIO DE VISTAS TÁCTICA / NÚCLEO 3D ---
function switchView(vista) {
    const vTactico = document.getElementById("view-tactico");
    const vEsfera = document.getElementById("view-esfera");
    const bTactico = document.getElementById("btn-tactico");
    const bEsfera = document.getElementById("btn-esfera");

    if (vista === "tactico") {
        vTactico.classList.add("active");
        vEsfera.classList.remove("active");
        bTactico.classList.add("active");
        bEsfera.classList.remove("active");
    } else if (vista === "esfera") {
        vTactico.classList.remove("active");
        vEsfera.classList.add("active");
        bTactico.classList.remove("active");
        bEsfera.classList.add("active");

        const iframe = document.getElementById("iframe-esfera");
        if (iframe && !iframe.src) {
            iframe.src = "/esfera";
        }
    }
}

// --- ENVÍO DE COMANDOS ---
function enviarComando() {
    const input = document.getElementById("cmd-input");
    const texto = input.value.trim();

    if (texto && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: "text_command",
            content: texto
        }));
        addLog(`[ORDEN]: ${texto}`, "user");
        input.value = "";
    }
}

function setupInputEvents() {
    const input = document.getElementById("cmd-input");
    if (input) {
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") enviarComando();
        });
    }
}

function addLog(msg, type = "system") {
    const logBox = document.getElementById("telemetry-log");
    if (logBox) {
        const div = document.createElement("div");
        div.className = `log-entry ${type}`;
        div.textContent = `> ${msg}`;
        logBox.appendChild(div);
        logBox.scrollTop = logBox.scrollHeight;
    }
}