let timerInterval = null;

function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(ms).padStart(2, '0')}`;
}

function startTimer() {
    const startBtn = document.getElementById('startBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const lapBtn = document.getElementById('lapBtn');
    const statusDisplay = document.getElementById('statusDisplay');
    
    startBtn.disabled = true;
    pauseBtn.disabled = false;
    lapBtn.disabled = false;
    statusDisplay.textContent = 'Läuft...';

    const startTime = Date.now() - (parseInt(localStorage.getItem('elapsedTime')) || 0);

    if (timerInterval) clearInterval(timerInterval);

    timerInterval = setInterval(() => {
        const elapsed = (Date.now() - startTime) / 1000;
        localStorage.setItem('elapsedTime', elapsed * 1000);
        document.getElementById('timeDisplay').textContent = formatTime(elapsed);
    }, 10);
}

function pauseTimer() {
    if (timerInterval) clearInterval(timerInterval);
    
    const startBtn = document.getElementById('startBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const statusDisplay = document.getElementById('statusDisplay');
    
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    statusDisplay.textContent = 'Pausiert';
    startBtn.textContent = 'Fortsetzen';
}

function resetTimer() {
    if (timerInterval) clearInterval(timerInterval);
    
    localStorage.removeItem('elapsedTime');
    localStorage.removeItem('laps');
    
    const startBtn = document.getElementById('startBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const lapBtn = document.getElementById('lapBtn');
    const statusDisplay = document.getElementById('statusDisplay');
    
    document.getElementById('timeDisplay').textContent = '00:00:00.00';
    statusDisplay.textContent = 'Bereit';
    startBtn.textContent = 'Start';
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    lapBtn.disabled = true;
    
    document.getElementById('lapsList').innerHTML = '<div class="empty-laps">Keine Runden erfasst</div>';
}

function recordLap() {
    const timeDisplay = document.getElementById('timeDisplay').textContent;
    const laps = JSON.parse(localStorage.getItem('laps')) || [];
    
    laps.push({
        number: laps.length + 1,
        time: timeDisplay
    });
    
    localStorage.setItem('laps', JSON.stringify(laps));
    updateLapsList();
}

function updateLapsList() {
    const laps = JSON.parse(localStorage.getItem('laps')) || [];
    const lapsList = document.getElementById('lapsList');
    
    if (laps.length === 0) {
        lapsList.innerHTML = '<div class="empty-laps">Keine Runden erfasst</div>';
        return;
    }
    
    lapsList.innerHTML = laps.map(lap => 
        `<div class="lap-item">
            <span class="lap-number">Runde ${lap.number}</span>
            <span class="lap-time">${lap.time}</span>
        </div>`
    ).join('');
}

// Spacebar zum Start/Pause
window.addEventListener('keydown', (event) => {
    if (event.code === 'Space') {
        event.preventDefault();
        const startBtn = document.getElementById('startBtn');
        const pauseBtn = document.getElementById('pauseBtn');

        if (!startBtn.disabled) {
            startTimer();
        } else if (!pauseBtn.disabled) {
            pauseTimer();
        }
    }
});

// Laden von gespeicherten Daten beim Seitenaufruf
window.addEventListener('load', () => {
    const elapsedTime = parseInt(localStorage.getItem('elapsedTime')) || 0;
    if (elapsedTime > 0) {
        document.getElementById('timeDisplay').textContent = formatTime(elapsedTime / 1000);
    }
    updateLapsList();
});
