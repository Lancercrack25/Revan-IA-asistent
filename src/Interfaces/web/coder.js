// SINTETIZADOR DE AUDIO SCI-FI (Web Audio API)
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function playAudio(type) {
    if (audioCtx.state === 'suspended') audioCtx.resume();

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    const now = audioCtx.currentTime;

    if (type === 'hover') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(800, now);
        osc.frequency.exponentialRampToValueAtTime(1200, now + 0.05);
        gain.gain.setValueAtTime(0.03, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        osc.start(now); osc.stop(now + 0.05);
    } else if (type === 'click') {
        osc.type = 'square';
        osc.frequency.setValueAtTime(400, now);
        osc.frequency.exponentialRampToValueAtTime(100, now + 0.12);
        gain.gain.setValueAtTime(0.08, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);
        osc.start(now); osc.stop(now + 0.12);
    } else if (type === 'back') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(300, now);
        osc.frequency.linearRampToValueAtTime(150, now + 0.15);
        gain.gain.setValueAtTime(0.06, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
        osc.start(now); osc.stop(now + 0.15);
    }
}

// NAVEGACIÓN Y CAMBIO DE VISTAS
function openCoderSubView(viewName) {
    playAudio('click');
    document.querySelectorAll('.coder-view').forEach(v => v.classList.remove('active'));
    
    const target = document.getElementById(`view-${viewName}`);
    if (target) target.classList.add('active');
}

function toggleCoderView() {
    playAudio('click');
    const cardsView = document.getElementById('coder-cards-view');
    if (cardsView.classList.contains('active')) {
        openCoderSubView('ide');
    } else {
        document.querySelectorAll('.coder-view').forEach(v => v.classList.remove('active'));
        cardsView.classList.add('active');
    }
}

function clearTerminal() {
    playAudio('click');
    const terminal = document.getElementById('terminal-output');
    if (terminal) terminal.innerHTML = '';
}

function runCoderCommand() {
    playAudio('click');
    const input = document.getElementById('coder-cmd');
    const terminal = document.getElementById('terminal-output');
    if (!input || !terminal) return;

    const cmdText = input.value.trim();
    if (!cmdText) return;

    if (document.getElementById('coder-cards-view').classList.contains('active')) {
        openCoderSubView('ide');
    }

    const cmdLine = document.createElement('div');
    cmdLine.style.color = '#00ffcc';
    cmdLine.innerHTML = `> [EXEC_CMD]: ${cmdText}`;
    terminal.appendChild(cmdLine);

    setTimeout(() => {
        playAudio('hover');
        const respLine = document.createElement('div');
        respLine.style.color = '#00ff88';
        respLine.innerHTML = `> [CODER_RESP]: Comando compilado y procesado exitosamente.`;
        terminal.appendChild(respLine);
        terminal.scrollTop = terminal.scrollHeight;
    }, 400);

    input.value = '';
}

// INICIALIZACIÓN & EFECTOS
document.addEventListener('DOMContentLoaded', () => {
    // Sonidos Hover en Tarjetas
    document.querySelectorAll('.epic-card, .nav-btn, button').forEach(elem => {
        elem.addEventListener('mouseenter', () => playAudio('hover'));
    });

    // Enter Key
    const coderInput = document.getElementById('coder-cmd');
    if (coderInput) {
        coderInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') runCoderCommand();
        });
    }

    // Animación de Telemetría Dinámica CPU/RAM
    setInterval(() => {
        const cpu = Math.floor(Math.random() * 30) + 20;
        const ram = Math.floor(Math.random() * 20) + 50;
        const cpuFill = document.getElementById('cpu-fill');
        const ramFill = document.getElementById('ram-fill');
        if (cpuFill) cpuFill.style.width = `${cpu}%`;
        if (ramFill) ramFill.style.width = `${ram}%`;
    }, 2500);

    // Particles.js
    if (typeof particlesJS !== 'undefined') {
        particlesJS('particles-js', {
            "particles": {
                "number": { "value": 40 },
                "color": { "value": "#00ffcc" },
                "line_linked": { "enable": true, "distance": 150, "color": "#00ffcc", "opacity": 0.25, "width": 1 },
                "move": { "enable": true, "speed": 1.2 }
            }
        });
    }
});