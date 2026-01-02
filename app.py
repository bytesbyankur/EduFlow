from flask import Flask
from flask_cors import CORS

from routes.auth_routes import auth_bp
from routes.session_routes import session_bp
from routes.attendance_routes import attendance_bp
from routes.admin_routes import admin_bp
from routes.otp_routes import otp_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(session_bp, url_prefix="/api/session")
app.register_blueprint(attendance_bp, url_prefix="/api/attendance")
app.register_blueprint(admin_bp, url_prefix = "/api/admin")
app.register_blueprint(otp_bp, url_prefix="/api/otp")

if __name__ == "__main__":
    app.run(debug=True)
