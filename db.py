import sqlite3
from datetime import datetime
import os
from contextlib import contextmanager

# Database path - can be overridden by environment variable or app config
DATABASE_PATH = os.getenv('DATABASE_PATH', 'instance/seelauf.db')

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row  # Return rows as dictionary-like objects
        yield conn
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

def init_db():
    """Initialize the database tables if they don't exist."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Students table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                class_group TEXT,
                nummer TEXT UNIQUE NOT NULL,
                ill INTEGER DEFAULT 0
            )
            """)
            # Measurements table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                lauf_id INTEGER,
                zeit TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id),
                FOREIGN KEY (lauf_id) REFERENCES laeufe (id)
            )
            """)
            # Läufe (running events) table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS laeufe (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_group TEXT NOT NULL,
                start_time TEXT NOT NULL,
                active INTEGER DEFAULT 1
            )
            """)
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")
        raise

# Initialize database on module import
init_db()

# ---- STUDENT CRUD ----
def add_student(name, class_group, nummer, ill=False):
    """Fügt einen neuen Schüler hinzu."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO students (name, class_group, nummer, ill)
            VALUES (?, ?, ?, ?)
            """, (name, class_group, nummer, 1 if ill else 0))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error adding student: {e}")
        raise

def get_students(include_ill=False):
    """Ruft alle Schüler ab. Wenn include_ill=False, nur gesunde Schüler."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if include_ill:
                cursor.execute("SELECT * FROM students ORDER BY class_group, name")
            else:
                cursor.execute("SELECT * FROM students WHERE ill = 0 ORDER BY class_group, name")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error retrieving students: {e}")
        raise

def get_student_by_nummer(nummer):
    """Ruft einen Schüler anhand seiner Nummer ab."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE nummer = ?", (nummer,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Error retrieving student by nummer: {e}")
        raise

def get_student_by_id(student_id):
    """Ruft einen Schüler anhand seiner ID ab."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Error retrieving student by id: {e}")
        raise

def update_student(student_id, name=None, class_group=None, nummer=None, ill=None):
    """Aktualisiert einen Schüler."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
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
                params.append(1 if ill else 0)
            if not updates:
                return
            params.append(student_id)
            query = f"UPDATE students SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, tuple(params))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error updating student: {e}")
        raise

def delete_student(student_id):
    """Löscht einen Schüler."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error deleting student: {e}")
        raise

# ---- LÄUFE ----
def start_lauf(class_group):
    """Startet einen Lauf für die angegebene Klasse/Gruppe.
    Deaktiviert eventuell vorher aktive Läufe derselben Gruppe (optional)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Optionally deactivate previous active lauf for same group
            cursor.execute("UPDATE laeufe SET active = 0 WHERE class_group = ? AND active = 1", (class_group,))
            start_time = datetime.now().isoformat()
            cursor.execute("""
            INSERT INTO laeufe (class_group, start_time, active)
            VALUES (?, ?, 1)
            """, (class_group, start_time))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error starting lauf: {e}")
        raise

def get_active_lauf(class_group):
    """Gibt den letzten aktiven Lauf für die angegebene Klasse/Gruppe zurück."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM laeufe WHERE class_group = ? AND active = 1 ORDER BY start_time DESC LIMIT 1
            """, (class_group,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"Error retrieving active lauf: {e}")
        raise

def get_laeufe(limit=50):
    """Ruft früher completed und aktive Läufe ab (neueste zuerst)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM laeufe ORDER BY start_time DESC LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error retrieving laeufe: {e}")
        raise

def end_lauf(lauf_id):
    """Deaktiviert einen Lauf (setzt active=0)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE laeufe SET active = 0 WHERE id = ?", (lauf_id,))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error ending lauf: {e}")
        raise

# ---- MEASUREMENTS ----
def save_measurement(student_id, zeit, lauf_id=None):
    """Speichert eine Zeitmessung für einen Schüler.
    Wenn lauf_id nicht übergeben wird, wird der aktive Lauf für die Klasse des Schülers gesucht."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if lauf_id is None:
                # Get student's class group
                cursor.execute("SELECT class_group FROM students WHERE id = ?", (student_id,))
                row = cursor.fetchone()
                if row:
                    class_group = row['class_group']
                    lauf = get_active_lauf(class_group)
                    lauf_id = lauf['id'] if lauf else None
            timestamp = datetime.now().isoformat()
            cursor.execute("""
            INSERT INTO measurements (student_id, lauf_id, zeit, timestamp)
            VALUES (?, ?, ?, ?)
            """, (student_id, lauf_id, zeit, timestamp))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"Error saving measurement: {e}")
        raise

def get_measurements(limit=None):
    """Ruft alle Messungen mit Schüler- und Lauf-Info ab."""
    try:
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
                query += f" LIMIT {limit}"
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error retrieving measurements: {e}")
        raise

def get_measurements_by_student(student_id):
    """Ruft alle Messungen eines bestimmten Schülers ab."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT m.id, m.zeit, m.timestamp
            FROM measurements m
            WHERE m.student_id = ?
            ORDER BY m.id DESC
            """, (student_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"Error retrieving measurements for student: {e}")
        raise

def clear_measurements():
    """Löscht alle Zeitmessungen."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM measurements")
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error clearing measurements: {e}")
        raise