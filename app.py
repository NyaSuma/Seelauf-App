import os
from flask import Flask
from dotenv import load_dotenv
from routen.main import main_bp
from routen.zeitmesser import zeitmesser_bp, api_bp
from routen.admin import admin_bp

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables with defaults
app.config.update(
    DEBUG=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
    HOST=os.getenv('FLASK_HOST', '0.0.0.0'),
    PORT=int(os.getenv('FLASK_PORT', 8000)),
    SECRET_KEY=os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
)

# Blueprint registrieren
app.register_blueprint(main_bp)
app.register_blueprint(zeitmesser_bp)
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp)

if __name__ == "__main__":
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])