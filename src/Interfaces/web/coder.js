const BASE_URL = window.location.origin;

const SOUND_PATHS = {
    hover: `${BASE_URL}/src/Sounds/welcome/hovers.mp3`,
    click: `${BASE_URL}/src/Sounds/welcome/clicks.mp3`,
    section: `${BASE_URL}/src/Sounds/welcome/sections.mp3`
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

    clickAudioCache.volume = 0.01;
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
        else snd = new Audio(SOUND_PATHS[type]);

        snd.volume = volume;
        snd.currentTime = 0;

        const ctx = getAudioContext();
        if (ctx) {
            const source = ctx.createMediaElementSource(snd);
            const filter = ctx.createBiquadFilter();
            
            filter.type = "peaking";
            filter.frequency.value = 2800;
            filter.gain.value = 4;
            
            source.connect(filter);
            filter.connect(ctx.destination);
        }

        snd.play().catch(() => {});
    } catch (e) {
        try {
            let snd = new Audio(SOUND_PATHS[type]);
            snd.volume = volume;
            snd.play().catch(() => {});
        } catch(err) {}
    }
}

function playClickAndNavigate(callbackUrl = null) {
    unlockAudioEngine();
    
    // Fuerza la reproducción explícita del sonido 'click'
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
function playSectionSFX() { playDirectSound('section', 0.7); }

function openCoderSubView(viewName) {
    // Al hacer clic en un módulo o tarjeta se escucha un 'click' seco y limpio
    playDirectSound('click', 1.0);
    document.querySelectorAll('.coder-view').forEach(v => v.classList.remove('active'));
    
    const target = document.getElementById(`view-${viewName}`);
    if (target) {
        target.classList.add('active');
    }
}

function toggleCoderView() {
    playDirectSound('click', 1.0);
    const cardsView = document.getElementById('coder-cards-view');
    if (cardsView && cardsView.classList.contains('active')) {
        openCoderSubView('ide');
    } else {
        document.querySelectorAll('.coder-view').forEach(v => v.classList.remove('active'));
        if (cardsView) cardsView.classList.add('active');
    }
}

function clearTerminal() {
    playDirectSound('click', 1.0);
    const terminal = document.getElementById('terminal-output');
    if (terminal) terminal.innerHTML = '';
}

function runCoderCommand() {
    const input = document.getElementById('coder-cmd');
    const terminal = document.getElementById('terminal-output');
    if (!input || !terminal) return;

    const cmdText = input.value.trim();
    if (!cmdText) return;

    playDirectSound('click', 1.0);

    if (document.getElementById('coder-cards-view').classList.contains('active')) {
        openCoderSubView('ide');
    }

    const cmdLine = document.createElement('div');
    cmdLine.style.color = '#00ffcc';
    cmdLine.innerHTML = `> [EXEC_CMD]: ${cmdText}`;
    terminal.appendChild(cmdLine);

    setTimeout(() => {
        playHoverSFX();
        const respLine = document.createElement('div');
        respLine.style.color = '#00ff88';
        respLine.innerHTML = `> [CODER_RESP]: Comando compilado y procesado exitosamente.`;
        terminal.appendChild(respLine);
        terminal.scrollTop = terminal.scrollHeight;
    }, 350);

    input.value = '';
}

document.addEventListener('DOMContentLoaded', () => {
    // Unico momento donde se usa section.mp3: al cargar la interfaz
    setTimeout(() => {
        playSectionSFX();
    }, 150);

    let currentHoveredElement = null;
    document.addEventListener('mouseover', (e) => {
        const target = e.target.closest('button, a, .epic-card, input, [onclick]');
        if (target && target !== currentHoveredElement) {
            currentHoveredElement = target;
            playHoverSFX();
        } else if (!target) {
            currentHoveredElement = null;
        }
    });

    const coderInput = document.getElementById('coder-cmd');
    if (coderInput) {
        coderInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') runCoderCommand();
        });
    }

    setInterval(() => {
        const cpu = Math.floor(Math.random() * 25) + 20;
        const ram = Math.floor(Math.random() * 15) + 55;
        const cpuFill = document.getElementById('cpu-fill');
        const ramFill = document.getElementById('ram-fill');
        if (cpuFill) cpuFill.style.width = `${cpu}%`;
        if (ramFill) ramFill.style.width = `${ram}%`;
    }, 2500);

    if (typeof particlesJS !== 'undefined') {
        particlesJS('particles-js', {
            "particles": {
                "number": { "value": 35 },
                "color": { "value": "#00ffcc" },
                "shape": { "type": "circle" },
                "opacity": { "value": 0.5 },
                "size": { "value": 3, "random": true },
                "line_linked": { 
                    "enable": true, 
                    "distance": 140, 
                    "color": "#00ffcc", 
                    "opacity": 0.2, 
                    "width": 1 
                },
                "move": { "enable": true, "speed": 1 }
            },
            "retina_detect": true
        });
    }
});