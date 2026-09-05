"""
Haupt-Anwendung für Seelauf-App (Zeitmessungsverwaltung)
"""
import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv

# Umgebungsvariablen laden
load_dotenv()

# Blueprints (Module) importieren
from routen.main import main_bp
from routen.zeitmesser import zeitmesser_bp, api_bp
from routen.admin import admin_bp



def create_app(test_config=None):
    """
    Flask-Anwendung erstellen und konfigurieren.
    
    Args:
        test_config: Optionale Test-Konfiguration
    
    Returns:
        Konfigurierte Flask-App
    """
    app = Flask(__name__, instance_relative_config=True)
    
    # Anwendungs-Konfiguration laden
    app.config.update(
        DEBUG=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        HOST=os.getenv('FLASK_HOST', '0.0.0.0'),
        PORT=int(os.getenv('FLASK_PORT', 8000)),
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        TEMPLATES_AUTO_RELOAD=True
    )
       
    # Test-Konfiguration überschreiben (falls vorhanden)
    if test_config:
        app.config.update(test_config)
        if 'DATABASE_PATH' in test_config:
            os.environ['DATABASE_PATH'] = test_config['DATABASE_PATH']
    
    # Instanz-Verzeichnis erstellen
    Path(app.instance_path).mkdir(exist_ok=True)
    
    # Route-Module registrieren
    app.register_blueprint(main_bp)
    app.register_blueprint(zeitmesser_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    
    return app


# App-Instanz erstellen
app = create_app()


if __name__ == '__main__':
    # Anwendung starten
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )