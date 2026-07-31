/* ==========================================================================
   DASHBOARD KERNEL - HUD CONTROLLER
   ========================================================================== */

let ws = null;
let reconnectTimer = null;

/* --------------------------------------------------------------------------
   0. AUDIO ENGINE & SFX SYSTEM
   -------------------------------------------------------------------------- */
const soundHover = new Audio('../../Sounds/welcome/hovers.mp3');
const soundClick = new Audio('../../Sounds/welcome/close.mp3'); 
const soundSection = new Audio('../../Sounds/welcome/sections.mp3');

// Configuración de volúmenes suaves
soundHover.volume = 0.2;
soundClick.volume = 0.4;
soundSection.volume = 0.5;

function playHoverSFX() {
    soundHover.currentTime = 0;
    soundHover.play().catch(() => {});
}

function playClickSFX() {
    soundClick.currentTime = 0;
    soundClick.play().catch(() => {});
}

function playSectionSFX() {
    soundSection.currentTime = 0;
    soundSection.play().catch(() => {});
}

/* --------------------------------------------------------------------------
   INICIALIZACIÓN DEL KERNEL
   -------------------------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
    initParticles();
    initTilt();
    setupModuleNavigation();
    setupInputEvents();
    conectarWebSocket();
    startMetricsSimulation();
    setupAudioListeners(); // Init SFX
});

function setupAudioListeners() {
    // 1. Hover y Click para interactivos y botones de módulos
    const elementosInteractivos = document.querySelectorAll('button, a, .card, .module-card, .hud-btn, input');
    
    elementosInteractivos.forEach(elemento => {
        elemento.addEventListener('mouseenter', playHoverSFX);
        elemento.addEventListener('click', playClickSFX);
    });

    // 2. Sonido de despliegue de sección/pestañas
    const botonesSeccion = document.querySelectorAll('.nav-link, .open-info-btn, [onClick*="switchView"]');
    botonesSeccion.forEach(btn => {
        btn.addEventListener('click', playSectionSFX);
    });
}

/* --------------------------------------------------------------------------
   1. AMBIENTE VISUAL (PARTICLES & TILT)
   -------------------------------------------------------------------------- */
function initParticles() {
    if (typeof particlesJS !== "undefined") {
        particlesJS("particles-js", {
            particles: {
                number: { value: 70, density: { enable: true, value_area: 900 } },
                color: { value: "#00f0ff" },
                shape: { type: "circle" },
                opacity: { value: 0.2, random: true },
                size: { value: 2, random: true },
                line_linked: {
                    enable: true,
                    distance: 130,
                    color: "#00f0ff",
                    opacity: 0.12,
                    width: 1
                },
                move: {
                    enable: true,
                    speed: 1,
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
                    grab: { distance: 140, line_linked: { opacity: 0.35 } }
                }
            },
            retina_detect: true
        });
    }
}

function initTilt() {
    if (typeof VanillaTilt !== "undefined") {
        VanillaTilt.init(document.querySelectorAll("[data-tilt]"), {
            max: 8,
            speed: 400,
            glare: true,
            "max-glare": 0.2,
            scale: 1.01
        });
    }
}

/* --------------------------------------------------------------------------
   2. GESTIÓN DE VISTAS (TÁCTICO VS NÚCLEO 3D)
   -------------------------------------------------------------------------- */
function switchView(vista) {
    playSectionSFX(); // Trigger SFX al cambiar vista táctica / esfera
    const vTactico = document.getElementById("view-tactico");
    const vEsfera = document.getElementById("view-esfera");
    const bTactico = document.getElementById("btn-tactico");
    const bEsfera = document.getElementById("btn-esfera");

    if (vista === "tactico") {
        if (vTactico) vTactico.classList.add("active");
        if (vEsfera) vEsfera.classList.remove("active");
        if (bTactico) bTactico.classList.add("active");
        if (bEsfera) bEsfera.classList.remove("active");
    } else if (vista === "esfera") {
        if (vTactico) vTactico.classList.remove("active");
        if (vEsfera) vEsfera.classList.add("active");
        if (bTactico) bTactico.classList.remove("active");
        if (bEsfera) bEsfera.classList.add("active");

        const iframe = document.getElementById("iframe-esfera");
        if (iframe && !iframe.getAttribute("src")) {
            iframe.src = "/esfera";
        }
    }
}

/* --------------------------------------------------------------------------
   3. NAVEGACIÓN Y REDIRECCIÓN DE MÓDULOS
   -------------------------------------------------------------------------- */
function setupModuleNavigation() {
    const rutasModulos = {
        'btn-camera': '/modulos/camera',
        'btn-phone': '/modulos/phone',
        'btn-network': '/modulos/network',
        'btn-mails': '/modulos/mails',
        'btn-database': '/modulos/databases',
        'btn-sounds': '/modulos/sounds',
        'btn-training': '/modulos/training',
        'btn-automation': '/modulos/automation',
        'btn-security': '/modulos/security',
        'btn-social': '/modulos/social',
        'btn-inspector': '/modulos/inspector',
        'btn-electronics': '/modulos/electronics'
    };

    Object.entries(rutasModulos).forEach(([id, url]) => {
        const card = document.getElementById(id);
        if (card) {
            card.addEventListener("click", () => {
                addLog(`Accediendo al módulo: ${id.replace('btn-', '').toUpperCase()}...`, "system");
                window.location.href = url;
            });
        }
    });
}

/* --------------------------------------------------------------------------
   4. WEBSOCKET & TELEMETRÍA EN TIEMPO REAL
   -------------------------------------------------------------------------- */
function conectarWebSocket() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        addLog("Enlace neural establecido con la red.", "system");
        updateLiveBeacon(true);
        if (reconnectTimer) clearInterval(reconnectTimer);
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.tipo === "chat" || data.tipo === "log") {
                const tag = data.rol ? data.rol.toUpperCase() : "SYS";
                addLog(`[${tag}]: ${data.texto}`, data.rol || "system");
            }
        } catch (e) {
            addLog(`> RAW: ${event.data}`, "system");
        }
    };

    ws.onclose = () => {
        addLog("Conexión interrumpida. Reintentando...", "system");
        updateLiveBeacon(false);
        reconnectTimer = setTimeout(conectarWebSocket, 4000);
    };

    ws.onerror = (err) => {
        console.error("WebSocket Error:", err);
        ws.close();
    };
}

/* --------------------------------------------------------------------------
   5. TERMINAL DE COMANDOS
   -------------------------------------------------------------------------- */
function setupInputEvents() {
    const input = document.getElementById("cmd-input");
    const btn = document.getElementById("btn-send");

    if (input) {
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") enviarComando();
        });
    }

    if (btn) {
        btn.addEventListener("click", enviarComando);
    }
}

function enviarComando() {
    const input = document.getElementById("cmd-input");
    if (!input) return;

    const texto = input.value.trim();

    if (texto) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: "text_command",
                content: texto
            }));
            addLog(`ORDEN: ${texto}`, "user");
        } else {
            addLog(`[OFFLINE]: No se pudo transmitir "${texto}"`, "system");
        }
        input.value = "";
    }
}

function addLog(msg, type = "system") {
    const logBox = document.getElementById("telemetry-log");
    if (!logBox) return;

    const div = document.createElement("div");
    div.className = `log-entry ${type}`;
    
    const timestamp = new Date().toLocaleTimeString('es-ES', { hour12: false });
    div.textContent = `[${timestamp}] ${msg}`;
    
    logBox.appendChild(div);
    logBox.scrollTop = logBox.scrollHeight;
}

function startMetricsSimulation() {
    const cpuFill = document.querySelector(".cpu-fill");
    
    setInterval(() => {
        if (cpuFill) {
            const randomCpu = Math.floor(Math.random() * (65 - 28 + 1)) + 28;
            cpuFill.style.width = `${randomCpu}%`;
        }
    }, 2500);
}

function updateLiveBeacon(online) {
    const beacon = document.querySelector(".beacon");
    const statusText = document.querySelector(".live-status span");

    if (beacon && statusText) {
        if (online) {
            beacon.style.background = "var(--green)";
            beacon.style.boxShadow = "0 0 10px var(--green)";
            statusText.textContent = "ONLINE";
            statusText.style.color = "var(--green)";
        } else {
            beacon.style.background = "var(--red)";
            beacon.style.boxShadow = "0 0 10px var(--red)";
            statusText.textContent = "OFFLINE";
            statusText.style.color = "var(--red)";
        }
    }
}