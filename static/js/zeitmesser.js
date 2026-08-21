let statusInterval = null;
let currentStatus = { is_running: false, is_paused: false };

// Für flüssige Anzeige: letzter bekannter Serverstand + Zeitpunkt des Empfangs.
// Zwischen den Server-Syncs wird die Zeit lokal per requestAnimationFrame
// weitergezählt, damit die Anzeige nicht an das 1s-Polling-Intervall gekoppelt ist.
let clientElapsedBase = 0;
let clientBaseTimestamp = 0;
let displayLoopAktiv = false;

function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);

    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}.${String(ms).padStart(2, '0')}`;
}

function updateDisplayLoop() {
    if (!currentStatus.is_running) {
        displayLoopAktiv = false;
        return;
    }
    const jetzt = performance.now();
    const verstrichen = clientElapsedBase + (jetzt - clientBaseTimestamp) / 1000;
    document.getElementById('timeDisplay').textContent = formatTime(verstrichen);
    requestAnimationFrame(updateDisplayLoop);
}

function starteDisplayLoop() {
    if (displayLoopAktiv) return;
    displayLoopAktiv = true;
    requestAnimationFrame(updateDisplayLoop);
}

function setControls(status) {
    const startBtn = document.getElementById('startBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const lapBtn = document.getElementById('lapBtn');
    const numberInput = document.getElementById('numberInput');
    const statusDisplay = document.getElementById('statusDisplay');

    if (status.is_running) {
        startBtn.textContent = 'Läuft';
        startBtn.disabled = true;
        pauseBtn.disabled = false;
        pauseBtn.textContent = 'Pause';
        lapBtn.disabled = false;
        numberInput.disabled = false;
        statusDisplay.textContent = 'Läuft…';
    } else if (status.is_paused) {
        startBtn.textContent = 'Fortsetzen';
        startBtn.disabled = false;
        pauseBtn.disabled = true;
        lapBtn.disabled = false;
        numberInput.disabled = false;
        statusDisplay.textContent = 'Pausiert';
    } else {
        startBtn.textContent = 'Start';
        startBtn.disabled = false;
        pauseBtn.disabled = true;
        lapBtn.disabled = true;
        numberInput.disabled = true;
        statusDisplay.textContent = 'Bereit';
    }
}

async function fetchStatus() {
    try {
        const response = await fetch('/api/stopwatch/status');
        if (!response.ok) {
            throw new Error('Status-Abruf fehlgeschlagen');
        }
        const status = await response.json();
        currentStatus = status;

        // Sync-Basis für die flüssige lokale Interpolation setzen
        clientElapsedBase = status.elapsed_time || 0;
        clientBaseTimestamp = performance.now();

        if (status.is_running) {
            starteDisplayLoop();
        } else {
            // Nicht laufend: exakten Serverwert anzeigen (kein Interpolieren nötig)
            document.getElementById('timeDisplay').textContent = status.formatted_time || '00:00:00.00';
        }

        setControls(status);

        if (status.is_running && !statusInterval) {
            statusInterval = setInterval(fetchStatus, 1000);
        }
        if (!status.is_running && statusInterval) {
            clearInterval(statusInterval);
            statusInterval = null;
        }
    } catch (error) {
        console.warn('Cannot fetch stopwatch status:', error);
        document.getElementById('statusDisplay').textContent = 'Server offline';
    }
}

async function fetchHistory() {
    try {
        const response = await fetch('/api/stopwatch/history');
        if (!response.ok) {
            throw new Error('Kann Ergebnisse nicht laden');
        }
        const measurements = await response.json();
        renderHistory(measurements);
    } catch (error) {
        document.getElementById('historyList').innerHTML = `<div class="empty-laps">Fehler beim Laden der Ergebnisse.</div>`;
        console.warn(error);
    }
}

async function fetchActiveRuns() {
    try {
        const response = await fetch('/api/stopwatch/active_runs');
        if (!response.ok) {
            throw new Error('Kann aktive Läufe nicht laden');
        }
        const runs = await response.json();
        renderActiveRuns(runs);
    } catch (error) {
        document.getElementById('activeRuns').innerHTML = `<div class="empty-laps">Fehler beim Laden der Läufe.</div>`;
        console.warn(error);
    }
}

function renderHistory(measurements) {
    const historyList = document.getElementById('historyList');
    if (!Array.isArray(measurements) || measurements.length === 0) {
        historyList.innerHTML = '<div class="empty-laps">Noch keine Ergebnisse vorhanden.</div>';
        return;
    }

    historyList.innerHTML = measurements.map((m) =>
        `<div class="lap-item d-flex justify-content-between align-items-center mb-2 p-2 rounded bg-light">
            <div>
                <div class="fw-semibold">${m.name || 'Startnummer ' + m.nummer}</div>
                <div class="text-muted">${m.class_group || 'Klasse unbekannt'} · Nr. ${m.nummer}</div>
            </div>
            <div class="text-monospace">${m.zeit}</div>
        </div>`
    ).join('');
}

function renderActiveRuns(runs) {
    const activeRuns = document.getElementById('activeRuns');
    if (!Array.isArray(runs) || runs.length === 0) {
        activeRuns.innerHTML = '<div class="empty-laps">Keine aktiven Läufe gefunden.</div>';
        return;
    }

    activeRuns.innerHTML = runs.map((run) =>
        `<div class="lap-item d-flex justify-content-between align-items-center mb-2 p-2 rounded bg-light">
            <div>
                <div class="fw-semibold">Klasse ${run.class_group}</div>
                <div class="text-muted">Gestartet: ${new Date(run.start_time).toLocaleString('de-DE')}</div>
            </div>
            <div class="badge bg-success">Aktiv</div>
        </div>`
    ).join('');
}

async function apiAction(action) {
    try {
        const response = await fetch(`/api/stopwatch/${action}`, { method: 'POST' });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.error || 'Server antwortete mit einem Fehler');
        }
        await fetchStatus();
    } catch (error) {
        alert('Fehler beim Kommunizieren mit dem Server: ' + error.message);
    }
}

function startTimer() {
    if (currentStatus.is_paused) {
        apiAction('resume');
    } else {
        apiAction('start');
    }
}

function pauseTimer() {
    apiAction('pause');
}

function resetTimer() {
    apiAction('stop');
    document.getElementById('lapsList').innerHTML = '<div class="empty-laps">Keine Messungen erfasst</div>';
}

async function recordMeasurement() {
    const numberInput = document.getElementById('numberInput');
    const number = numberInput.value.trim();

    if (!number) {
        alert('Bitte geben Sie eine Nummer ein!');
        return;
    }

    try {
        const response = await fetch('/api/stopwatch/record', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ number })
        });
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Unbekannter Fehler beim Speichern');
        }

        const measurements = JSON.parse(localStorage.getItem('measurements')) || [];
        measurements.unshift({ number, time: data.time, student_name: data.student_name });
        localStorage.setItem('measurements', JSON.stringify(measurements));
        updateLapsList();
        numberInput.value = '';
        numberInput.focus();
        fetchHistory();
    } catch (error) {
        alert('Fehler beim Speichern: ' + error.message);
    }
}

function updateLapsList() {
    const measurements = JSON.parse(localStorage.getItem('measurements')) || [];
    const lapsList = document.getElementById('lapsList');

    if (measurements.length === 0) {
        lapsList.innerHTML = '<div class="empty-laps">Keine Messungen erfasst</div>';
        return;
    }

    lapsList.innerHTML = measurements.map((m) =>
        `<div class="lap-item d-flex justify-content-between align-items-center mb-2 p-2 rounded bg-light">
            <div>
                <div class="fw-semibold">${m.student_name || 'Startnummer ' + m.number}</div>
                <div class="text-muted">Nummer ${m.number}</div>
            </div>
            <div class="text-monospace">${m.time}</div>
        </div>`
    ).join('');
}

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

    if (event.code === 'Enter') {
        const numberInput = document.getElementById('numberInput');
        if (document.activeElement === numberInput && !numberInput.disabled) {
            event.preventDefault();
            recordMeasurement();
        }
    }
});

window.addEventListener('load', () => {
    updateLapsList();
    fetchStatus();
    fetchHistory();
    fetchActiveRuns();
});