from flask import Blueprint, request, jsonify
from db import get_db
from utils.auth import verify_token
from functools import wraps
import datetime

session_bp = Blueprint("session", __name__)

session_data = {}

def auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if not auth:
            return jsonify({"error": "Token missing"}), 401

        token = auth.replace("Bearer ", "")
        data = verify_token(token)
        if not data:
            return jsonify({"error": "Invalid token"}), 401

        request.user = data
        return f(*args, **kwargs)
    return wrapper



# ---------------- START SESSION ----------------
@session_bp.route("/start_session", methods=["POST"])
@auth_required
def start_session():
    teacher_id = request.user["teacher_id"]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT c.id, s.id
        FROM classes c
        JOIN subjects s ON c.subject_id = s.id
        WHERE s.teacher_id = %s
    """, (teacher_id,))

    rows = cur.fetchall()

    if not rows:
        return jsonify({"error": "No class found for teacher"}), 400

    return jsonify({
        "classes": [
            {
                "class_id": r[0],
                "subject_id": r[1]
            } for r in rows
        ]
    })

#-----------------START CASS SESSIOIN ----------------
@session_bp.route("/start_class_session", methods=["POST"])
@auth_required
def start_class_session():
    data = request.json
    if not data or "class_id" not in data or "subject_id" not in data:
        return jsonify({"error": "class_id and subject_id required"}), 400

    class_id = int(data["class_id"])
    subject_id = int(data["subject_id"])
    teacher_id = request.user["teacher_id"]

    if class_id in session_data:
        return jsonify({"error": "Session already active"}), 400

    db = get_db()
    cur = db.cursor()

    # 🔐 Ownership validation
    cur.execute("""
        SELECT 1
        FROM classes c
        JOIN subjects s ON c.subject_id = s.id
        WHERE c.id = %s AND s.id = %s AND s.teacher_id = %s
    """, (class_id, subject_id, teacher_id))

    if not cur.fetchone():
        return jsonify({"error": "Unauthorized class access"}), 403

    session_data[class_id] = {
        "teacher_id": teacher_id,
        "subject_id": subject_id,
        "students": {},
        "started_at": datetime.datetime.utcnow()
    }

    return jsonify({"status": "session started"})
