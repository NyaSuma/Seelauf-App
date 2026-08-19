"""
Datenbank-Modul für Seelauf-App
Verwaltung von Schülern, Zeitmessungen und Laufveranstaltungen
"""
import sqlite3
from datetime import datetime
import os
from contextlib import contextmanager
from pathlib import Path

# Datenbank-Pfad konfigurieren
DB_PATH = Path(__file__).parent / 'instance' / 'seelauf.db'


def get_database_path():
    """Datenbank-Pfad dynamisch auflösen (Umgebungsvariable oder Standard)."""
    return Path(os.getenv('DATABASE_PATH', DB_PATH)).resolve()


@contextmanager
def get_db_connection():
    """
    Context Manager für Datenbankverbindungen.
    Stellt sicher, dass Verbindungen automatisch geschlossen werden.
    """
    db_path = get_database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Verbindung öffnen
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.row_factory = sqlite3.Row  # Rückgabe als dict-ähnliche Objekte
    conn.execute('PRAGMA foreign_keys = ON')  # Fremdschlüssel aktivieren
    conn.execute('PRAGMA journal_mode = WAL')  # Write-Ahead Logging für Stabilität
    
    try:
        yield conn
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Datenbank-Tabellen initialisieren (falls nicht vorhanden)."""
    with get_db_connection() as conn:
        conn.executescript("""
            -- Schüler-Tabelle
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                class_group TEXT,
                nummer TEXT UNIQUE NOT NULL,
                ill INTEGER DEFAULT 0
            );
            
            -- Zeitmessungs-Tabelle
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                lauf_id INTEGER,
                zeit TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id),
                FOREIGN KEY (lauf_id) REFERENCES laeufe (id)
            );
            
            -- Lauf-Veranstaltungen (z.B. pro Klasse)
            CREATE TABLE IF NOT EXISTS laeufe (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_group TEXT NOT NULL,
                start_time TEXT NOT NULL,
                active INTEGER DEFAULT 1
            );
            
            -- Indizes für schnellere Abfragen
            CREATE INDEX IF NOT EXISTS idx_students_nummer ON students(nummer);
            CREATE INDEX IF NOT EXISTS idx_measurements_student_id ON measurements(student_id);
            CREATE INDEX IF NOT EXISTS idx_measurements_lauf_id ON measurements(lauf_id);
            CREATE INDEX IF NOT EXISTS idx_laeufe_class_group ON laeufe(class_group);
        """)
        conn.commit()


# Datenbank beim Start initialisieren
init_db()

# ============================================================================
# SCHÜLER-VERWALTUNG
# ============================================================================

def add_student(name, class_group, nummer, ill=False):
    """
    Neuen Schüler hinzufügen.
    
    Args:
        name: Name des Schülers
        class_group: Klasse/Gruppe
        nummer: Startnummer
        ill: Ist der Schüler krank? (Standard: False)
    
    Returns:
        ID des neu eingefügten Schülers
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO students (name, class_group, nummer, ill) VALUES (?, ?, ?, ?)",
            (name, class_group, nummer, int(ill))
        )
        conn.commit()
        return cursor.lastrowid


def get_students(include_ill=False):
    """
    Alle Schüler abrufen.
    
    Args:
        include_ill: Auch kranke Schüler anzeigen? (Standard: nur gesunde)
    
    Returns:
        Liste aller Schüler als Dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM students"
        if not include_ill:
            query += " WHERE ill = 0"
        query += " ORDER BY class_group, name"
        cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]


def get_student_by_id(student_id):
    """Schüler anhand seiner ID abrufen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_student_by_nummer(nummer):
    """Schüler anhand seiner Startnummer abrufen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE nummer = ?", (nummer,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_student(student_id, name=None, class_group=None, nummer=None, ill=None):
    """
    Schüler-Informationen aktualisieren (optional).
    
    Args:
        student_id: ID des Schülers
        name, class_group, nummer, ill: Zu aktualisierende Felder (None = nicht ändern)
    """
    # Nur die zu ändernden Felder sammeln
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = ?")
        params.append(name)
    if class_group is not None:
        updates.append("class_group = ?")
        params.append(class_group)
    if nummer is not None:
        updates.append("nummer = ?")
        params.append(nummer)
    if ill is not None:
        updates.append("ill = ?")
        params.append(int(ill))
    
    if not updates:
        return  # Nichts zu ändern
    
    params.append(student_id)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE students SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()


def delete_student(student_id):
    """Schüler löschen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()

# ============================================================================
# LAUF-VERANSTALTUNGEN (z.B. Sporttag pro Klasse)
# ============================================================================

def start_lauf(class_group):
    """
    Neuen Lauf für eine Klasse starten.
    (Beendet automatisch vorherige Läufe dieser Klasse)
    
    Args:
        class_group: Klasse/Gruppe
    
    Returns:
        ID des neuen Laufs
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Vorherige aktive Läufe deaktivieren
        cursor.execute(
            "UPDATE laeufe SET active = 0 WHERE class_group = ? AND active = 1",
            (class_group,)
        )
        # Neuen Lauf starten
        cursor.execute(
            "INSERT INTO laeufe (class_group, start_time, active) VALUES (?, ?, 1)",
            (class_group, datetime.now().isoformat())
        )
        conn.commit()
        return cursor.lastrowid


def get_active_lauf(class_group):
    """Aktuellen aktiven Lauf für eine Klasse abrufen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM laeufe WHERE class_group = ? AND active = 1 ORDER BY start_time DESC LIMIT 1",
            (class_group,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def get_active_runs():
    """Alle aktuell aktiven Läufe abrufen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM laeufe WHERE active = 1 ORDER BY start_time DESC")
        return [dict(row) for row in cursor.fetchall()]


def get_laeufe(limit=50):
    """Frühere Läufe abrufen (neueste zuerst)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM laeufe ORDER BY start_time DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]


def end_lauf(lauf_id):
    """Lauf beenden (als inaktiv markieren)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE laeufe SET active = 0 WHERE id = ?", (lauf_id,))
        conn.commit()

# ============================================================================
# ZEITMESSUNGEN
# ============================================================================

def save_measurement(student_identifier, zeit, lauf_id=None):
    """
    Zeitmessung für einen Schüler speichern.
    
    Args:
        student_identifier: Schüler-ID (int) oder Startnummer (str)
        zeit: Zeit im Format HH:MM:SS.MS
        lauf_id: Optional - Lauf-ID (wenn nicht angegeben, wird aktiver Lauf gesucht)
    
    Returns:
        ID der neuen Zeitmessung
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Schüler-ID auflösen (versuche zuerst als ID, dann als Nummer)
        student_id = None
        try:
            student_id = int(student_identifier)
            cursor.execute("SELECT id FROM students WHERE id = ?", (student_id,))
            if not cursor.fetchone():
                student_id = None
        except (ValueError, TypeError):
            pass
        
        # Wenn nicht als ID gefunden, nach Nummer suchen
        if student_id is None:
            cursor.execute("SELECT id FROM students WHERE nummer = ?", (str(student_identifier),))
            row = cursor.fetchone()
            student_id = row['id'] if row else None
        
        # Wenn Schüler nicht existiert, Platzhalter-Schüler erstellen
        if student_id is None:
            cursor.execute(
                "INSERT INTO students (name, class_group, nummer, ill) VALUES (?, ?, ?, ?)",
                ("", None, str(student_identifier), 0)
            )
            student_id = cursor.lastrowid
        
        # Falls keine Lauf-ID angegeben, aktiven Lauf der Schüler-Klasse suchen
        if lauf_id is None:
            cursor.execute("SELECT class_group FROM students WHERE id = ?", (student_id,))
            row = cursor.fetchone()
            if row and row['class_group']:
                lauf = get_active_lauf(row['class_group'])
                lauf_id = lauf['id'] if lauf else None
        
        # Zeitmessung speichern
        cursor.execute(
            "INSERT INTO measurements (student_id, lauf_id, zeit, timestamp) VALUES (?, ?, ?, ?)",
            (student_id, lauf_id, zeit, datetime.now().isoformat())
        )
        conn.commit()
        return cursor.lastrowid


def get_measurements(limit=None):
    """
    Alle Zeitmessungen mit Schüler- und Lauf-Info abrufen.
    
    Args:
        limit: Maximale Anzahl (Standard: alle)
    
    Returns:
        Liste mit Zeitmessungen (mit Student und Lauf-Details)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT m.id, m.zeit, m.timestamp, s.name, s.class_group, s.nummer,
                   l.class_group AS lauf_class, l.start_time AS lauf_start
            FROM measurements m
            JOIN students s ON m.student_id = s.id
            LEFT JOIN laeufe l ON m.lauf_id = l.id
            ORDER BY m.id DESC
        """
        if limit:
            query += " LIMIT ?"
            cursor.execute(query, (limit,))
        else:
            cursor.execute(query)
        return [dict(row) for row in cursor.fetchall()]


def get_recent_measurements(limit=20):
    """Die neuesten Zeitmessungen abrufen."""
    return get_measurements(limit=limit)


def get_measurements_by_student(student_id):
    """Alle Zeitmessungen eines bestimmten Schülers abrufen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, zeit, timestamp FROM measurements WHERE student_id = ? ORDER BY id DESC",
            (student_id,)
        )
        return [dict(row) for row in cursor.fetchall()]


def get_measurements_by_number(nummer):
    """Alle Zeitmessungen für eine Startnummer abrufen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT m.id, m.zeit, m.timestamp, s.name, s.class_group, s.nummer
               FROM measurements m
               JOIN students s ON m.student_id = s.id
               WHERE s.nummer = ?
               ORDER BY m.id DESC""",
            (nummer,)
        )
        return [dict(row) for row in cursor.fetchall()]


def clear_measurements():
    """Alle Zeitmessungen löschen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM measurements")
        conn.commit()
