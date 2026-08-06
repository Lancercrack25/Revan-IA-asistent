const audioCtx = new (window.AudioContext || window.webkitAudioContext)();

function playCreativeAudio(type) {
    if (audioCtx.state === 'suspended') audioCtx.resume();

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(audioCtx.destination);

    const now = audioCtx.currentTime;

    if (type === 'hover') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(1000, now);
        osc.frequency.exponentialRampToValueAtTime(1500, now + 0.05);
        gain.gain.setValueAtTime(0.04, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        osc.start(now); osc.stop(now + 0.05);
    } else if (type === 'click') {
        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(600, now);
        osc.frequency.exponentialRampToValueAtTime(200, now + 0.1);
        gain.gain.setValueAtTime(0.07, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.1);
        osc.start(now); osc.stop(now + 0.1);
    } else if (type === 'back') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(400, now);
        osc.frequency.linearRampToValueAtTime(100, now + 0.15);
        gain.gain.setValueAtTime(0.06, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.15);
        osc.start(now); osc.stop(now + 0.15);
    }
}

function openCreativeSubView(viewName) {
    playCreativeAudio('click');
    document.querySelectorAll('.creative-view').forEach(v => v.classList.remove('active'));
    
    const target = document.getElementById(`view-${viewName}`);
    if (target) target.classList.add('active');
}

function toggleCreativeView() {
    playCreativeAudio('click');
    const cardsView = document.getElementById('creative-cards-view');
    if (cardsView.classList.contains('active')) {
        openCreativeSubView('canvas');
    } else {
        document.querySelectorAll('.creative-view').forEach(v => v.classList.remove('active'));
        cardsView.classList.add('active');
    }
}

function runCreativeCommand() {
    playCreativeAudio('click');
    const input = document.getElementById('creative-cmd');
    if (!input) return;

    const cmdText = input.value.trim();
    if (!cmdText) return;

    if (document.getElementById('creative-cards-view').classList.contains('active')) {
        openCreativeSubView('canvas');
    }

    alert(`Sintetizando prompt en Creative Agent: "${cmdText}"`);
    input.value = '';
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.epic-card, .nav-btn, button').forEach(elem => {
        elem.addEventListener('mouseenter', () => playCreativeAudio('hover'));
    });

    const creativeInput = document.getElementById('creative-cmd');
    if (creativeInput) {
        creativeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') runCreativeCommand();
        });
    }
});