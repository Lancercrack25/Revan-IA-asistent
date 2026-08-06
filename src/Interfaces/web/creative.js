// ==========================================
// REVAN // CREATIVE AGENT - CORE LOGIC
// ==========================================

// Manejo de Cambio de Pestañas / Ventanas Tácticas
function switchCreativeTab(tabName) {
    // Ocultar todos los paneles
    const panels = document.querySelectorAll('.creative-tab-panel');
    panels.forEach(p => p.classList.remove('active'));

    // Quitar estado activo de los botones de navegación
    const buttons = document.querySelectorAll('.hud-switcher .nav-btn:not(.back-btn)');
    buttons.forEach(b => b.classList.remove('active'));

    // Activar pestaña requerida
    if (tabName === 'studio') {
        document.getElementById('view-studio')?.classList.add('active');
        document.getElementById('tab-studio')?.classList.add('active');
    } else if (tabName === 'manual') {
        document.getElementById('view-manual')?.classList.add('active');
        document.getElementById('tab-manual')?.classList.add('active');
    } else if (tabName === 'ultron') {
        document.getElementById('view-ultron')?.classList.add('active');
        document.getElementById('tab-ultron')?.classList.add('active');
    }
}

// Reiniciar / Limpiar Canvas
function clearCanvas() {
    const canvas = document.getElementById('canvas-display');
    if (canvas) {
        canvas.innerHTML = `
            <div class="placeholder-art">
                <i class="fa-solid fa-photo-film placeholder-icon"></i>
                <p>> Esperando parámetros para iniciar síntesis visual...</p>
            </div>
        `;
    }
}

// Generación / Renderizado simulado de Media
function runCreativeCommand() {
    const input = document.getElementById('creative-cmd');
    const canvas = document.getElementById('canvas-display');
    if (!input || !canvas) return;

    const promptText = input.value.trim();
    if (!promptText) return;

    // Obtener valores seleccionados en los controles
    const mediaType = document.getElementById('media-type')?.value || 'image';
    const styleType = document.getElementById('style-type')?.value || 'cyberpunk';

    // Mostrar estado de carga en el Canvas
    canvas.innerHTML = `
        <div class="placeholder-art render-pulse">
            <i class="fa-solid fa-wand-magic-sparkles placeholder-icon cyan-text"></i>
            <p>> Sintetizando recurso [${mediaType.toUpperCase()}] / Estilo: [${styleType.toUpperCase()}]...</p>
            <span class="sub-text">PROMPT: "${promptText}"</span>
        </div>
    `;

    // Simular resultado final tras 1.2 segundos
    setTimeout(() => {
        canvas.innerHTML = `
            <div class="placeholder-art render-complete">
                <i class="fa-solid fa-circle-check placeholder-icon magenta-text"></i>
                <p>> RENDERIZADO COMPLETADO</p>
                <span class="sub-text">Prompt procesado con éxito por Creative Agent.</span>
            </div>
        `;
    }, 1200);

    input.value = '';
}

// Escuchar eventos al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    // Permitir ejecutar enviando Enter desde el input de prompts
    const creativeInput = document.getElementById('creative-cmd');
    if (creativeInput) {
        creativeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                runCreativeCommand();
            }
        });
    }

    // Configurar comportamiento para los botones de Relación de Aspecto (16:9, 9:16, 1:1)
    const ratioBtns = document.querySelectorAll('.ratio-btn');
    ratioBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            ratioBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
});

// Inicializar Partículas Sci-Fi Magenta en el fondo
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