"""
Haupt-Navigation für Seelauf-App
Startseite und Umleitung zum Zeitmesser-Interface
"""
from flask import Blueprint, render_template, redirect, url_for

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Startseite der Anwendung.
    Zeigt die Hauptmenü-Seite mit verfügbaren Funktionen.
    """
    return render_template('index.html')


@main_bp.route('/user_interface')
def user_interface():
    """
    Umleitung zum Zeitmesser-Interface.
    (Entfernt zwischengeschaltete Menü-Seite)
    """
    return redirect(url_for('zeitmesser.zeitmesser'))


@main_bp.route('/laeufer')
def user_zeit():
    """
    Zeigt die Eigenzeit-Seite für Läufer an.
    """
    return render_template('user_zeit.html')