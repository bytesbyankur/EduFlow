from flask import Blueprint, request, jsonify
from db import get_db
from utils.auth import verify_token
from functools import wraps
import datetime

session_bp = Blueprint("session", __name__)

# In-memory session store
session_data = {}

# ================= AUTH DECORATOR =================
def auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return jsonify({"error": "Token missing"}), 401

        token = auth.split(" ", 1)[1]
        data = verify_token(token)

        if not data or "teacher_id" not in data:
            return jsonify({"error": "Invalid token"}), 401

        request.user = data
        return f(*args, **kwargs)
    return wrapper


# ================= GET CLASSES & SUBJECTS =================
@session_bp.route("/start_session", methods=["GET"])
@auth_required
def start_session():
    teacher_id = request.user["teacher_id"]

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            c.id AS class_id,
            c.class_name,
            s.id AS subject_id,
            s.subject_name
        FROM teacher_subjects ts
        JOIN subjects s ON ts.subject_id = s.id
        JOIN class_subjects cs ON cs.subject_id = s.id
        JOIN classes c ON cs.class_id = c.id
        WHERE ts.teacher_id = %s
    """, (teacher_id,))

    rows = cur.fetchall()
    cur.close()
    db.close()

    if not rows:
        return jsonify({"error": "No classes assigned"}), 400

    return jsonify(rows), 200


# ================= START CLASS SESSION =================
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

    # 🔐 Validate ownership
    cur.execute("""
        SELECT 1
        FROM teacher_subjects ts
        JOIN class_subjects cs ON cs.subject_id = ts.subject_id
        WHERE ts.teacher_id = %s
          AND ts.subject_id = %s
          AND cs.class_id = %s
    """, (teacher_id, subject_id, class_id))

    if not cur.fetchone():
        return jsonify({"error": "Unauthorized session"}), 403

    session_data[class_id] = {
        "teacher_id": teacher_id,
        "subject_id": subject_id,
        "students": {},
        "started_at": datetime.datetime.utcnow()
    }

    return jsonify({"status": "Session started"}), 200
