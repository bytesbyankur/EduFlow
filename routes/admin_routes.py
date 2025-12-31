from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from db import get_db
from utils.auth import generate_token, verify_token
import cv2
import numpy as np
import time
from utils.face_utils import get_embedding
from utils.spoofing import blink_detect
from config import CAMERA_INDEX    

admin_bp = Blueprint("admin", __name__)

def capture_face_embedding():
    cap = cv2.VideoCapture(CAMERA_INDEX)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    embeddings = []
    blink_detected = False
    start_time = time.time()

    while time.time() - start_time < 10:  # 10 seconds window
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)

        if blink_detect(frame):
            blink_detected = True

        emb = get_embedding(frame)
        if emb is not None:
            embeddings.append(emb)

        if len(embeddings) >= 5 and blink_detected:
            break

    cap.release()

    if not blink_detected:
        return None, "Blink not detected"

    if len(embeddings) < 5:
        return None, "Insufficient face samples"

    avg_embedding = np.mean(embeddings, axis=0)
    return avg_embedding, None


#---------------- ADMIN-ONLY DECORATOR ----------------
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if not auth:
            return jsonify({"error": "Token missing"}), 401

        token = auth.replace("Bearer ", "")
        data = verify_token(token)
        if not data or data.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403

        request.admin = data
        return f(*args, **kwargs)
    return wrapper


#---------------- ADMIN LOGIN API ----------------
@admin_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.json
    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Email and password required"}), 400

    db = get_db()
    cur = db.cursor(dictionary = True)

    cur.execute("""
        SELECT id, password_hash
        FROM admins
        WHERE email = %s
    """, (data["email"],))

    row = cur.fetchone()

    if not row or not check_password_hash(row["password_hash"], data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_token({
    "admin_id": row["id"],
    "role": "admin"
    })


    cur.close()
    db.close()

    return jsonify({"token": token}), 200


#---------------- CORE ADMIN APIs ----------------
@admin_bp.route("/create_teacher", methods=["POST"])
@admin_required
def create_teacher():
    data = request.json
    if not data or "name" not in data:
        return jsonify({"error": "Teacher name required"}), 400

    db = get_db()
    cur = db.cursor(dictionary = True)
    cur.execute("SELECT id FROM teachers WHERE name = %s", (data["name"],))
    if cur.fetchone():
        return jsonify({"error": "Teacher already exists"}), 409

    cur.execute("""
        INSERT INTO teachers (name)
        VALUES (%s)
    """, (data["name"],))

    db.commit()
    teacher_id = cur.lastrowid

    cur.close()
    db.close()

    return jsonify({
        "status": "Teacher created",
        "teacher_id": teacher_id
    }), 201

#---------------- CREATE STUDENT ----------------
@admin_bp.route("/create_student", methods=["POST"])
@admin_required
def create_student():
    data = request.json
    required = ["name", "regd_no", "class_id"]

    if not data or not all(k in data for k in required):
        return jsonify({"error": "name, regd_no, class_id required"}), 400

    db = get_db()
    cur = db.cursor(dictionary = True)
    cur.execute("SELECT id FROM classes WHERE id = %s", (data["class_id"],))
    if not cur.fetchone():
        return jsonify({"error": "Invalid class_id"}), 400

    cur.execute("SELECT id FROM students WHERE regd_no = %s", (data["regd_no"],))
    if cur.fetchone():
        return jsonify({"error": "Student already exists"}), 409

    cur.execute("""
        INSERT INTO students (name, regd_no, class_id)
        VALUES (%s, %s, %s)
    """, (data["name"], data["regd_no"], data["class_id"]))

    db.commit()
    student_id = cur.lastrowid

    cur.close()
    db.close()

    return jsonify({
        "status": "Student created",
        "student_id": student_id
    }), 201

#---------------- CREATE CLASS ----------------
@admin_bp.route("/create_class", methods=["POST"])
@admin_required
def create_class():
    data = request.json
    required = ["class_name", "semester", "department"]

    if not data or not all(k in data for k in required):
        return jsonify({"error": "class_name, semester, department required"}), 400

    db = get_db()
    cur = db.cursor(dictionary = True)

    cur.execute("""
        INSERT INTO classes (class_name, semester, department)
        VALUES (%s, %s, %s)
    """, (data["class_name"], data["semester"], data["department"]))

    db.commit()
    class_id = cur.lastrowid

    cur.close()
    db.close()

    return jsonify({
        "status": "Class created",
        "class_id": class_id
    }), 201

#---------------- CREATE SUBJECT ----------------
@admin_bp.route("/create_subject", methods=["POST"])
@admin_required
def create_subject():
    data = request.json
    required = ["subject_name", "semester", "department"]

    if not data or not all(k in data for k in required):
        return jsonify({"error": "subject_name, semester, department required"}), 400

    db = get_db()
    cur = db.cursor(dictionary = True)

    cur.execute("""
        INSERT INTO subjects (subject_name, semester, department)
        VALUES (%s, %s, %s)
    """, (data["subject_name"], data["semester"], data["department"]))

    db.commit()
    subject_id = cur.lastrowid

    cur.close()
    db.close()

    return jsonify({
        "status": "Subject created",
        "subject_id": subject_id
    }), 201

#---------------- ASSIGN SUBJECT TO TEACHER ----------------
@admin_bp.route("/assign_subject_teacher", methods=["POST"])
@admin_required
def assign_subject_teacher():
    data = request.json
    if not data or "teacher_id" not in data or "subject_id" not in data:
        return jsonify({"error": "teacher_id and subject_id required"}), 400

    db = get_db()
    cur = db.cursor(dictionary = True)
    cur.execute("SELECT id FROM teachers WHERE id = %s", (data["teacher_id"],))
    if not cur.fetchone():
        return jsonify({"error": "Invalid teacher_id"}), 400

    cur.execute("SELECT id FROM subjects WHERE id = %s", (data["subject_id"],))
    if not cur.fetchone():
        return jsonify({"error": "Invalid subject_id"}), 400

    cur.execute("""
        INSERT IGNORE INTO teacher_subjects (teacher_id, subject_id, face_embedding)
        VALUES (%s, %s, X'00')
    """, (data["teacher_id"], data["subject_id"]))

    db.commit()
    cur.close()
    db.close()

    return jsonify({"status": "Subject assigned to teacher"}), 200

#---------------- ASSIGN SUBJECT TO CLASS ----------------
@admin_bp.route("/assign_subject_class", methods=["POST"])
@admin_required
def assign_subject_class():
    data = request.json
    if not data or "class_id" not in data or "subject_id" not in data:
        return jsonify({"error": "class_id and subject_id required"}), 400

    db = get_db()
    cur = db.cursor(dictionary = True)
    cur.execute("SELECT id FROM classes WHERE id = %s", (data["class_id"],))
    
    if not cur.fetchone():
        return jsonify({"error": "Invalid class_id"}), 400

    cur.execute("SELECT id FROM subjects WHERE id = %s", (data["subject_id"],))
    if not cur.fetchone():
        return jsonify({"error": "Invalid subject_id"}), 400


    cur.execute("""
        INSERT IGNORE INTO class_subjects (class_id, subject_id)
        VALUES (%s, %s)
    """, (data["class_id"], data["subject_id"]))

    db.commit()
    cur.close()
    db.close()

    return jsonify({"status": "Subject assigned to class"}), 200


#---------------- SET TEACHER FACE EMBEDDING ----------------
@admin_bp.route("/enroll_teacher_face", methods=["POST"])
@admin_required
def enroll_teacher_face():
    data = request.json
    if not data or "teacher_id" not in data:
        return jsonify({"error": "teacher_id required"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT id FROM teachers WHERE id = %s", (data["teacher_id"],))
    if not cur.fetchone():
        return jsonify({"error": "Invalid teacher_id"}), 400

    embedding, error = capture_face_embedding()
    if error:
        return jsonify({"error": error}), 400

    cur.execute("""
        UPDATE teachers
        SET face_embedding = %s
        WHERE id = %s
    """, (embedding.tobytes(), data["teacher_id"]))

    db.commit()
    cur.close()
    db.close()

    return jsonify({"status": "Teacher face enrolled successfully"}), 200


#---------------- SET STUDENT FACE EMBEDDING ----------------
@admin_bp.route("/enroll_student_face", methods=["POST"])
@admin_required
def enroll_student_face():
    data = request.json
    if not data or "student_id" not in data:
        return jsonify({"error": "student_id required"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT id FROM students WHERE id = %s", (data["student_id"],))
    if not cur.fetchone():
        return jsonify({"error": "Invalid student_id"}), 400

    embedding, error = capture_face_embedding()
    if error:
        return jsonify({"error": error}), 400

    cur.execute("""
        UPDATE students
        SET face_embedding = %s
        WHERE id = %s
    """, (embedding.tobytes(), data["student_id"]))

    db.commit()
    cur.close()
    db.close()

    return jsonify({"status": "Student face enrolled successfully"}), 200
