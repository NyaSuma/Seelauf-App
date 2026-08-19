"""
Stopwatch-Klasse für Seelauf-App
Implementierung einer Stoppuhr mit Pause/Fortsetzen-Funktionalität
"""
import time
from datetime import datetime


class Stopwatch:
    """
    Einfache Stopwatch-Implementierung mit Pause/Fortsetzen-Funktion.
    Verfolgt die verstrichene Zeit, Pausen und Zwischenzeiten.
    """
    
    def __init__(self):
        # Zeitpunkt des Starts (Unix-Timestamp)
        self.start_time = None
        # Zeitpunkt der Pause (Unix-Timestamp)
        self.pause_time = None
        # Gesamte Pausenzeiten (in Sekunden)
        self.total_pause_duration = 0
        # Flags für Zustand
        self.is_running = False
        self.is_paused = False
        # Liste der Zwischenzeiten
        self.laps = []
    
    def start(self):
        """Stoppuhr starten (nur wenn nicht bereits läuft)."""
        if not self.is_running and not self.is_paused:
            self.start_time = time.time()
            self.pause_time = None
            self.total_pause_duration = 0
            self.is_running = True
            self.is_paused = False
            self.laps = []
    
    def pause(self):
        """Stoppuhr pausieren."""
        if self.is_running and not self.is_paused:
            self.pause_time = time.time()
            self.is_running = False
            self.is_paused = True
    
    def resume(self):
        """Stoppuhr fortsetzen (nach Pause)."""
        if self.is_paused and self.pause_time:
            # Addiere die Pausendauer zur Gesamtpausendauer
            self.total_pause_duration += time.time() - self.pause_time
            self.pause_time = None
            self.is_running = True
            self.is_paused = False
    
    def stop(self):
        """Stoppuhr stoppen und zurücksetzen."""
        self.is_running = False
        self.is_paused = False
        self.start_time = None
        self.pause_time = None
        self.total_pause_duration = 0
        self.laps = []
    
    def get_elapsed_time(self):
        """
        Verstrichene Zeit abrufen (in Sekunden).
        Berücksichtigt Pausen.
        """
        if self.start_time is None:
            return 0
        
        if self.is_running:
            # Aktiv laufend: Aktuelle Zeit - Start - Pausen
            return time.time() - self.start_time - self.total_pause_duration
        elif self.is_paused and self.pause_time:
            # Pausiert: Pausenzeit - Start - Pausen
            return self.pause_time - self.start_time - self.total_pause_duration
        return 0
    
    def add_lap(self):
        """
        Zwischenzeit hinzufügen.
        Speichert die verstrichene Zeit mit Timestamp.
        """
        if self.is_running or self.is_paused:
            elapsed = self.get_elapsed_time()
            self.laps.append({
                'lap_number': len(self.laps) + 1,
                'time': elapsed,
                'timestamp': datetime.now().isoformat()
            })
            return elapsed
        return None
    
    def get_formatted_time(self, seconds=None):
        """
        Zeit formatiert als String: HH:MM:SS.MS
        Beispiel: "00:01:23.45"
        """
        if seconds is None:
            seconds = self.get_elapsed_time()
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 100)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:02d}"
    
    def get_status(self):
        """
        Stopwatch-Status abrufen.
        
        Returns:
            Dict mit Zustand, verstrichener Zeit und Zwischenzeiten
        """
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'elapsed_time': self.get_elapsed_time(),
            'formatted_time': self.get_formatted_time(),
            'laps': self.laps
        }


# Globale Stopwatch-Instanz (wird von zeitmesser.py verwendet)
stopwatch = Stopwatch()
