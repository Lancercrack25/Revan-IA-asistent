function switchCreativeTab(tabName) {
    document.querySelectorAll('.creative-tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.hud-switcher .nav-btn:not(.back-btn)').forEach(b => b.classList.remove('active'));

    const targetPanel = document.getElementById(`view-${tabName}`);
    const targetBtn = document.getElementById(`tab-${tabName}`);

    if (targetPanel) targetPanel.classList.add('active');
    if (targetBtn) targetBtn.classList.add('active');
}

function runCreativeCommand() {
    const input = document.getElementById('creative-cmd');
    if (!input) return;

    const cmdText = input.value.trim();
    if (!cmdText) return;

    alert(`Instrucción enviada a Creative Agent: "${cmdText}"`);
    input.value = '';
}

document.addEventListener('DOMContentLoaded', () => {
    const creativeInput = document.getElementById('creative-cmd');
    if (creativeInput) {
        creativeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') runCreativeCommand();
        });
    }
});