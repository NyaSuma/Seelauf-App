import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import blueprints
from routen.main import main_bp
from routen.zeitmesser import zeitmesser_bp, api_bp
from routen.admin import admin_bp


def create_app(test_config=None):
    """Create and configure Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    
    # Configuration
    app.config.update(
        DEBUG=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        HOST=os.getenv('FLASK_HOST', '0.0.0.0'),
        PORT=int(os.getenv('FLASK_PORT', 8000)),
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax'
    )
    
    # Override with test config if provided
    if test_config:
        app.config.update(test_config)
        if 'DATABASE_PATH' in test_config:
            os.environ['DATABASE_PATH'] = test_config['DATABASE_PATH']
    
    # Ensure instance path exists
    Path(app.instance_path).mkdir(exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(zeitmesser_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    
    return app


# Create app instance
app = create_app()


if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )