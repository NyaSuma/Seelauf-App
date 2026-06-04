from flask import Blueprint, render_template, jsonify, request
from routen.stopwatch import stopwatch
import db
import re

zeitmesser_bp = Blueprint('zeitmesser', __name__, url_prefix='/zeitmesser')
api_bp = Blueprint('api', __name__, url_prefix='/api/stopwatch')

# Time format validation regex: HH:MM:SS.ms (with two-digit milliseconds)
TIME_FORMAT_REGEX = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{2}$')

@zeitmesser_bp.route('/')
def zeitmesser():
    return render_template('Zeitmesser.html')

@api_bp.route('/start', methods=['POST'])
def api_start():
    stopwatch.start()
    return jsonify(stopwatch.get_status())

@api_bp.route('/pause', methods=['POST'])
def api_pause():
    stopwatch.pause()
    return jsonify(stopwatch.get_status())

@api_bp.route('/resume', methods=['POST'])
def api_resume():
    stopwatch.resume()
    return jsonify(stopwatch.get_status())

@api_bp.route('/stop', methods=['POST'])
def api_stop():
    stopwatch.stop()
    return jsonify(stopwatch.get_status())

@api_bp.route('/lap', methods=['POST'])
def api_lap():
    stopwatch.add_lap()
    return jsonify(stopwatch.get_status())

@api_bp.route('/record', methods=['POST'])
def api_record():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Keine Daten empfangen'}), 400

    number = data.get('number')
    if not number:
        return jsonify({'success': False, 'error': 'Nummer erforderlich'}), 400

    # Use the stopwatch's current formatted time instead of trusting client-sent time
    time_str = stopwatch.get_formatted_time()

    # Optional: Validate the time format (should always be valid from stopwatch, but just in case)
    if not TIME_FORMAT_REGEX.match(time_str):
        return jsonify({'success': False, 'error': 'Ungültiges Zeitformat'}), 400

    try:
        # Look up student by nummer
        student = db.get_student_by_nummer(number)
        if not student:
            return jsonify({'success': False, 'error': 'Schüler mit dieser Nummer nicht gefunden'}), 404

        # Save measurement (DB will automatically fetch active lauf for student's class if needed)
        db.save_measurement(student['id'], time_str)
        return jsonify({'success': True, 'time': time_str, 'student_name': student['name']})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Datenbankfehler: {str(e)}'}), 500

@api_bp.route('/status', methods=['GET'])
def api_status():
    return jsonify(stopwatch.get_status())