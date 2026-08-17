# Seelauf-App

Eine Flask-basierte Anwendung zur Zeitmessung bei Laufveranstaltungen.

## Features

- Start/Stop/Pausen eines serverseitigen Stoppuhrs
- Runde Zeiten (Lap) erfassen und direkt speichern
- Zeiten nach Startnummer speichern
- Aufzeichnung aller Messungen in SQLite-Datenbank
- Stabiler Adminbereich zur Verwaltung von Schülern, Läufen und Messungen
- RESTful API zur Steuerung und Auswertung der Zeitnahme
- Aktive Läufe und Ergebnisübersicht direkt im Zeitnehmer-Interface
- Moderne, responsive Oberfläche und bessere Fehlerbehandlung

## Installation

### Voraussetzungen

- Python 3.8+
- pip

### Schritte

1. Repository klonen
   ```bash
   git clone <repository-url>
   cd seelauf-app
   ```

2. Virtuelle Umgebung erstellen (optional aber empfohlen)
   ```bash
   python -m venv venv
   source venv/bin/activate  # Auf Windows: venv\Scripts\activate
   ```

3. Abhängigkeiten installieren
   ```bash
   pip install -r requirements.txt
   ```
4. Umgebungskopie erstellen
   ```bash
   copy .env.example .env
   ```
   Passe die Werte in `.env` nach Bedarf an, insbesondere `SECRET_KEY` und `ADMIN_CODE`.
5. Datenbank initialisieren (wird beim ersten Start automatisch erstellt)

6. Anwendung starten
   ```bash
   python app.py
   ```
   Die App läuft dann unter `http://localhost:8000`.

## API Endpunkte

- `POST /api/stopwatch/start` - Stoppuhr starten
- `POST /api/stopwatch/pause` - Stoppuhr pausieren
- `POST /api/stopwatch/resume` - Stoppuhr fortsetzen
- `POST /api/stopwatch/stop` - Stoppuhr stoppen und zurücksetzen
- `POST /api/stopwatch/lap` - Runde hinzufügen
- `POST /api/stopwatch/record` - Zeit mit Nummer aufnehmen
  - Body: `{ "number": "123" }`
- `GET /api/stopwatch/status` - Aktuellen Stoppuhrstatus abrufen
- `GET /api/stopwatch/history` - Letzte Messungen abrufen
- `GET /api/stopwatch/active_runs` - Aktive Läufe abrufen

## Projektstruktur

```
/ (root)
├── app.py              # Hauptanwendung
├── db.py               # Datenbankhilfen
├── requirements.txt    # Python-Abhängigkeiten
├── README.md           # Diese Datei
├── .env.example        # Beispiel-Umgebungsvariablen
├── Dockerfile          # Optional: Docker-Setup
├── /routen             # Flask Blueprints
│   ├── __init__.py
│   ├── main.py         # Hauptrouten
│   ├── stopwatch.py    # Stoppuhr-Logik und API
│   └── zeitmesser.py   # Zeitmesser-Routen
├── /static             # Statische Dateien (CSS, JS)
│   ├── css/
│   └── js/
├── /templates          # HTML-Vorlagen
├── /instance           # SQLite-Datenbank (wird erzeugt)
└── /tests              # Unit-Tests (optional)
```

## Entwicklung

- Führe `pytest` aus, um Tests zu laufen.
- Für permanente Änderungen einen Pull Request erstellen.

## Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE) Datei für Details.