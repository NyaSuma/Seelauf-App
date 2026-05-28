from flask import Flask
from routen.main import main_bp
from routen.zeitmesser import zeitmesser_bp, api_bp

app = Flask(__name__)

# Blueprint registrieren
app.register_blueprint(main_bp)
app.register_blueprint(zeitmesser_bp)
app.register_blueprint(api_bp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

