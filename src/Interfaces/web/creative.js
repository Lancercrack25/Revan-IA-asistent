const BASE_URL = window.location.origin;

// Cambia esto al nombre EXACTO de tu archivo físico (revisa minúsculas y dobles 's'):
const SOUND_PATHS = {
    hover: `${BASE_URL}/src/Sounds/welcome/hovers.mp3`,
    click: `${BASE_URL}/src/Sounds/welcome/clicks.mp3`,
    section: `${BASE_URL}/src/Sounds/modules/Creative_asisstent.mp3` // <-- Revisa si lleva 'ss' o minúsculas
};

let userInteracted = false;
let audioCtx = null;

// Cache precargado
const clickAudioCache = new Audio(SOUND_PATHS.click);
clickAudioCache.preload = 'auto';

const hoverAudioCache = new Audio(SOUND_PATHS.hover);
hoverAudioCache.preload = 'auto';

const sectionAudioCache = new Audio(SOUND_PATHS.section);
sectionAudioCache.preload = 'auto';

function getAudioContext() {
    if (!audioCtx) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (AudioContextClass) {
            audioCtx = new AudioContextClass();
        }
    }
    if (audioCtx && audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
    return audioCtx;
}

function unlockAudioEngine() {
    if (userInteracted) return;
    userInteracted = true;
    
    getAudioContext();

    clickAudioCache.volume = 0.9;
    clickAudioCache.play().then(() => {
        clickAudioCache.pause();
        clickAudioCache.currentTime = 0;
    }).catch(() => {});
    
    window.removeEventListener('pointerdown', unlockAudioEngine);
    window.removeEventListener('keydown', unlockAudioEngine);
}

window.addEventListener('pointerdown', unlockAudioEngine);
window.addEventListener('keydown', unlockAudioEngine);

function playDirectSound(type, volume = 0.8) {
    if (!SOUND_PATHS[type]) return;
    try {
        let snd;
        if (type === 'click') snd = clickAudioCache.cloneNode();
        else if (type === 'hover') snd = hoverAudioCache.cloneNode();
        else if (type === 'section') snd = sectionAudioCache.cloneNode();
        else snd = new Audio(encodeURI(SOUND_PATHS[type]));

        snd.volume = volume;
        snd.currentTime = 0;

        const ctx = getAudioContext();
        if (ctx) {
            try {
                const source = ctx.createMediaElementSource(snd);
                const filter = ctx.createBiquadFilter();
                
                filter.type = "peaking";
                filter.frequency.value = 2800;
                filter.gain.value = 4;
                
                source.connect(filter);
                filter.connect(ctx.destination);
            } catch (errNode) {
                // Si el nodo WebAudio ya fue conectado, reproduce por HTML5 directo
            }
        }

        snd.play().catch(() => {});
    } catch (e) {
        try {
            let snd = new Audio(encodeURI(SOUND_PATHS[type]));
            snd.volume = volume;
            snd.play().catch(() => {});
        } catch(err) {}
    }
}

// 🔊 Función para navegar a Creative Agent reproduciendo el sonido de sección/voz antes del cambio de página
function navegarACreative(targetUrl = '/creative') {
    unlockAudioEngine();
    
    // Reproduce el clic y el sonido de voz del módulo Creative
    playDirectSound('click', 1.0);
    playSectionSFX();

    let navigated = false;
    const goToPage = () => {
        if (!navigated) {
            navigated = true;
            window.location.href = targetUrl;
        }
    };

    // Dar tiempo para escuchar el sonido antes de navegar
    setTimeout(goToPage, 300);
    setTimeout(goToPage, 500);
}

function playClickAndNavigate(callbackUrl = null) {
    unlockAudioEngine();
    
    playDirectSound('click', 1.0);

    if (!callbackUrl) return;

    let navigated = false;
    const goToPage = () => {
        if (!navigated) {
            navigated = true;
            window.location.href = callbackUrl;
        }
    };

    setTimeout(goToPage, 260);
    setTimeout(goToPage, 450);
}

function playHoverSFX() { playDirectSound('hover', 0.4); }
function playSectionSFX() { playDirectSound('section', 0.8); }

function openCreativeSubView(viewName) {
    playDirectSound('click', 1.0);
    document.querySelectorAll('.creative-view').forEach(v => v.classList.remove('active'));
    
    const target = document.getElementById(`view-${viewName}`);
    if (target) {
        target.classList.add('active');
    }
}

function toggleCreativeView() {
    playDirectSound('click', 1.0);
    const cardsView = document.getElementById('creative-cards-view');
    if (cardsView && cardsView.classList.contains('active')) {
        openCreativeSubView('canvas');
    } else {
        document.querySelectorAll('.creative-view').forEach(v => v.classList.remove('active'));
        if (cardsView) cardsView.classList.add('active');
    }
}

let creativeSocket = null;

function conectarWebSocketCreative() {
    creativeSocket = new WebSocket(`ws://${window.location.host}/ws`);

    creativeSocket.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.tipo === 'creative_response') {
                mostrarRespuestaCreative(data.texto);
            }
        } catch (e) { /* mensaje no relacionado con este canal, se ignora */ }
    };

    creativeSocket.onclose = () => {
        setTimeout(conectarWebSocketCreative, 2000);
    };
}

function _obtenerWorkspaceCanvas() {
    const workspace = document.querySelector('#view-canvas .canvas-workspace');
    if (workspace && document.getElementById('creative-cards-view') && document.getElementById('creative-cards-view').classList.contains('active')) {
        openCreativeSubView('canvas');
    }
    return workspace;
}

function mostrarRespuestaCreative(texto) {
    const workspace = document.querySelector('#view-canvas .canvas-workspace');
    if (!workspace) return;

    const lineaEspera = document.getElementById('creative-espera-linea');
    if (lineaEspera) lineaEspera.remove();

    // Reproduce el audio del módulo al recibir la respuesta
    playSectionSFX();

    const p = document.createElement('p');
    p.style.color = '#ff66aa';
    p.style.whiteSpace = 'pre-wrap';
    p.textContent = `> ${texto}`;
    workspace.appendChild(p);
}

function runCreativeCommand() {
    const input = document.getElementById('creative-cmd');
    if (!input) return;

    const cmdText = input.value.trim();
    if (!cmdText) return;

    // 🔊 Sonido directo e instantáneo al presionar SINTETIZAR o Enter
    try {
        const sndClick = new Audio(SOUND_PATHS.click);
        sndClick.volume = 1.0;
        sndClick.play().catch(() => {});
    } catch(e) {}

    const workspace = _obtenerWorkspaceCanvas();

    if (workspace) {
        const p = document.createElement('p');
        p.style.color = '#ffffff';
        p.textContent = `> Prompt: "${cmdText}"`;
        workspace.appendChild(p);
    }

    if (creativeSocket && creativeSocket.readyState === WebSocket.OPEN) {
        if (workspace) {
            const espera = document.createElement('p');
            espera.id = 'creative-espera-linea';
            espera.style.color = '#888';
            espera.textContent = '> Generando imagen, esto puede tardar unos segundos...';
            workspace.appendChild(espera);
        }
        creativeSocket.send(JSON.stringify({ type: 'creative_command', content: cmdText }));
    } else if (workspace) {
        const err = document.createElement('p');
        err.style.color = '#ff4444';
        err.textContent = '> [ERROR]: Sin conexión con REVAN. Verifique que main.py esté corriendo.';
        workspace.appendChild(err);
    }

    input.value = '';
}

document.addEventListener('DOMContentLoaded', () => {
    conectarWebSocketCreative();

    // 🔊 Reproducir el sonido de entrada de Creative Agent
    const reproducirSonidoEntrada = () => {
        playSectionSFX();
        window.removeEventListener('pointerdown', reproducirSonidoEntrada);
        window.removeEventListener('keydown', reproducirSonidoEntrada);
    };

    try {
        playSectionSFX();
    } catch(e) {}

    window.addEventListener('pointerdown', reproducirSonidoEntrada, { once: true });
    window.addEventListener('keydown', reproducirSonidoEntrada, { once: true });

    let currentHoveredElement = null;
    document.addEventListener('mouseover', (e) => {
        const target = e.target.closest('button, a, .revan-card, .epic-card, input, [onclick]');
        if (target && target !== currentHoveredElement) {
            currentHoveredElement = target;
            playHoverSFX();
        } else if (!target) {
            currentHoveredElement = null;
        }
    });

    const creativeInput = document.getElementById('creative-cmd');
    if (creativeInput) {
        creativeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') runCreativeCommand();
        });
    }

    if (typeof particlesJS !== 'undefined') {
        particlesJS('particles-js', {
            "particles": {
                "number": { "value": 40 },
                "color": { "value": "#ff0055" },
                "shape": { "type": "circle" },
                "opacity": { "value": 0.5 },
                "size": { "value": 3, "random": true },
                "line_linked": { 
                    "enable": true, 
                    "distance": 140, 
                    "color": "#ff0055", 
                    "opacity": 0.25, 
                    "width": 1 
                },
                "move": { "enable": true, "speed": 1 }
            },
            "retina_detect": true
        });
    }
});