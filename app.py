# app.py - Main Application
from flask import Flask
from flask_cors import CORS
from config import Config
from models import db
from routes import auth_bp, cases_bp, debtors_bp, debtor_portal_bp

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
CORS(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(cases_bp)
app.register_blueprint(debtors_bp)
app.register_blueprint(debtor_portal_bp)

@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
