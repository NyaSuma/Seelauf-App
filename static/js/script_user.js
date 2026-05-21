function goToTimer() {
    // Navigiere zum Zeitmesser
    window.location.href = '/zeitmesser';
}

function closeOverlay() {
    const overlay = document.getElementById('mainOverlay');
    overlay.style.opacity = '0';
    overlay.style.transition = 'opacity 0.3s ease';
    setTimeout(() => {
        overlay.style.display = 'none';
    }, 300);
}
