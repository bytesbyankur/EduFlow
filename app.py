from flask import Flask, send_from_directory
from flask_cors import CORS

from routes.auth_routes import auth_bp
from routes.session_routes import session_bp
from routes.attendance_routes import attendance_bp
from routes.admin_routes import admin_bp

app = Flask(__name__, static_folder="static")
CORS(app)

# Serve frontend
@app.route("/")
def home():
    return send_from_directory("static", "index.html")

# API routes (REAL backend)
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(session_bp, url_prefix="/api/session")
app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
app.register_blueprint(admin_bp, url_prefix="/api/admin")

if __name__ == "__main__":
    app.run(debug=True)
