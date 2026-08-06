function switchCoderTab(tabName) {
    document.querySelectorAll('.coder-tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.hud-switcher .nav-btn:not(.back-btn)').forEach(b => b.classList.remove('active'));

    const targetPanel = document.getElementById(`view-${tabName}`);
    const targetBtn = document.getElementById(`tab-${tabName}`);

    if (targetPanel) targetPanel.classList.add('active');
    if (targetBtn) targetBtn.classList.add('active');
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

    const cmdLine = document.createElement('div');
    cmdLine.style.color = '#00ffcc';
    cmdLine.innerHTML = `> [EXEC_CMD]: ${cmdText}`;
    terminal.appendChild(cmdLine);

    setTimeout(() => {
        const respLine = document.createElement('div');
        respLine.style.color = '#00ff88';
        respLine.innerHTML = `> [CODER_RESP]: Script procesado correctamente sin errores sintácticos.`;
        terminal.appendChild(respLine);
        terminal.scrollTop = terminal.scrollHeight;
    }, 500);

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