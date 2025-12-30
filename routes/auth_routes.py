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
@auth_bp.route("/teacher/register", methods=["POST"])
def teacher_register():
    data = request.json

    if not data or "email" not in data or "password" not in data or "teacher_id" not in data:
        return jsonify({"error": "email, password, teacher_id required"}), 400

    db = get_db()
    cur = db.cursor()

    # 🔍 Verify teacher exists
    cur.execute("SELECT id FROM teachers WHERE id = %s", (data["teacher_id"],))
    if not cur.fetchone():
        return jsonify({"error": "Invalid teacher_id"}), 400

    # 🔍 Email already registered?
    cur.execute("SELECT id FROM teacher_auth WHERE email = %s", (data["email"],))
    if cur.fetchone():
        return jsonify({"error": "Email already registered"}), 409

    password_hash = generate_password_hash(data["password"])

    cur.execute("""
        INSERT INTO teacher_auth (teacher_id, email, password_hash)
        VALUES (%s, %s, %s)
    """, (
        data["teacher_id"],
        data["email"],
        password_hash
    ))

    db.commit()
    cur.close()
    db.close()

    return jsonify({"status": "Teacher registered successfully"}), 201


@auth_bp.route("/student/register", methods=["POST"])
def student_register():
    data = request.json

    if not data or "email" not in data or "password" not in data or "student_id" not in data:
        return jsonify({"error": "email, password, student_id required"}), 400

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT id FROM students WHERE id = %s", (data["student_id"],))
    if not cur.fetchone():
        return jsonify({"error": "Invalid student_id"}), 400

    # Email verification (already exists?)
    cur.execute("SELECT id FROM student_auth WHERE email = %s", (data["email"],))
    if cur.fetchone():
        return jsonify({"error": "Email already registered"}), 409

    password_hash = generate_password_hash(data["password"])

    cur.execute("""
        INSERT INTO student_auth (student_id, email, password_hash)
        VALUES (%s, %s, %s)
    """, (
        data["student_id"],
        data["email"],
        password_hash
    ))

    db.commit()

    return jsonify({"status": "Student registered successfully"}), 201

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
