from flask import Blueprint, request, jsonify
import cv2
import numpy as np
from werkzeug.security import check_password_hash
from db import get_db
from utils.face_utils import get_embedding, match_face
from utils.spoofing import blink_detect
from utils.auth import generate_token
from config import CAMERA_INDEX
from werkzeug.security import generate_password_hash

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/teacher/login", methods=["POST"])
def teacher_login():
    data = request.json

    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password required"}), 400

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT t.id, t.name, ta.password_hash
        FROM teacher_auth ta
        JOIN teachers t ON ta.teacher_id = t.id
        WHERE ta.email = %s
    """, (data["email"],))

    row = cur.fetchone()

    if not row:
        return jsonify({"error": "Email not registered"}), 404

    if not check_password_hash(row[2], data["password"]):
        return jsonify({"error": "Incorrect password"}), 401
    
    if not row["is_verified"]:
        return jsonify({"error": "Email not verified"}), 403


    token = generate_token({"teacher_id": row[0]})

    cur.close()
    db.close()

    return jsonify({
        "token": token,
        "teacher_id": row[0],
        "name": row[1]
    }), 200


@auth_bp.route("/student/login", methods=["POST"])
def student_login():
    data = request.json
    db = get_db()
    cur = db.cursor()
    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password required"}), 400


    cur.execute("""
        SELECT s.id, s.regd_no, s.name, sa.password_hash
        FROM student_auth sa
        JOIN students s ON sa.student_id = s.id
        WHERE sa.email = %s
    """, (data["email"],))

    row = cur.fetchone()

    if not row:
        return jsonify({"error": "Email not registered"}), 404

    if not check_password_hash(row[3], data["password"]):
        return jsonify({"error": "Incorrect password"}), 401


    token = generate_token({
        "student_id": row[0],
        "regd_no": row[1]
    })

    return jsonify({
        "token": token,
        "regd_no": row[1],
        "name": row[2]
    })

@auth_bp.route("/teacher/login_face", methods=["POST"])
def teacher_login_face():
    db = get_db()
    cur = db.cursor()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return jsonify({"error": "Camera error"}), 500

    frame = cv2.flip(frame, 1)

    if not blink_detect(frame):
        return jsonify({"error": "Blink not detected"}), 403

    emb = get_embedding(frame)

    cur.execute("SELECT id, face_embedding FROM teachers")
    teachers = {
        row[0]: np.frombuffer(row[1], dtype=np.float64)
        for row in cur.fetchall()
    }

    teacher_id = match_face(emb, teachers)

    if not teacher_id:
        return jsonify({"error": "Teacher not recognized"}), 401

    token = generate_token({"teacher_id": teacher_id})

    return jsonify({
        "token": token,
        "teacher_id": teacher_id
    })
