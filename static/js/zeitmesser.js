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
    const numberInput = document.getElementById('numberInput');
    const statusDisplay = document.getElementById('statusDisplay');
    
    startBtn.disabled = true;
    pauseBtn.disabled = false;
    lapBtn.disabled = false;
    numberInput.disabled = false;
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
    localStorage.removeItem('measurements');
    
    const startBtn = document.getElementById('startBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const lapBtn = document.getElementById('lapBtn');
    const numberInput = document.getElementById('numberInput');
    const statusDisplay = document.getElementById('statusDisplay');
    
    document.getElementById('timeDisplay').textContent = '00:00:00.00';
    statusDisplay.textContent = 'Bereit';
    startBtn.textContent = 'Start';
    startBtn.disabled = false;
    pauseBtn.disabled = true;
    lapBtn.disabled = true;
    numberInput.disabled = true;
    numberInput.value = '';
    
    document.getElementById('lapsList').innerHTML = '<div class="empty-laps">Keine Messungen erfasst</div>';
}

async function recordMeasurement() {
    const numberInput = document.getElementById('numberInput');
    const number = numberInput.value.trim();
    const timeDisplay = document.getElementById('timeDisplay').textContent;
    
    if (!number) {
        alert('Bitte geben Sie eine Nummer ein!');
        return;
    }
    
    try {
        // Sende die Messung an den Backend
        const response = await fetch('/api/stopwatch/record', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                number: number,
                time: timeDisplay
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Speichere lokal
            const measurements = JSON.parse(localStorage.getItem('measurements')) || [];
            measurements.push({
                number: number,
                time: timeDisplay
            });
            localStorage.setItem('measurements', JSON.stringify(measurements));
            updateLapsList();
            numberInput.value = '';
            numberInput.focus();
        } else {
            alert('Fehler beim Speichern: ' + (data.error || 'Unbekannter Fehler'));
        }
    } catch (error) {
        console.error('Fehler:', error);
        // Fallback: Speichere lokal wenn Backend nicht erreichbar
        const measurements = JSON.parse(localStorage.getItem('measurements')) || [];
        measurements.push({
            number: number,
            time: timeDisplay
        });
        localStorage.setItem('measurements', JSON.stringify(measurements));
        updateLapsList();
        numberInput.value = '';
        numberInput.focus();
    }
}

function updateLapsList() {
    const measurements = JSON.parse(localStorage.getItem('measurements')) || [];
    const lapsList = document.getElementById('lapsList');
    
    if (measurements.length === 0) {
        lapsList.innerHTML = '<div class="empty-laps">Keine Messungen erfasst</div>';
        return;
    }
    
    lapsList.innerHTML = measurements.map((m, index) => 
        `<div class="lap-item">
            <span class="lap-number">Nummer ${m.number}</span>
            <span class="lap-time">${m.time}</span>
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
    
    // Enter-Taste zum Speichern (wenn Input fokussiert ist)
    if (event.code === 'Enter') {
        const numberInput = document.getElementById('numberInput');
        if (document.activeElement === numberInput && !numberInput.disabled) {
            event.preventDefault();
            recordMeasurement();
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
