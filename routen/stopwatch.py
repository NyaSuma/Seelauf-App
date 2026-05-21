import time
from datetime import datetime

class Stopwatch:
    def __init__(self):
        self.start_time = None
        self.pause_time = None
        self.total_pause_duration = 0
        self.is_running = False
        self.is_paused = False
        self.laps = []

    def start(self):
        """Startet den Zeitmesser"""
        if not self.is_running:
            self.start_time = time.time() - self.total_pause_duration
            self.is_running = True
            self.is_paused = False

    def pause(self):
        """Pausiert den Zeitmesser"""
        if self.is_running and not self.is_paused:
            self.pause_time = time.time()
            self.is_running = False
            self.is_paused = True

    def resume(self):
        """Setzt den Zeitmesser fort"""
        if self.is_paused and self.pause_time:
            pause_duration = time.time() - self.pause_time
            self.total_pause_duration += pause_duration
            self.is_running = True
            self.is_paused = False

    def stop(self):
        """Stoppt den Zeitmesser und setzt es zurück"""
        self.is_running = False
        self.is_paused = False
        self.start_time = None
        self.pause_time = None
        self.total_pause_duration = 0
        self.laps = []

    def get_elapsed_time(self):
        """Gibt die verstrichene Zeit in Sekunden zurück"""
        if self.start_time is None:
            return 0
        
        if self.is_running:
            return time.time() - self.start_time
        else:
            return self.pause_time - self.start_time if self.pause_time else 0

    def add_lap(self):
        """Fügt eine Runde hinzu"""
        if self.is_running or self.is_paused:
            elapsed = self.get_elapsed_time()
            self.laps.append({
                'lap_number': len(self.laps) + 1,
                'time': elapsed,
                'timestamp': datetime.now().isoformat()
            })
            return elapsed

    def get_formatted_time(self, seconds=None):
        """Formatiert die Zeit als HH:MM:SS.MS"""
        if seconds is None:
            seconds = self.get_elapsed_time()
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 100)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:02d}"

    def get_status(self):
        """Gibt den aktuellen Status zurück"""
        return {
            'is_running': self.is_running,
            'is_paused': self.is_paused,
            'elapsed_time': self.get_elapsed_time(),
            'formatted_time': self.get_formatted_time(),
            'laps': self.laps
        }

# Globale Instanz
stopwatch = Stopwatch()
