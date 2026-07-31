/* ==========================================================================
   DASHBOARD KERNEL - ULTRA-LOW LATENCY AUDIO & HUD SYSTEM
   ========================================================================== */

let ws = null;
let reconnectTimer = null;

/* --------------------------------------------------------------------------
   0. MOTOR DE AUDIO NATIVO (SINTETIZADOR HUD DE LEY - ZERO LAG)
   -------------------------------------------------------------------------- */
const AudioCtx = window.AudioContext || window.webkitAudioContext;
let audioCtx = null;

function initAudioContext() {
    if (!audioCtx) {
        audioCtx = new AudioCtx();
    }
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
}

// Generador de efectos tácticos sintetizados (Garantiza sonido instantáneo de 0ms)
function playToneSFX(type) {
    initAudioContext();
    if (!audioCtx) return;

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    const now = audioCtx.currentTime;

    if (type === 'hover') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(800, now);
        osc.frequency.exponentialRampToValueAtTime(1200, now + 0.04);
        gain.gain.setValueAtTime(0.05, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.04);
        osc.start(now);
        osc.stop(now + 0.04);
    } else if (type === 'click') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(1500, now);
        osc.frequency.exponentialRampToValueAtTime(400, now + 0.08);
        gain.gain.setValueAtTime(0.15, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.08);
        osc.start(now);
        osc.stop(now + 0.08);
    } else if (type === 'section') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(300, now);
        osc.frequency.exponentialRampToValueAtTime(900, now + 0.15);
        gain.gain.setValueAtTime(0.1, now);
        gain.gain.linearRampToValueAtTime(0.01, now + 0.15);
        osc.start(now);
        osc.stop(now + 0.15);
    }
}

function playHoverSFX() { playToneSFX('hover'); }
function playClickSFX() { playToneSFX('click'); }
function playSectionSFX() { playToneSFX('section'); }

// Desbloqueo al primer contacto del usuario
['click', 'keydown', 'mousemove'].forEach(evt => {
    document.addEventListener(evt, () => {
        initAudioContext();
    }, { once: true });
});

/* --------------------------------------------------------------------------
   INICIALIZACIÓN Y EVENTOS
   -------------------------------------------------------------------------- */
document.addEventListener("DOMContentLoaded", () => {
    initParticles();
    initTilt();
    setupModuleNavigation();
    setupInputEvents();
    conectarWebSocket();
    startMetricsSimulation();
    setupGlobalAudioListeners();
});

/* --------------------------------------------------------------------------
   DELEGACIÓN DE AUDIO PERFECTA (HOVER Y CLICK)
   -------------------------------------------------------------------------- */
function setupGlobalAudioListeners() {
    // 1. HOVER Instantáneo
    document.addEventListener('mouseover', (e) => {
        const target = e.target.closest('button, a, .card, .module-card, .keyword-card, .hud-btn, input, [onclick]');
        if (target && !target.dataset.hoverActive) {
            target.dataset.hoverActive = "true";
            playHoverSFX();
            setTimeout(() => delete target.dataset.hoverActive, 100);
        }
    });

    // 2. CLIC Instantáneo (Garantizado)
    document.addEventListener('pointerdown', (e) => {
        const target = e.target.closest('button, a, .card, .module-card, .keyword-card, .hud-btn, .btn-back, [onclick]');
        if (target) {
            playClickSFX();
        }
    });

    // 3. Manejo de enlaces para garantizar que suenen ANTES de cambiar la página
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (link && link.href && !link.href.startsWith('#') && !link.target) {
            e.preventDefault();
            const destination = link.href;
            playClickSFX();
            setTimeout(() => {
                window.location.href = destination;
            }, 90); // Tiempo suficiente para oír el clic sintetizado
        }
    });
}

/* --------------------------------------------------------------------------
   1. AMBIENTE VISUAL (PARTICLES & TILT)
   -------------------------------------------------------------------------- */
function initParticles() {
    if (typeof particlesJS !== "undefined" && document.getElementById("particles-js")) {
        particlesJS("particles-js", {
            particles: {
                number: { value: 50, density: { enable: true, value_area: 900 } },
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
                }
            },
            retina_detect: true
        });
    }
}

function initTilt() {
    if (typeof VanillaTilt !== "undefined") {
        VanillaTilt.init(document.querySelectorAll("[data-tilt]"), {
            max: 6,
            speed: 300,
            glare: true,
            "max-glare": 0.15,
            scale: 1.01
        });
    }
}

/* --------------------------------------------------------------------------
   2. GESTIÓN DE VISTAS (TÁCTICO VS NÚCLEO 3D)
   -------------------------------------------------------------------------- */
function switchView(vista) {
    playSectionSFX();
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
   3. NAVEGACIÓN Y DASHBOARD
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
            card.addEventListener("click", (e) => {
                e.preventDefault();
                playClickSFX();
                addLog(`Accediendo al módulo: ${id.replace('btn-', '').toUpperCase()}...`, "system");
                
                setTimeout(() => {
                    window.location.href = url;
                }, 90);
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
   5. TERMINAL DE COMANDOS Y AUXILIARES
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