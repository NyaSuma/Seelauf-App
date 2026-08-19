"""
Zeitmesser-Modul für Seelauf-App
Stopwatch-Interface und RESTful API für Zeitmessungen
"""
import re
from flask import Blueprint, render_template, jsonify, request

from routen.stopwatch import stopwatch
import db

zeitmesser_bp = Blueprint('zeitmesser', __name__, url_prefix='/zeitmesser')
api_bp = Blueprint('api', __name__, url_prefix='/api/stopwatch')

# Zeitformat-Validierung: HH:MM:SS.MS (z.B. "12:34:56.78")
TIME_PATTERN = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{2}$')


# ============================================================================
# ZEITMESSER-INTERFACE
# ============================================================================

@zeitmesser_bp.route('/')
def zeitmesser():
    """Zeitmesser-UI: Stopwatch-Bedienoberfläche."""
    return render_template('zeitmesser.html')


# ============================================================================
# STOPWATCH-STEUERUNG (API)
# ============================================================================

@api_bp.route('/start', methods=['POST'])
def api_start():
    """Stopwatch starten."""
    stopwatch.start()
    return jsonify(stopwatch.get_status())


@api_bp.route('/pause', methods=['POST'])
def api_pause():
    """Stopwatch pausieren."""
    stopwatch.pause()
    return jsonify(stopwatch.get_status())


@api_bp.route('/resume', methods=['POST'])
def api_resume():
    """Stopwatch fortsetzen."""
    stopwatch.resume()
    return jsonify(stopwatch.get_status())


@api_bp.route('/stop', methods=['POST'])
def api_stop():
    """Stopwatch stoppen."""
    stopwatch.stop()
    return jsonify(stopwatch.get_status())


@api_bp.route('/lap', methods=['POST'])
def api_lap():
    """Zwischenzeit (Lap) hinzufügen."""
    stopwatch.add_lap()
    return jsonify(stopwatch.get_status())


@api_bp.route('/status', methods=['GET'])
def api_status():
    """Status der Stopwatch abrufen."""
    return jsonify(stopwatch.get_status())


# ============================================================================
# ZEITMESSUNGS-ERFASSUNG
# ============================================================================

@api_bp.route('/record', methods=['POST'])
def api_record():
    """
    Zeit für einen Schüler aufzeichnen.
    Erwartet JSON mit Schüler-Nummer.
    """
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Keine Daten empfangen'}), 400

    number = data.get('number')
    if not number:
        return jsonify({'success': False, 'error': 'Nummer erforderlich'}), 400

    # Formatierte Zeit von Stopwatch abrufen
    time_str = stopwatch.get_formatted_time()
    
    # Validiere Zeitformat mit Regex
    if not TIME_PATTERN.match(time_str):
        return jsonify({'success': False, 'error': 'Ungültiges Zeitformat'}), 400

    try:
        student = db.get_student_by_nummer(number)
        if not student:
            return jsonify({'success': False, 'error': 'Schüler nicht gefunden'}), 404

        # Speichere Zeitmessung in Datenbank
        db.save_measurement(student['id'], time_str)
        return jsonify({'success': True, 'time': time_str, 'student_name': student['name']})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Datenbankfehler: {str(e)}'}), 500


# ============================================================================
# VERLAUF UND STATUS
# ============================================================================

@api_bp.route('/history', methods=['GET'])
def api_history():
    """Letzte Zeitmessungen abrufen."""
    try:
        return jsonify(db.get_recent_measurements(limit=20))
    except Exception as e:
        return jsonify({'success': False, 'error': f'Datenbankfehler: {str(e)}'}), 500


@api_bp.route('/active_runs', methods=['GET'])
def api_active_runs():
    """Aktive Lauf-Veranstaltungen abrufen."""
    try:
        return jsonify(db.get_active_runs())
    except Exception as e:
        return jsonify({'success': False, 'error': f'Datenbankfehler: {str(e)}'}), 500
