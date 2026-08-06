// Manejo de Cambio de Pestañas / Ventanas Tácticas
function switchCoderTab(tabName) {
    // Ocultar todos los paneles
    const panels = document.querySelectorAll('.coder-tab-panel');
    panels.forEach(p => p.classList.remove('active'));

    // Quitar activo de botones
    const buttons = document.querySelectorAll('.hud-switcher .nav-btn:not(.back-btn)');
    buttons.forEach(b => b.classList.remove('active'));

    // Activar pestaña requerida
    if (tabName === 'ide') {
        document.getElementById('view-ide').classList.add('active');
        document.getElementById('tab-ide').classList.add('active');
    } else if (tabName === 'manual') {
        document.getElementById('view-manual').classList.add('active');
        document.getElementById('tab-manual').classList.add('active');
    } else if (tabName === 'ultron') {
        document.getElementById('view-ultron').classList.add('active');
        document.getElementById('tab-ultron').classList.add('active');
    }
}

// Limpiar salida de la terminal
function clearTerminal() {
    document.getElementById('terminal-output').innerHTML = '';
}

// Ejecución/Compilación simulada en consola
function runCoderCommand() {
    const input = document.getElementById('coder-cmd');
    const terminal = document.getElementById('terminal-output');
    const cmdText = input.value.trim();

    if (!cmdText) return;

    // Agregar comando a la terminal
    const cmdLine = document.createElement('div');
    cmdLine.className = 'term-line system';
    cmdLine.innerHTML = `> [EXEC_CMD]: ${cmdText}`;
    terminal.appendChild(cmdLine);

    // Simulación de respuesta del compilador
    setTimeout(() => {
        const respLine = document.createElement('div');
        respLine.className = 'term-line success';
        respLine.innerHTML = `> [CODER_RESP]: Procesando script... Código verificado sin errores sintácticos.`;
        terminal.appendChild(respLine);
        terminal.scrollTop = terminal.scrollHeight;
    }, 600);

    input.value = '';
}

// Inicializar Partículas Sci-Fi en el fondo
if (typeof particlesJS !== 'undefined') {
    particlesJS('particles-js', {
        "particles": {
            "number": { "value": 40 },
            "color": { "value": "#00ffcc" },
            "line_linked": { "enable": true, "distance": 150, "color": "#00ffcc", "opacity": 0.2, "width": 1 },
            "move": { "enable": true, "speed": 1.5 }
        }
    });
}