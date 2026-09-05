let statusInterval = null;
let currentStatus = { is_running: false, is_paused: false };
let selectedRunGroupId = '';
let participantInterval = null;
let activeRunGroups = [];

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
    } else if (activeRunGroups.length && !selectedRunGroupId) {
        startBtn.textContent = 'Gruppe auswählen';
        startBtn.disabled = true;
        pauseBtn.disabled = true;
        lapBtn.disabled = false;
        numberInput.disabled = false;
        statusDisplay.textContent = 'Automatische Nummernsuche';
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
        const query = selectedRunGroupId ? `?run_group_id=${encodeURIComponent(selectedRunGroupId)}` : '';
        const response = await fetch(`/api/stopwatch/status${query}`);
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
            throw new Error('Kann aktive Laufgruppen nicht laden');
        }
        const runs = await response.json();
        activeRunGroups = runs;
        renderActiveRuns(runs);
        if (!selectedRunGroupId) setControls(currentStatus);
    } catch (error) {
        document.getElementById('activeRuns').innerHTML = `<div class="empty-laps">Fehler beim Laden der Läufe.</div>`;
        console.warn(error);
    }
}

async function fetchRunGroups() {
    try {
        const response = await fetch('/api/stopwatch/run_groups');
        const groups = await response.json();
        const select = document.getElementById('runGroupSelect');
        select.innerHTML = '<option value="">Automatische Nummernsuche</option>';
        groups.forEach((group) => {
            const option = document.createElement('option');
            option.value = group.id;
            option.textContent = `${group.name} (${group.classes || 'keine Klassen'})`;
            select.appendChild(option);
        });
    } catch (error) {
        document.getElementById('runGroupClasses').textContent = 'Laufgruppen konnten nicht geladen werden.';
    }
}

async function fetchParticipants() {
    if (!selectedRunGroupId) return;
    try {
        const response = await fetch(`/api/stopwatch/run_groups/${selectedRunGroupId}/participants`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.error);
        const list = document.getElementById('participantsList');
        const remaining = data.participants.filter((item) => item.still_running);
        document.getElementById('remainingCount').textContent = data.remaining;
        list.innerHTML = data.participants.length
            ? data.participants.map((item) => `<div class="lap-item d-flex justify-content-between mb-2 p-2 rounded bg-light"><span>${item.class_group} · Nr. ${item.nummer}</span>${item.still_running ? '<span class="badge bg-warning text-dark">Läuft</span>' : `<span class="text-success">${item.zeit}</span>`}</div>`).join('')
            : '<div class="empty-laps text-success">Alle gesunden Teilnehmer sind angekommen.</div>';
    } catch (error) {
        document.getElementById('participantsList').innerHTML = '<div class="empty-laps">Teilnehmer konnten nicht geladen werden.</div>';
    }
}

function updateRunGroupSelection() {
    const select = document.getElementById('runGroupSelect');
    selectedRunGroupId = select.value;
    const option = select.options[select.selectedIndex];
    document.getElementById('runGroupClasses').textContent = option && option.value ? option.textContent : 'Startnummer wird in den aktiven Laufgruppen gesucht';
    fetchStatus();
    fetchParticipants();
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
                <div class="fw-semibold">Klasse ${m.class_group} · Nr. ${m.nummer}</div>
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
                <div class="fw-semibold">${run.name}</div>
                <div class="text-muted">Klassen: ${run.classes || 'keine'}</div>
                <div class="text-muted">Gestartet: ${new Date(run.started_at).toLocaleString('de-DE')}</div>
            </div>
            <div class="badge bg-success">Aktiv</div>
        </div>`
    ).join('');
}

async function apiAction(action) {
    try {
        if (!selectedRunGroupId) {
            throw new Error('Bitte zuerst eine Laufgruppe auswählen.');
        }
        const body = JSON.stringify({ run_group_id: selectedRunGroupId });
        const response = await fetch(`/api/stopwatch/${action}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body
        });
        if (!response.ok) {
            const data = await response.json().catch(() => ({}));
            throw new Error(data.error || 'Server antwortete mit einem Fehler');
        }
        await fetchStatus();
        fetchParticipants();
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
            body: JSON.stringify(selectedRunGroupId ? { number, run_group_id: selectedRunGroupId } : { number })
        });
        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Unbekannter Fehler beim Speichern');
        }

        const measurements = JSON.parse(localStorage.getItem('measurements')) || [];
        measurements.unshift({
            number: data.number,
            class_group: data.class_group,
            time: data.time
        });
        localStorage.setItem('measurements', JSON.stringify(measurements));
        updateLapsList();
        numberInput.value = '';
        numberInput.focus();
        fetchHistory();
        fetchParticipants();
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
                <div class="fw-semibold">Klasse ${m.class_group || 'unbekannt'} · Nr. ${m.number}</div>
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
    fetchRunGroups();
    document.getElementById('runGroupSelect').addEventListener('change', updateRunGroupSelection);
    participantInterval = setInterval(fetchParticipants, 2000);
});