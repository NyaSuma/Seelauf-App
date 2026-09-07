"""
Zeitmesser-Modul für Seelauf-App
Stopwatch-Interface und RESTful API für Zeitmessungen
"""
import re
from flask import Blueprint, render_template, jsonify, request

from routen.stopwatch import Stopwatch
import db

zeitmesser_bp = Blueprint('zeitmesser', __name__, url_prefix='/zeitmesser')
api_bp = Blueprint('api', __name__, url_prefix='/api/stopwatch')

# Zeitformat-Validierung: HH:MM:SS.MS (z.B. "12:34:56.78")
TIME_PATTERN = re.compile(r'^\d{2}:\d{2}:\d{2}\.\d{2}$')
group_stopwatches = {}


def get_group_stopwatch(run_group_id):
    """Liefert die unabhängige Stoppuhr einer Laufgruppe."""
    if run_group_id not in group_stopwatches:
        group_stopwatches[run_group_id] = Stopwatch()
    return group_stopwatches[run_group_id]


def requested_group_id():
    data = request.get_json(silent=True) or {}
    value = data.get('run_group_id') or request.args.get('run_group_id')
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


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
    """Stopwatch für eine ausgewählte Laufgruppe starten."""
    data = request.get_json(silent=True) or {}
    try:
        run_group_id = int(data.get('run_group_id'))
        group = db.start_run_group(run_group_id)
    except (TypeError, ValueError) as error:
        return jsonify({'success': False, 'error': str(error) or 'Laufgruppe auswählen'}), 400
    stopwatch = get_group_stopwatch(run_group_id)
    stopwatch.start()
    result = stopwatch.get_status()
    result['run_group'] = group
    return jsonify(result)


@api_bp.route('/pause', methods=['POST'])
def api_pause():
    """Stopwatch pausieren."""
    run_group_id = requested_group_id()
    if run_group_id is None:
        return jsonify({'success': False, 'error': 'Laufgruppe erforderlich'}), 400
    stopwatch = get_group_stopwatch(run_group_id)
    stopwatch.pause()
    return jsonify(stopwatch.get_status())


@api_bp.route('/resume', methods=['POST'])
def api_resume():
    """Stopwatch fortsetzen."""
    run_group_id = requested_group_id()
    if run_group_id is None:
        return jsonify({'success': False, 'error': 'Laufgruppe erforderlich'}), 400
    stopwatch = get_group_stopwatch(run_group_id)
    stopwatch.resume()
    return jsonify(stopwatch.get_status())


@api_bp.route('/stop', methods=['POST'])
def api_stop():
    """Stopwatch stoppen."""
    run_group_id = requested_group_id()
    if run_group_id is None:
        return jsonify({'success': False, 'error': 'Laufgruppe erforderlich'}), 400
    stopwatch = get_group_stopwatch(run_group_id)
    group = db.get_run_group(run_group_id)
    stopwatch.stop()
    if group:
        db.end_run_group(group['id'])
    return jsonify(stopwatch.get_status())


@api_bp.route('/lap', methods=['POST'])
def api_lap():
    """Zwischenzeit (Lap) hinzufügen."""
    run_group_id = requested_group_id()
    if run_group_id is None:
        return jsonify({'success': False, 'error': 'Laufgruppe erforderlich'}), 400
    stopwatch = get_group_stopwatch(run_group_id)
    stopwatch.add_lap()
    return jsonify(stopwatch.get_status())


@api_bp.route('/status', methods=['GET'])
def api_status():
    """Status der Stopwatch abrufen."""
    run_group_id = requested_group_id()
    if run_group_id is None:
        return jsonify({'is_running': False, 'is_paused': False, 'elapsed_time': 0, 'formatted_time': '00:00:00.00'})
    stopwatch = get_group_stopwatch(run_group_id)
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

    number = str(data.get('number', '')).strip()
    run_group_id = data.get('run_group_id')
    if not number:
        return jsonify({'success': False, 'error': 'Nummer erforderlich'}), 400

    try:
        student = db.get_student_by_startnummer(number)
        if not student:
            return jsonify({'success': False, 'error': 'Startnummer nicht gefunden'}), 404

        if run_group_id is None:
            active_groups = db.get_active_run_groups_for_class(student['class_group'])
            if len(active_groups) != 1:
                return jsonify({'success': False, 'error': 'Für diese Startnummer gibt es keine eindeutig aktive Laufgruppe'}), 400
            run_group_id = active_groups[0]['id']

        group = db.get_run_group(int(run_group_id))
        if not group or not group.get('active'):
            return jsonify({'success': False, 'error': 'Keine aktive Laufgruppe ausgewählt'}), 400

        stopwatch = get_group_stopwatch(group['id'])
        if not stopwatch.is_running and not stopwatch.is_paused:
            return jsonify({'success': False, 'error': 'Die Stoppuhr dieser Laufgruppe läuft nicht'}), 400
        time_str = stopwatch.get_formatted_time()
        if not TIME_PATTERN.match(time_str):
            return jsonify({'success': False, 'error': 'Ungültiges Zeitformat'}), 400

        # Speichere Zeitmessung in Datenbank
        db.save_measurement(number, time_str, run_group_id=group['id'])
        student = next(
            (
                item for item in db.get_run_group_students(group['id'])
                if item['startnummer'] == int(number)
            ),
            None
        )
        return jsonify({
            'success': True,
            'time': time_str,
            'class_group': student['class_group'] if student else '',
            'number': student['startnummer'] if student else number,
            'run_group': group['name']
        })
    except ValueError as error:
        return jsonify({'success': False, 'error': str(error)}), 400
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
    """Aktive Laufgruppen abrufen."""
    try:
        return jsonify(db.get_run_groups(include_inactive=False))
    except Exception as e:
        return jsonify({'success': False, 'error': f'Datenbankfehler: {str(e)}'}), 500


@api_bp.route('/run_groups', methods=['GET'])
def api_run_groups():
    """Alle Laufgruppen für die Auswahl im Zeitmesser."""
    return jsonify(db.get_run_groups())


@api_bp.route('/run_groups/<int:run_group_id>/participants', methods=['GET'])
def api_run_group_participants(run_group_id):
    """Teilnehmerstatus einer Laufgruppe abrufen."""
    group = db.get_run_group(run_group_id)
    if not group:
        return jsonify({'success': False, 'error': 'Laufgruppe nicht gefunden'}), 404
    participants = db.get_run_group_students(run_group_id)
    return jsonify({
        'run_group': group,
        'participants': participants,
        'remaining': sum(item['still_running'] for item in participants),
        'finished': sum(not item['still_running'] for item in participants)
    })
