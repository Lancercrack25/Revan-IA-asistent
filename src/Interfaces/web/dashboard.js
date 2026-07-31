let ws = null;
let reconnectTimer = null;
const BASE_URL = window.location.origin;

const SOUND_PATHS = {
    hover: `${BASE_URL}/src/Sounds/welcome/hovers.mp3`,
    click: `${BASE_URL}/src/Sounds/welcome/clicks.mp3`,
    section: `${BASE_URL}/src/Sounds/welcome/sections.mp3`
};

let userInteracted = false;

function unlockAudioEngine() {
    if (userInteracted) return;
    userInteracted = true;
    
    const dummy = new Audio(SOUND_PATHS.click);
    dummy.volume = 0.01;
    dummy.play().then(() => dummy.pause()).catch(() => {});
    
    window.removeEventListener('pointerdown', unlockAudioEngine);
    window.removeEventListener('keydown', unlockAudioEngine);
}

window.addEventListener('pointerdown', unlockAudioEngine);
window.addEventListener('keydown', unlockAudioEngine);

// Reproduce audio normal (Hover/Section)
function playDirectSound(type, volume = 0.5) {
    if (!SOUND_PATHS[type]) return;
    try {
        const snd = new Audio(SOUND_PATHS[type]);
        snd.volume = volume;
        snd.play().catch(() => {});
    } catch (e) {}
}

// Reproduce Clic de forma garantizada y ejecuta un callback al terminar o iniciar
function playClickAndNavigate(callbackUrl = null) {
    unlockAudioEngine();
    
    try {
        const clickAudio = new Audio(SOUND_PATHS.click);
        clickAudio.volume = 0.8;

        // Si hay una redirección, esperamos a que el audio inicie/avance
        if (callbackUrl) {
            let navigated = false;

            const goToPage = () => {
                if (!navigated) {
                    navigated = true;
                    window.location.href = callbackUrl;
                }
            };

            // Intentar reproducir y dar tiempo al efecto sonoro
            clickAudio.play().then(() => {
                setTimeout(goToPage, 180); // 180ms para escuchar la ráfaga del clic
            }).catch(() => {
                goToPage(); // Si falla el audio, redirige de todos modos
            });

            // Respaldo por si el archivo de audio tarda en cargar
            setTimeout(goToPage, 250);
        } else {
            clickAudio.play().catch(() => {});
        }
    } catch (e) {
        if (callbackUrl) window.location.href = callbackUrl;
    }
}

function playHoverSFX() { playDirectSound('hover', 0.25); }
function playSectionSFX() { playDirectSound('section', 0.5); }
document.addEventListener("DOMContentLoaded", () => {
    initParticles();
    initTilt();
    setupModuleNavigation();
    setupInputEvents();
    conectarWebSocket();
    startMetricsSimulation();
    setupGlobalAudioListeners();

    // Reproduce sections.mp3 SOLO al entrar a un módulo secundario
    const currentPath = window.location.pathname;
    const isDashboard = currentPath === "/" || currentPath === "/index.html";
    
    if (!isDashboard) {
        setTimeout(() => {
            playSectionSFX();
        }, 150);
    }
});

let currentHoveredElement = null;

function setupGlobalAudioListeners() {
    
    // 1. HOVER ÚNICO
    document.addEventListener('mouseover', (e) => {
        const target = e.target.closest('button, a, .card, .module-card, .keyword-card, .hud-btn, .btn-back, [onclick]');
        
        if (target && target !== currentHoveredElement) {
            currentHoveredElement = target;
            playHoverSFX();
        } else if (!target) {
            currentHoveredElement = null;
        }
    });

    document.addEventListener('mouseout', (e) => {
        const target = e.target.closest('button, a, .card, .module-card, .keyword-card, .hud-btn, .btn-back, [onclick]');
        if (target && e.relatedTarget && !target.contains(e.relatedTarget)) {
            currentHoveredElement = null;
        }
    });

    // 2. INTERCEPTOR DE CLICS PARA ELEMENTOS QUE NO REDIRIGEN (Botones simples/Inputs)
    document.addEventListener('pointerdown', (e) => {
        unlockAudioEngine();
        const target = e.target.closest('button, .hud-btn, .btn-back, [onclick]');
        const isLink = e.target.closest('a, .module-card');
        
        // Si no es un enlace de módulo, reproducimos el clic simple inmediatamente
        if (target && !isLink) {
            playClickAndNavigate(null);
        }
    }, true);

    // 3. INTERCEPTOR DE ENLACES Y MÓDULOS (Garantiza reproducir clicks.mp3 antes de irse)
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        if (link && link.href && !link.href.startsWith('#') && link.target !== '_blank') {
            e.preventDefault();
            e.stopPropagation();
            playClickAndNavigate(link.href);
        }
    }, true);
}

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
                e.stopPropagation();
                addLog(`Accediendo al módulo: ${id.replace('btn-', '').toUpperCase()}...`, "system");
                playClickAndNavigate(url);
            });
        }
    });
}

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

let testClick = new Audio(window.location.origin + '/src/Sounds/welcome/clicks.mp3');
testClick.volume = 1.0;
testClick.play()
    .then(() => console.log("✅ EL MP3 SÍ EXISTE Y SÍ SUENA"))
    .catch(err => console.error("❌ ERROR AL REPRODUCIR:", err));