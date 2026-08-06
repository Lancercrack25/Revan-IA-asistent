// Manejo de Cambio de Pestañas / Ventanas Tácticas
function switchCreativeTab(tabName) {
    // Ocultar todos los paneles
    const panels = document.querySelectorAll('.creative-tab-panel');
    panels.forEach(p => p.classList.remove('active'));

    // Quitar activo de botones
    const buttons = document.querySelectorAll('.hud-switcher .nav-btn:not(.back-btn)');
    buttons.forEach(b => b.classList.remove('active'));

    // Activar pestaña requerida
    if (tabName === 'studio') {
        document.getElementById('view-studio').classList.add('active');
        document.getElementById('tab-studio').classList.add('active');
    } else if (tabName === 'manual') {
        document.getElementById('view-manual').classList.add('active');
        document.getElementById('tab-manual').classList.add('active');
    } else if (tabName === 'ultron') {
        document.getElementById('view-ultron').classList.add('active');
        document.getElementById('tab-ultron').classList.add('active');
    }
}

// Limpiar el canvas
function clearCanvas() {
    const canvas = document.getElementById('canvas-display');
    canvas.innerHTML = `
        <div class="placeholder-art">
            <i class="fa-solid fa-photo-film placeholder-icon"></i>
            <p>> Esperando parámetros para iniciar síntesis visual...</p>
        </div>
    `;
}

// Simulación de Generación Creativa
function runCreativeCommand() {
    const input = document.getElementById('creative-cmd');
    const canvas = document.getElementById('canvas-display');
    const promptText = input.value.trim();

    if (!promptText) return;

    // Colocar estado de Renderizando
    canvas.innerHTML = `
        <div class="placeholder-art">
            <i class="fa-solid fa-compact-disc fa-spin placeholder-icon" style="color: #e040ff;"></i>
            <p>> Sintetizando recurso visual: "${promptText}"...</p>
            <span style="font-size: 0.75rem; color: #00ffcc;">[APLICANDO ESTILO Y RAY-TRACING]</span>
        </div>
    `;

    // Simulación de finalización del render
    setTimeout(() => {
        canvas.innerHTML = `
            <div style="text-align: center; border: 1px solid #e040ff; padding: 20px; background: rgba(224, 64, 255, 0.05);">
                <i class="fa-solid fa-wand-magic-sparkles" style="font-size: 2.5rem; color: #e040ff; margin-bottom: 10px;"></i>
                <h3 style="color: #00ffcc;">SÍNTESIS COMPLETADA</h3>
                <p style="color: #fff; margin-top: 5px;">"${promptText}"</p>
                <small style="color: #8a609d; display:block; margin-top:10px;">Render listo para exportación o buffer local.</small>
            </div>
        `;
    }, 1500);

    input.value = '';
}

// Configurar botones de aspecto (Ratio)
document.querySelectorAll('.ratio-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
        document.querySelectorAll('.ratio-btn').forEach(b => b.classList.remove('active'));
        e.target.classList.add('active');
    });
});

// Inicializar Partículas Sci-Fi en el fondo (Tono Magenta)
if (typeof particlesJS !== 'undefined') {
    particlesJS('particles-js', {
        "particles": {
            "number": { "value": 40 },
            "color": { "value": "#e040ff" },
            "line_linked": { "enable": true, "distance": 150, "color": "#e040ff", "opacity": 0.2, "width": 1 },
            "move": { "enable": true, "speed": 1.5 }
        }
    });
}