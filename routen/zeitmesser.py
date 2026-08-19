import re
from flask import Blueprint, render_template, jsonify, request

from routen.stopwatch import stopwatch
import db

zeitmesser_bp = Blueprint('zeitmesser', __name__, url_prefix='/zeitmesser')
api_bp = Blueprint('api', __name__, url_prefix='/api/stopwatch')

# Time format validation: HH:MM:SS.MS
TIME_PATTERN = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{2}$')


@zeitmesser_bp.route('/')
def zeitmesser():
    """Stopwatch UI."""
    return render_template('zeitmesser.html')


# ---- STOPWATCH CONTROL ----

@api_bp.route('/start', methods=['POST'])
def api_start():
    """Start stopwatch."""
    stopwatch.start()
    return jsonify(stopwatch.get_status())


@api_bp.route('/pause', methods=['POST'])
def api_pause():
    """Pause stopwatch."""
    stopwatch.pause()
    return jsonify(stopwatch.get_status())


@api_bp.route('/resume', methods=['POST'])
def api_resume():
    """Resume stopwatch."""
    stopwatch.resume()
    return jsonify(stopwatch.get_status())


@api_bp.route('/stop', methods=['POST'])
def api_stop():
    """Stop stopwatch."""
    stopwatch.stop()
    return jsonify(stopwatch.get_status())


@api_bp.route('/lap', methods=['POST'])
def api_lap():
    """Add lap."""
    stopwatch.add_lap()
    return jsonify(stopwatch.get_status())


@api_bp.route('/status', methods=['GET'])
def api_status():
    """Get stopwatch status."""
    return jsonify(stopwatch.get_status())


# ---- TIME RECORDING ----

@api_bp.route('/record', methods=['POST'])
def api_record():
    """Record time for a student."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Keine Daten empfangen'}), 400

    number = data.get('number')
    if not number:
        return jsonify({'success': False, 'error': 'Nummer erforderlich'}), 400

    # Get formatted time from stopwatch
    time_str = stopwatch.get_formatted_time()
    
    if not TIME_PATTERN.match(time_str):
        return jsonify({'success': False, 'error': 'Ungültiges Zeitformat'}), 400

    try:
        student = db.get_student_by_nummer(number)
        if not student:
            return jsonify({'success': False, 'error': 'Schüler nicht gefunden'}), 404

        db.save_measurement(student['id'], time_str)
        return jsonify({'success': True, 'time': time_str, 'student_name': student['name']})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Datenbankfehler: {str(e)}'}), 500


# ---- HISTORY ----

@api_bp.route('/history', methods=['GET'])
def api_history():
    """Get recent measurements."""
    try:
        return jsonify(db.get_recent_measurements(limit=20))
    except Exception as e:
        return jsonify({'success': False, 'error': f'Datenbankfehler: {str(e)}'}), 500


@api_bp.route('/active_runs', methods=['GET'])
def api_active_runs():
    """Get active running events."""
    try:
        return jsonify(db.get_active_runs())
    except Exception as e:
        return jsonify({'success': False, 'error': f'Datenbankfehler: {str(e)}'}), 500
