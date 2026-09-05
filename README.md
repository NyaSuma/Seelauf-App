# Seelauf-App

Ein Flask-basiertes Anwendung zur Verwaltung von Schülerlaufzeiten mit Admin-Dashboard und Zeitmesser-Interface.

## Features

- 🏃 Zeitmesser mit Start/Pause/Stop-Funktionalität
- 📊 Admin-Dashboard zur Verwaltung von Schülern und Laufzeiten
- 📋 Schüler- und Klassenverwaltung
- ⏱️ Zeitmessungen mit automatischem Speichern
- 🔐 Sichere Admin-Authentifizierung

## Installation

### Voraussetzungen
- Python 3.8+
- pip (Python Package Manager)

### Setup

1. **Repository klonen:**
```bash
cd f:\Informatik\Seelauf-App
```
ssss
2. **Virtual Environment erstellen:**
```bash
python -m venv .venv
```

3. **Virtual Environment aktivieren:**
```bash
# Windows
.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate
```

4. **Dependencies installieren:**
```bash
pip install -r requirements.txt
```

5. **Environment-Konfiguration:**
```bash
cp .env.example .env
# .env anpassen (Admin-Code ändern, etc.)
```

6. **Anwendung starten:**
```bash
python app.py
```

Die App ist dann unter `http://localhost:8000` verfügbar.

## Struktur

```
seelauf-app/
├── app.py              # Haupt-Anwendung
├── db.py               # Datenbankmodul
├── requirements.txt    # Python-Dependencies
├── routen/             # Route-Module
│   ├── main.py         # Haupt-Routes
│   ├── admin.py        # Admin-Routes
│   ├── zeitmesser.py   # Zeitmesser-Routes
│   └── stopwatch.py    # Stopwatch-Klasse
├── templates/          # HTML-Templates
├── static/             # CSS, JS, Images
│   ├── css/
│   ├── js/
│   └── images/
└── instance/           # Instanz-Verzeichnis (Datenbank)
```

## Verwendung

### Zeitmesser
- Unter `/zeitmesser` verfügbar
- Start/Pause/Stop-Buttons zum Steuern der Zeit
- Nummern eingeben und Zeit aufzeichnen

### Admin-Panel
- Login unter `/admin/login`
- Default Admin-Code: `admin123`
- Schüler hinzufügen/bearbeiten/löschen
- Laufzeiten verwalten
- Zeitmessungen einsehen

## Konfiguration

Die Konfiguration erfolgt über die `.env` Datei:
- `FLASK_DEBUG`: Debug-Modus aktivieren
- `SECRET_KEY`: Session-Verschlüsselung
- `ADMIN_CODE`: Admin-Zugangsscode
- `DATABASE_PATH`: Pfad zur SQLite-Datenbank

## Datenbankschema

### students
- id, class_group, nummer, startnummer, ill
- `startnummer` ist global eindeutig und wird automatisch vergeben.

### classes
- class_group, teacher
- Klassen können im Admin-Bereich umbenannt und einer Lehrkraft zugeordnet werden.

### run_groups
- Laufgruppen fassen mehrere Klassen zusammen.
- Im Zeitmesser kann eine Laufgruppe gestartet und ausgewählt werden.
- Jede Laufgruppe besitzt eine eigene Stoppuhr und kann zeitversetzt zu anderen Gruppen laufen.
- Die Teilnehmerübersicht zeigt laufende und bereits gemessene Personen.
- Kranke Schüler werden automatisch nicht als Teilnehmer geführt.
- Für die Zeitnahme genügt die globale Startnummer; eine Laufgruppe muss dafür nicht ausgewählt werden.

### measurements
- id, student_id, lauf_id, zeit, timestamp

### laeufe
- id, class_group, start_time, active

### Excel-Import
Im Admin-Bereich können `.xlsx`-Dateien importiert werden. Die Tabelle benötigt
eine Klasse und die Anzahl der Schüler. Bei `10a | 36` werden automatisch die
Nummern `1` bis `36` für die Klasse `10a` angelegt. Namen werden nicht gespeichert;
eine Person wird ausschließlich durch Klasse und Nummer identifiziert.

# Virtual Environment aktivieren
.venv\Scripts\Activate.ps1

# Dependencies installieren
pip install -r requirements.txt

# App mit Debug-Modus starten
set FLASK_DEBUG=1
python app.py
``
