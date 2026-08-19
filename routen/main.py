from flask import Blueprint, render_template, redirect, url_for

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@main_bp.route('/user_interface')
def user_interface():
    """Redirect to stopwatch interface."""
    return redirect(url_for('zeitmesser.zeitmesser'))
