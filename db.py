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
                class_group TEXT NOT NULL,
                nummer TEXT NOT NULL,
                startnummer INTEGER UNIQUE,
                ill INTEGER DEFAULT 0,
                UNIQUE (class_group, nummer)
            );

            -- Klassen und zugehörige Lehrkräfte
            CREATE TABLE IF NOT EXISTS classes (
                class_group TEXT PRIMARY KEY,
                teacher TEXT NOT NULL DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS run_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                active INTEGER DEFAULT 0,
                started_at TEXT,
                ended_at TEXT
            );

            CREATE TABLE IF NOT EXISTS run_group_classes (
                run_group_id INTEGER NOT NULL,
                class_group TEXT NOT NULL,
                PRIMARY KEY (run_group_id, class_group),
                FOREIGN KEY (run_group_id) REFERENCES run_groups (id) ON DELETE CASCADE
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
            CREATE INDEX IF NOT EXISTS idx_run_group_classes_class ON run_group_classes(class_group);
        """)
        measurement_columns = {row['name'] for row in conn.execute("PRAGMA table_info(measurements)")}
        if 'run_group_id' not in measurement_columns:
            conn.execute("ALTER TABLE measurements ADD COLUMN run_group_id INTEGER")
        columns = {row['name'] for row in conn.execute("PRAGMA table_info(students)")}
        if 'name' in columns:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.execute("""
                CREATE TABLE students_without_names (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_group TEXT NOT NULL,
                    nummer TEXT NOT NULL,
                    startnummer INTEGER UNIQUE,
                    ill INTEGER DEFAULT 0,
                    UNIQUE (class_group, nummer)
                )
            """)
            conn.execute("""
                INSERT INTO students_without_names (id, class_group, nummer, ill)
                SELECT id, COALESCE(class_group, 'Unbekannt'), nummer, id, ill FROM students
            """)
            conn.execute("DROP TABLE students")
            conn.execute("ALTER TABLE students_without_names RENAME TO students")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_students_nummer ON students(nummer)")
            conn.execute("PRAGMA foreign_keys = ON")
        columns = {row['name'] for row in conn.execute("PRAGMA table_info(students)")}
        if 'startnummer' not in columns:
            conn.execute("ALTER TABLE students ADD COLUMN startnummer INTEGER")
        conn.execute("UPDATE students SET startnummer = id WHERE startnummer IS NULL")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_students_startnummer ON students(startnummer)")
        conn.execute("""
            INSERT OR IGNORE INTO classes (class_group)
            SELECT DISTINCT class_group FROM students WHERE class_group IS NOT NULL
        """)
        conn.commit()


# Datenbank beim Start initialisieren
init_db()

# ============================================================================
# SCHÜLER-VERWALTUNG
# ============================================================================

def add_student(class_group, nummer, ill=False):
    """
    Neuen Schüler hinzufügen.
    
    Args:
        class_group: Klasse/Gruppe
        nummer: Startnummer
        ill: Ist der Schüler krank? (Standard: False)
    
    Returns:
        ID des neu eingefügten Schülers
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO classes (class_group) VALUES (?)",
            (class_group,)
        )
        cursor.execute(
            "INSERT INTO students (class_group, nummer, startnummer, ill) "
            "VALUES (?, ?, COALESCE((SELECT MAX(startnummer) + 1 FROM students), 1), ?)",
            (class_group, nummer, int(ill))
        )
        conn.commit()
        return cursor.lastrowid


def get_students(include_ill=False, class_group=None, nummer=None):
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
        filters = []
        params = []
        if class_group:
            filters.append("class_group = ?")
            params.append(class_group)
        if nummer:
            filters.append("(CAST(startnummer AS TEXT) LIKE ? OR nummer LIKE ?)")
            params.append(f"%{nummer}%")
            params.append(f"%{nummer}%")
        if filters:
            query += " AND " if " WHERE " in query else " WHERE "
            query += " AND ".join(filters)
        query += " ORDER BY startnummer"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_classes():
    """Alle Klassen mit Lehrkraft und Schüleranzahl abrufen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.class_group, c.teacher, COUNT(s.id) AS student_count
            FROM classes c
            LEFT JOIN students s ON s.class_group = c.class_group
            GROUP BY c.class_group, c.teacher
            ORDER BY c.class_group
        """)
        return [dict(row) for row in cursor.fetchall()]


def update_class(old_class_group, class_group, teacher=''):
    """Klassenname und Lehrkraft aktualisieren und Verweise synchron halten."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO classes (class_group, teacher) VALUES (?, ?) "
            "ON CONFLICT(class_group) DO UPDATE SET teacher = excluded.teacher",
            (class_group, teacher)
        )
        if old_class_group != class_group:
            cursor.execute(
                "UPDATE students SET class_group = ? WHERE class_group = ?",
                (class_group, old_class_group)
            )
            cursor.execute(
                "UPDATE laeufe SET class_group = ? WHERE class_group = ?",
                (class_group, old_class_group)
            )
            cursor.execute("DELETE FROM classes WHERE class_group = ?", (old_class_group,))
        conn.commit()


def get_student_by_id(student_id):
    """Schüler anhand seiner ID abrufen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_student_by_nummer(nummer, class_group=None):
    """Schüler anhand von Startnummer, optional zusammen mit Klasse abrufen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if class_group:
            cursor.execute(
                "SELECT * FROM students WHERE nummer = ? AND class_group = ?",
                (nummer, class_group)
            )
        else:
            cursor.execute("SELECT * FROM students WHERE nummer = ? ORDER BY class_group", (nummer,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_student_by_startnummer(startnummer):
    """Schüler anhand der global eindeutigen Startnummer abrufen."""
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT * FROM students WHERE startnummer = ?",
            (str(startnummer),)
        ).fetchone()
        return dict(row) if row else None


def get_active_run_groups_for_class(class_group):
    """Aktive Laufgruppen einer Klasse abrufen."""
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT rg.id, rg.name, rg.active, rg.started_at, rg.ended_at
            FROM run_groups rg
            JOIN run_group_classes rgc ON rgc.run_group_id = rg.id
            WHERE rgc.class_group = ? AND rg.active = 1
            ORDER BY rg.started_at DESC
        """, (class_group,)).fetchall()
        return [dict(row) for row in rows]


def update_student(student_id, class_group=None, nummer=None, ill=None):
    """
    Schüler-Informationen aktualisieren (optional).
    
    Args:
        student_id: ID des Schülers
        class_group, nummer, ill: Zu aktualisierende Felder (None = nicht ändern)
    """
    # Nur die zu ändernden Felder sammeln
    updates = []
    params = []
    
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
        if class_group is not None:
            cursor.execute(
                "INSERT OR IGNORE INTO classes (class_group) VALUES (?)",
                (class_group,)
            )
        cursor.execute(f"UPDATE students SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()


def import_students(students):
    """Fügt neue Klassen-/Nummernpaare in einer Transaktion ein."""
    inserted = 0
    skipped = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for row_number, class_group, nummer in students:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO classes (class_group) VALUES (?)",
                    (class_group,)
                )
                cursor.execute(
                    "INSERT INTO students (class_group, nummer, startnummer, ill) "
                    "VALUES (?, ?, COALESCE((SELECT MAX(startnummer) + 1 FROM students), 1), 0)",
                    (class_group, nummer)
                )
                inserted += 1
            except sqlite3.IntegrityError:
                skipped.append((row_number, class_group, nummer, 'bereits vorhanden'))
        conn.commit()
    return inserted, skipped


def get_run_groups(include_inactive=True):
    """Laufgruppen mit Klassen und Status abrufen."""
    with get_db_connection() as conn:
        query = """
            SELECT rg.id, rg.name, rg.active, rg.started_at, rg.ended_at,
                   GROUP_CONCAT(rgc.class_group, ', ') AS classes
            FROM run_groups rg
            LEFT JOIN run_group_classes rgc ON rgc.run_group_id = rg.id
        """
        params = []
        if not include_inactive:
            query += " WHERE rg.active = 1"
        query += " GROUP BY rg.id ORDER BY rg.name"
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def create_run_group(name, class_groups):
    """Neue Laufgruppe mit mindestens einer Klasse anlegen."""
    class_groups = sorted({item.strip() for item in class_groups if item and item.strip()})
    if not name.strip() or not class_groups:
        raise ValueError('Name und mindestens eine Klasse sind erforderlich.')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO run_groups (name) VALUES (?)", (name.strip(),))
        group_id = cursor.lastrowid
        cursor.executemany(
            "INSERT INTO run_group_classes (run_group_id, class_group) VALUES (?, ?)",
            [(group_id, class_group) for class_group in class_groups]
        )
        conn.commit()
        return group_id


def get_run_group(run_group_id):
    """Eine Laufgruppe inklusive Klassen abrufen."""
    with get_db_connection() as conn:
        group = conn.execute(
            "SELECT id, name, active, started_at, ended_at FROM run_groups WHERE id = ?",
            (run_group_id,)
        ).fetchone()
        if not group:
            return None
        result = dict(group)
        result['classes'] = [row['class_group'] for row in conn.execute(
            "SELECT class_group FROM run_group_classes WHERE run_group_id = ? ORDER BY class_group",
            (run_group_id,)
        ).fetchall()]
        return result


def start_run_group(run_group_id):
    """Laufgruppe aktivieren; mehrere Gruppen dürfen parallel laufen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM run_groups WHERE id = ?", (run_group_id,))
        if not cursor.fetchone():
            raise ValueError('Laufgruppe nicht gefunden.')
        now = datetime.now().isoformat()
        cursor.execute(
            "UPDATE run_groups SET active = 1, started_at = ?, ended_at = NULL WHERE id = ?",
            (now, run_group_id)
        )
        conn.commit()
        return get_run_group(run_group_id)


def end_run_group(run_group_id):
    """Aktive Laufgruppe beenden."""
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE run_groups SET active = 0, ended_at = ? WHERE id = ?",
            (datetime.now().isoformat(), run_group_id)
        )
        conn.commit()


def get_active_run_group():
    groups = get_run_groups(include_inactive=False)
    return groups[0] if groups else None


def get_run_group_students(run_group_id):
    """Teilnehmerstatus einer Laufgruppe ohne kranke Schüler abrufen."""
    with get_db_connection() as conn:
        cursor = conn.execute("""
            SELECT s.id, s.class_group, s.nummer, s.startnummer, s.ill,
                   latest.zeit,
                   CASE WHEN latest.id IS NOT NULL THEN 0 ELSE 1 END AS still_running
            FROM students s
            JOIN run_group_classes rgc ON rgc.class_group = s.class_group
            LEFT JOIN (
                SELECT m.id, m.student_id, m.zeit
                FROM measurements m
                WHERE m.run_group_id = ?
                  AND m.id = (
                      SELECT MAX(m2.id) FROM measurements m2
                      WHERE m2.student_id = m.student_id AND m2.run_group_id = ?
                  )
            ) latest ON latest.student_id = s.id
            WHERE rgc.run_group_id = ? AND s.ill = 0
            ORDER BY s.class_group, CAST(s.nummer AS INTEGER), s.nummer
        """, (run_group_id, run_group_id, run_group_id))
        return [dict(row) for row in cursor.fetchall()]


def delete_student(student_id):
    """Schüler löschen."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
        conn.commit()
# ============================================================================
# LAUF-VERWALTUNG
# ============================================================================

def create_lauf(class_group, start_time=None, active=True):
    """
    Neuen Lauf für eine Klasse erstellen.
    
    Args:
        class_group: Klasse/Gruppe
        start_time: Startzeit (Standard: jetzt)
        active: Ist der Lauf aktiv? (Standard: True)
    
    Returns:
        ID des neu erstellten Laufs
    """
    if start_time is None:
        start_time = datetime.now().isoformat()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO laeufe (class_group, start_time, active) VALUES (?, ?, ?)",
            (class_group, start_time, int(active))
        )
        conn.commit()
        return cursor.lastrowid





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

def delete_lauf(lauf_id):
    """Lauf löschen (inklusive aller zugehörigen Zeitmessungen)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Zuerst alle Zeitmessungen dieses Laufs löschen
        cursor.execute("DELETE FROM measurements WHERE lauf_id = ?", (lauf_id,))
        # Dann den Lauf selbst löschen
        cursor.execute("DELETE FROM laeufe WHERE id = ?", (lauf_id,))
        conn.commit()

def restart_lauf(lauf_id):
    """Lauf zurücksetzen (alle Zeitmessungen löschen, Lauf bleibt aktiv)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Alle Zeitmessungen dieses Laufs löschen
        cursor.execute("DELETE FROM measurements WHERE lauf_id = ?", (lauf_id,))
        # Lauf als aktiv markieren (falls er deaktiviert war)
        cursor.execute("UPDATE laeufe SET active = 1 WHERE id = ?", (lauf_id,))
        conn.commit()

# ============================================================================
# ZEITMESSUNGEN
# ============================================================================

def save_measurement(student_identifier, zeit, lauf_id=None, run_group_id=None):
    """
    Zeitmessung für einen Schüler speichern.
    
    Args:
        student_identifier: Globale Startnummer
        zeit: Zeit im Format HH:MM:SS.MS
        lauf_id: Optional - alte Lauf-ID
        run_group_id: Laufgruppe, der die Messung zugeordnet wird
    
    Returns:
        ID der neuen Zeitmessung
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Die Eingabe ist immer die globale Startnummer, nie die interne ID.
        student_id = None
        if run_group_id is not None:
            matches = cursor.execute("""
                SELECT s.id, s.class_group FROM students s
                JOIN run_group_classes rgc ON rgc.class_group = s.class_group
                WHERE s.startnummer = ? AND rgc.run_group_id = ?
            """, (str(student_identifier), run_group_id)).fetchall()
            row = matches[0] if matches else None
            student_id = row['id'] if row else None
        else:
            cursor.execute("SELECT id FROM students WHERE startnummer = ?", (str(student_identifier),))
            row = cursor.fetchone()
            student_id = row['id'] if row else None
        
        # Wenn Schüler nicht existiert, Platzhalter-Schüler erstellen
        if student_id is None:
            raise ValueError('Schülernummer gehört nicht zur ausgewählten Laufgruppe.')

        cursor.execute("SELECT ill FROM students WHERE id = ?", (student_id,))
        if cursor.fetchone()['ill']:
            raise ValueError('Kranke Schüler nehmen nicht am Lauf teil.')
        
        # Falls keine Lauf-ID angegeben, aktiven Lauf der Schüler-Klasse suchen
        if lauf_id is None and run_group_id is None:
            cursor.execute("SELECT class_group FROM students WHERE id = ?", (student_id,))
            row = cursor.fetchone()
            if row and row['class_group']:
                lauf = get_active_lauf(row['class_group'])
                lauf_id = lauf['id'] if lauf else None
        
        # Zeitmessung speichern
        cursor.execute(
            "INSERT INTO measurements (student_id, lauf_id, run_group_id, zeit, timestamp) VALUES (?, ?, ?, ?, ?)",
            (student_id, lauf_id, run_group_id, zeit, datetime.now().isoformat())
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
                SELECT m.id, m.zeit, m.timestamp, s.class_group, s.nummer, s.startnummer,
                     l.class_group AS lauf_class, l.start_time AS lauf_start,
                     rg.name AS run_group_name
            FROM measurements m
            JOIN students s ON m.student_id = s.id
            LEFT JOIN laeufe l ON m.lauf_id = l.id
                 LEFT JOIN run_groups rg ON m.run_group_id = rg.id
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
            """SELECT m.id, m.zeit, m.timestamp, s.class_group, s.nummer
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
