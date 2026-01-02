from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
from db import get_db
import datetime

otp_bp = Blueprint("otp", __name__)

@otp_bp.route("/verify_otp", methods=["POST"])
def verify_otp():
    data = request.json
    required = ["email", "otp", "role"]

    if not data or not all(k in data for k in required):
        return jsonify({"error": "email, otp, role required"}), 400

    email = data["email"]
    otp = data["otp"]
    role = data["role"]

    if role not in ("student", "teacher"):
        return jsonify({"error": "Invalid role"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)

    # Fetch latest OTP
    cur.execute("""
        SELECT * FROM email_otp
        WHERE email = %s AND purpose = 'REGISTER'
        ORDER BY created_at DESC
        LIMIT 1
    """, (email,))
    record = cur.fetchone()

    if not record:
        return jsonify({"error": "OTP not found"}), 404

    if record["verified"]:
        return jsonify({"error": "OTP already used"}), 400

    if datetime.datetime.utcnow() > record["expires_at"]:
        return jsonify({"error": "OTP expired"}), 400

    if record["attempts"] >= 5:
        return jsonify({"error": "Too many attempts"}), 403

    if not check_password_hash(record["otp_hash"], otp):
        cur.execute(
            "UPDATE email_otp SET attempts = attempts + 1 WHERE id = %s",
            (record["id"],)
        )
        db.commit()
        return jsonify({"error": "Invalid OTP"}), 401

    # OTP success
    table = "student_auth" if role == "student" else "teacher_auth"

    # Verify account exists
    cur.execute(f"SELECT id FROM {table} WHERE email = %s", (email,))
    if not cur.fetchone():
        return jsonify({"error": "Account not found"}), 404

    # Mark OTP + account verified
    cur.execute("UPDATE email_otp SET verified = 1 WHERE id = %s", (record["id"],))
    cur.execute(
        f"UPDATE {table} SET is_verified = 1 WHERE email = %s",
        (email,)
    )

    db.commit()
    cur.close()
    db.close()

    return jsonify({"status": "Email verified successfully"}), 200
