import sqlite3

# Erstellt eine beispielhafte Datenbank. Achtung: Daten müssen bearbeitet werden.

def verbindung_herstellen():
    return sqlite3.connect("NAME_EURER_DB.db") # Hier den Namen eurer DB angeben

# CRUD Operationen:

# CREATE
def hinzufügen(attribut1, attribut2, attribut3):
    verbindung = verbindung_herstellen()
    cursor = verbindung.cursor()
    cursor.execute("""
    INSERT INTO name_der_tabelle (attribut1, attribut2, attribut3)
    VALUES (?, ?, ?)
    """, (attribut1, attribut2, attribut3))
    verbindung.commit()
    verbindung.close()

# READ
def abfragen():
    verbindung = verbindung_herstellen()
    cursor = verbindung.cursor()
    cursor.execute("SELECT * FROM name_der_tabelle")
    alle_daten = cursor.fetchall()
    verbindung.close()
    return alle_daten

# UPDATE
def update_attribut1(id, attribut1):
    verbindung = verbindung_herstellen()
    cursor = verbindung.cursor()
    cursor.execute("""
    UPDATE name_der_tabelle
    SET attribut1 = ?
    WHERE id = ?
    """, (attribut1, id))
    verbindung.commit()
    verbindung.close()

# DELETE
def delete(id):
    verbindung = verbindung_herstellen()
    cursor = verbindung.cursor()
    cursor.execute("""
    DELETE FROM name_der_tabelle
    WHERE id = ?
    """, (id,))
    verbindung.commit()
    verbindung.close()


# Tabelle erstellen
verbindung = verbindung_herstellen()
cursor = verbindung.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS name_der_tabelle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attribut1 TEXT,
    attribut2 INTEGER, 
    attribut3 TEXT          
               )
               """)

verbindung.commit() # speichert Änderungen
verbindung.close() # schließt die Verbindung
