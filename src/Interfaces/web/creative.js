function openCreativeSubView(viewName) {
    document.querySelectorAll('.creative-view').forEach(v => v.classList.remove('active'));
    
    const target = document.getElementById(`view-${viewName}`);
    if (target) target.classList.add('active');
}

function showCreativeMenu() {
    document.querySelectorAll('.creative-view').forEach(v => v.classList.remove('active'));
    document.getElementById('creative-cards-view').classList.add('active');
}

function runCreativeCommand() {
    const input = document.getElementById('creative-cmd');
    if (!input) return;

    const cmdText = input.value.trim();
    if (!cmdText) return;

    if (document.getElementById('creative-cards-view').classList.contains('active')) {
        openCreativeSubView('canvas');
    }

    alert(`Procesando prompt en Creative Agent: "${cmdText}"`);
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