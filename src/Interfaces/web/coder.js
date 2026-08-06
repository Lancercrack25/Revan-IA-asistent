// Abrir vista desde las tarjetas
function openCoderSubView(viewName) {
    document.querySelectorAll('.coder-view').forEach(v => v.classList.remove('active'));
    
    const target = document.getElementById(`view-${viewName}`);
    if (target) target.classList.add('active');
}

// Volver a la pantalla de las 3 tarjetas
function showSubMenu() {
    document.querySelectorAll('.coder-view').forEach(v => v.classList.remove('active'));
    document.getElementById('coder-cards-view').classList.add('active');
}

function clearTerminal() {
    const terminal = document.getElementById('terminal-output');
    if (terminal) terminal.innerHTML = '';
}

function runCoderCommand() {
    const input = document.getElementById('coder-cmd');
    const terminal = document.getElementById('terminal-output');
    if (!input || !terminal) return;

    const cmdText = input.value.trim();
    if (!cmdText) return;

    // Si está en la grilla de tarjetas y escribe un comando, abrir el IDE
    if (document.getElementById('coder-cards-view').classList.contains('active')) {
        openCoderSubView('ide');
    }

    const cmdLine = document.createElement('div');
    cmdLine.style.color = '#00ffcc';
    cmdLine.innerHTML = `> [EXEC_CMD]: ${cmdText}`;
    terminal.appendChild(cmdLine);

    setTimeout(() => {
        const respLine = document.createElement('div');
        respLine.style.color = '#00ff88';
        respLine.innerHTML = `> [CODER_RESP]: Procesando petición... OK.`;
        terminal.appendChild(respLine);
        terminal.scrollTop = terminal.scrollHeight;
    }, 400);

    input.value = '';
}

document.addEventListener('DOMContentLoaded', () => {
    const coderInput = document.getElementById('coder-cmd');
    if (coderInput) {
        coderInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') runCoderCommand();
        });
    }

    if (typeof particlesJS !== 'undefined') {
        particlesJS('particles-js', {
            "particles": {
                "number": { "value": 35 },
                "color": { "value": "#00ffcc" },
                "line_linked": { "enable": true, "distance": 150, "color": "#00ffcc", "opacity": 0.2, "width": 1 },
                "move": { "enable": true, "speed": 1 }
            }
        });
    }
});