import sqlite3
from datetime import datetime

# Datenbank für die Seelauf App

def verbindung_herstellen():
    return sqlite3.connect("instance/seelauf.db")

# CRUD Operationen für Zeitmessungen:

# CREATE - Messung speichern
def save_measurement(nummer, zeit):
    """Speichert eine Zeitmessung mit Nummer in der Datenbank"""
    verbindung = verbindung_herstellen()
    cursor = verbindung.cursor()
    timestamp = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO seelauf_messungen (nummer, zeit, timestamp)
    VALUES (?, ?, ?)
    """, (nummer, zeit, timestamp))
    verbindung.commit()
    verbindung.close()

# READ - Alle Messungen abrufen
def get_measurements():
    """Ruft alle gespeicherten Zeitmessungen ab"""
    verbindung = verbindung_herstellen()
    cursor = verbindung.cursor()
    cursor.execute("SELECT * FROM seelauf_messungen ORDER BY id DESC")
    alle_messungen = cursor.fetchall()
    verbindung.close()
    return alle_messungen

# READ - Messung nach Nummer
def get_measurement_by_number(nummer):
    """Ruft Messungen für eine bestimmte Nummer ab"""
    verbindung = verbindung_herstellen()
    cursor = verbindung.cursor()
    cursor.execute("SELECT * FROM seelauf_messungen WHERE nummer = ? ORDER BY id DESC", (nummer,))
    messungen = cursor.fetchall()
    verbindung.close()
    return messungen

# UPDATE
def update_measurement(id, nummer, zeit):
    """Aktualisiert eine Zeitmessung"""
    verbindung = verbindung_herstellen()
    cursor = verbindung.cursor()
    cursor.execute("""
    UPDATE seelauf_messungen
    SET nummer = ?, zeit = ?
    WHERE id = ?
    """, (nummer, zeit, id))
    verbindung.commit()
    verbindung.close()

# DELETE
def delete_measurement(id):
    """Löscht eine Zeitmessung"""
    verbindung = verbindung_herstellen()
    cursor = verbindung.cursor()
    cursor.execute("DELETE FROM seelauf_messungen WHERE id = ?", (id,))
    verbindung.commit()
    verbindung.close()

# DELETE ALL
def clear_measurements():
    """Löscht alle Zeitmessungen"""
    verbindung = verbindung_herstellen()
    cursor = verbindung.cursor()
    cursor.execute("DELETE FROM seelauf_messungen")
    verbindung.commit()
    verbindung.close()


# Tabelle erstellen
verbindung = verbindung_herstellen()
cursor = verbindung.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS seelauf_messungen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nummer TEXT NOT NULL,
    zeit TEXT NOT NULL,
    timestamp TEXT NOT NULL
)
""")

verbindung.commit()
verbindung.close()
