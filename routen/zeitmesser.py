from flask import Blueprint, render_template, jsonify
from routen.stopwatch import stopwatch

zeitmesser_bp = Blueprint('zeitmesser', __name__, url_prefix='/zeitmesser')
api_bp = Blueprint('api', __name__, url_prefix='/api/stopwatch')

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

@api_bp.route('/status', methods=['GET'])
def api_status():
    return jsonify(stopwatch.get_status())
