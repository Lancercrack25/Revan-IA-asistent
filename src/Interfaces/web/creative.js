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
function playCloseSFX() { playDirectSound('close', 0.5); }

// NAVEGACIÓN DE VISTAS EN CREATIVE
function openCreativeSubView(viewName) {
    playSectionSFX();
    document.querySelectorAll('.creative-view').forEach(v => v.classList.remove('active'));
    
    const target = document.getElementById(`view-${viewName}`);
    if (target) {
        target.classList.add('active');
    }
}

function toggleCreativeView() {
    playDirectSound('click', 0.5);
    const cardsView = document.getElementById('creative-cards-view');
    if (cardsView && cardsView.classList.contains('active')) {
        openCreativeSubView('canvas');
    } else {
        document.querySelectorAll('.creative-view').forEach(v => v.classList.remove('active'));
        if (cardsView) cardsView.classList.add('active');
    }
}

function runCreativeCommand() {
    const input = document.getElementById('creative-cmd');
    if (!input) return;

    const cmdText = input.value.trim();
    if (!cmdText) return;

    playDirectSound('click', 0.5);

    if (document.getElementById('creative-cards-view').classList.contains('active')) {
        openCreativeSubView('canvas');
    }

    input.value = '';
}

document.addEventListener('DOMContentLoaded', () => {
    // Sonido al cargar sección
    setTimeout(() => {
        playSectionSFX();
    }, 150);

    // Hover automático en elementos
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
                "number": { "value": 30 },
                "color": { "value": "#ff0055" },
                "line_linked": { "enable": true, "distance": 140, "color": "#ff0055", "opacity": 0.25, "width": 1 },
                "move": { "enable": true, "speed": 1 }
            }
        });
    }
});