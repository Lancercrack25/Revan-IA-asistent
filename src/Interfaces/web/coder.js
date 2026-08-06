const BASE_URL = window.location.origin;

const SOUND_PATHS = {
    hover: `${BASE_URL}/src/Sounds/welcome/hovers.mp3`,
    click: `${BASE_URL}/src/Sounds/welcome/clicks.mp3`,
    section: `${BASE_URL}/src/Sounds/welcome/sections.mp3`,
    close: `${BASE_URL}/src/Sounds/welcome/close.mp3`
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

function playDirectSound(type, volume = 0.5) {
    if (!SOUND_PATHS[type]) return;
    try {
        const snd = new Audio(SOUND_PATHS[type]);
        snd.volume = volume;
        snd.play().catch(() => {});
    } catch (e) {}
}

function playClickAndNavigate(callbackUrl = null) {
    unlockAudioEngine();
    
    try {
        const clickAudio = new Audio(SOUND_PATHS.click);
        clickAudio.volume = 0.8;

        if (callbackUrl) {
            let navigated = false;

            const goToPage = () => {
                if (!navigated) {
                    navigated = true;
                    window.location.href = callbackUrl;
                }
            };

            clickAudio.play().then(() => {
                setTimeout(goToPage, 180);
            }).catch(() => {
                goToPage();
            });

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

// CONTROL DE INTERFAZ CODER
function openCoderSubView(viewName) {
    playSectionSFX();
    document.querySelectorAll('.coder-view').forEach(v => v.classList.remove('active'));
    
    const target = document.getElementById(`view-${viewName}`);
    if (target) {
        target.classList.add('active');
    }
}

function toggleCoderView() {
    playDirectSound('click', 0.5);
    const cardsView = document.getElementById('coder-cards-view');
    if (cardsView && cardsView.classList.contains('active')) {
        openCoderSubView('ide');
    } else {
        document.querySelectorAll('.coder-view').forEach(v => v.classList.remove('active'));
        if (cardsView) cardsView.classList.add('active');
    }
}

function clearTerminal() {
    playDirectSound('click', 0.5);
    const terminal = document.getElementById('terminal-output');
    if (terminal) terminal.innerHTML = '';
}

function runCoderCommand() {
    const input = document.getElementById('coder-cmd');
    const terminal = document.getElementById('terminal-output');
    if (!input || !terminal) return;

    const cmdText = input.value.trim();
    if (!cmdText) return;

    playDirectSound('click', 0.5);

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
    // Repro en carga
    setTimeout(() => {
        playSectionSFX();
    }, 150);

    // Hover genérico
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

    // Telemetría
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
                "line_linked": { "enable": true, "distance": 140, "color": "#00ffcc", "opacity": 0.2, "width": 1 },
                "move": { "enable": true, "speed": 1 }
            }
        });
    }
});