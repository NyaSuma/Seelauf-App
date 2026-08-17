import os
from flask import Flask
from dotenv import load_dotenv
from routen.main import main_bp
from routen.zeitmesser import zeitmesser_bp, api_bp
from routen.admin import admin_bp

# Load environment variables from .env file
load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DEBUG=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        HOST=os.getenv('FLASK_HOST', '0.0.0.0'),
        PORT=int(os.getenv('FLASK_PORT', 8000)),
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production'),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax'
    )

    if test_config:
        app.config.update(test_config)
        if 'DATABASE_PATH' in test_config:
            os.environ['DATABASE_PATH'] = test_config['DATABASE_PATH']

    os.makedirs(app.instance_path, exist_ok=True)
    app.register_blueprint(main_bp)
    app.register_blueprint(zeitmesser_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])