from flask import Blueprint, request, jsonify, g
from werkzeug.security import check_password_hash
from functools import wraps
from db import get_db
from utils.auth import generate_token, verify_token
import cv2
import numpy as np
import time
from utils.face_utils import get_embedding
from utils.spoofing import blink_detect
from config import CAMERA_INDEX

# --------- LOGGER ----------
from logger import setup_logger
logger = setup_logger()
# --------------------------

# --------- RATE LIMITER ----------
from ratelimit import rate_limit
# -------------------------------

admin_bp = Blueprint("admin", __name__)

# ================= FACE CAPTURE =================
def capture_face_embedding():
    cap = None
    try:
        cap = cv2.VideoCapture(CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        embeddings = []
        blink_detected = False
        start_time = time.time()

        while time.time() - start_time < 10:
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

        if not blink_detected:
            logger.warning("Blink not detected during face capture")
            return None, "Blink not detected"

        if len(embeddings) < 5:
            logger.warning("Insufficient face samples captured")
            return None, "Insufficient face samples"

        return np.mean(embeddings, axis=0), None

    except Exception:
        logger.critical("Face embedding capture crashed", exc_info=True)
        return None, "Face capture failed"

    finally:
        if cap:
            cap.release()


# ================= ADMIN DECORATOR =================
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            auth = request.headers.get("Authorization")
            if not auth:
                logger.warning("Admin token missing")
                return jsonify({"error": "Token missing"}), 401

            if not auth.startswith("Bearer "):
                logger.warning("Malformed Authorization header")
                return jsonify({"error": "Invalid token format"}), 401

            token = auth.split(" ", 1)[1]

            data = verify_token(token)

            if not data or data.get("role") != "admin":
                logger.warning("Unauthorized admin access attempt")
                return jsonify({"error": "Admin access required"}), 403

            g.admin = data
            return f(*args, **kwargs)

        except Exception:
            logger.critical("Admin auth middleware crashed", exc_info=True)
            return jsonify({"error": "Authorization error"}), 500

    return wrapper


# ================= ADMIN LOGIN =================
@admin_bp.route("/login", methods=["POST"])
@rate_limit(5, 60)
def admin_login():
    db = None
    cur = None
    try:
        data = request.json
        if not data or "email" not in data or "password" not in data:
            logger.warning("Admin login missing credentials")
            return jsonify({"error": "Email and password required"}), 400

        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("""
            SELECT id, password_hash
            FROM admins
            WHERE email = %s
        """, (data["email"],))

        row = cur.fetchone()

        if not row or not check_password_hash(row["password_hash"], data["password"]):
            logger.warning(f"Admin login failed: {data['email']}")
            return jsonify({"error": "Invalid credentials"}), 401

        token = generate_token({
            "admin_id": row["id"],
            "role": "admin"
        })

        logger.info(f"Admin logged in: {data['email']}")
        return jsonify({"token": token}), 200

    except Exception:
        logger.error("Admin login crashed", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        if cur:
            cur.close()
        if db:
            db.close()

#================ CREATE STUDENT LOGIN =================
@admin_bp.route("/create_student_login", methods=["POST"])
@rate_limit(10, 60)
@admin_required
def create_student_login():
    data = request.json
    required = ["student_id", "email", "password"]

    if not data or not all(k in data for k in required):
        return jsonify({"error": "student_id, email, password required"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT id FROM students WHERE id = %s", (data["student_id"],))
    if not cur.fetchone():
        return jsonify({"error": "Invalid student_id"}), 400

    cur.execute("SELECT id FROM student_auth WHERE email = %s", (data["email"],))
    if cur.fetchone():
        return jsonify({"error": "Email already exists"}), 409

    from werkzeug.security import generate_password_hash
    password_hash = generate_password_hash(data["password"])

    cur.execute("""
        INSERT INTO student_auth (student_id, email, password_hash, is_verified)
        VALUES (%s, %s, %s, 1)
    """, (data["student_id"], data["email"], password_hash))

    db.commit()
    cur.close()
    db.close()

    return jsonify({"status": "Student login created"}), 201


#================ CREATE TEACHER LOGIN =================
@admin_bp.route("/create_teacher_login", methods=["POST"])
@rate_limit(10, 60)
@admin_required
def create_teacher_login():
    data = request.json
    required = ["teacher_id", "email", "password"]

    if not data or not all(k in data for k in required):
        return jsonify({"error": "teacher_id, email, password required"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT id FROM teachers WHERE id = %s", (data["teacher_id"],))
    if not cur.fetchone():
        return jsonify({"error": "Invalid teacher_id"}), 400

    cur.execute("SELECT id FROM teacher_auth WHERE email = %s", (data["email"],))
    if cur.fetchone():
        return jsonify({"error": "Email already exists"}), 409

    from werkzeug.security import generate_password_hash
    password_hash = generate_password_hash(data["password"])

    cur.execute("""
        INSERT INTO teacher_auth (teacher_id, email, password_hash, is_verified)
        VALUES (%s, %s, %s, 1)
    """, (data["teacher_id"], data["email"], password_hash))

    db.commit()
    cur.close()
    db.close()

    return jsonify({"status": "Teacher login created"}), 201

# ================= ENROLL STUDENT FACE =================

@admin_bp.route("/enroll_student_face", methods=["POST"])
@rate_limit(5, 60)
@admin_required
def enroll_student_face():
    db = None
    cur = None
    try:
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
        logger.info(f"Student face enrolled: {data['student_id']}")

        return jsonify({"status": "Student face enrolled"}), 200

    except Exception:
        logger.error("Student face enrollment failed", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        if cur:
            cur.close()
        if db:
            db.close()


# ================= ENROLL TEACHER FACE =================
@admin_bp.route("/enroll_teacher_face", methods=["POST"])
@rate_limit(5, 60)
@admin_required
def enroll_teacher_face():
    db = None
    cur = None
    try:
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
        logger.info(f"Teacher face enrolled: {data['teacher_id']}")

        return jsonify({"status": "Teacher face enrolled"}), 200

    except Exception:
        logger.error("Teacher face enrollment failed", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        if cur:
            cur.close()
        if db:
            db.close()


# ================= CREATE TEACHER =================
@admin_bp.route("/create_teacher", methods=["POST"])
@rate_limit(20, 60)
@admin_required
def create_teacher():
    db = None
    cur = None
    try:
        data = request.json
        if not data or "name" not in data:
            return jsonify({"error": "Teacher name required"}), 400

        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("SELECT id FROM teachers WHERE name = %s", (data["name"],))
        if cur.fetchone():
            return jsonify({"error": "Teacher already exists"}), 409

        cur.execute("INSERT INTO teachers (name) VALUES (%s)", (data["name"],))
        db.commit()

        logger.info(f"Teacher created: {cur.lastrowid}")
        return jsonify({"status": "Teacher created", "teacher_id": cur.lastrowid}), 201

    except Exception:
        logger.error("Create teacher failed", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        if cur:
            cur.close()
        if db:
            db.close()


# ================= CREATE STUDENT =================
@admin_bp.route("/create_student", methods=["POST"])
@rate_limit(20, 60)
@admin_required
def create_student():
    db = None
    cur = None
    try:
        data = request.json
        required = ["name", "regd_no", "class_id"]

        if not data or not all(k in data for k in required):
            return jsonify({"error": "name, regd_no, class_id required"}), 400

        db = get_db()
        cur = db.cursor(dictionary=True)

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
        logger.info(f"Student created: {cur.lastrowid}")
        return jsonify({"status": "Student created", "student_id": cur.lastrowid}), 201

    except Exception:
        logger.error("Create student failed", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        if cur:
            cur.close()
        if db:
            db.close()


# ================= CREATE CLASS =================
@admin_bp.route("/create_class", methods=["POST"])
@rate_limit(15, 60)
@admin_required
def create_class():
    db = None
    cur = None
    try:
        data = request.json
        required = ["class_name", "semester", "department"]

        if not data or not all(k in data for k in required):
            return jsonify({"error": "class_name, semester, department required"}), 400

        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("""
            INSERT INTO classes (class_name, semester, department)
            VALUES (%s, %s, %s)
        """, (data["class_name"], data["semester"], data["department"]))

        db.commit()
        logger.info(f"Class created: {cur.lastrowid}")
        return jsonify({"status": "Class created", "class_id": cur.lastrowid}), 201

    except Exception:
        logger.error("Create class failed", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        if cur:
            cur.close()
        if db:
            db.close()


# ================= CREATE SUBJECT =================
@admin_bp.route("/create_subject", methods=["POST"])
@rate_limit(15, 60)
@admin_required
def create_subject():
    db = None
    cur = None
    try:
        data = request.json
        required = ["subject_name", "semester", "department"]

        if not data or not all(k in data for k in required):
            return jsonify({"error": "subject_name, semester, department required"}), 400

        db = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute("""
            INSERT INTO subjects (subject_name, semester, department)
            VALUES (%s, %s, %s)
        """, (data["subject_name"], data["semester"], data["department"]))

        db.commit()
        logger.info(f"Subject created: {cur.lastrowid}")
        return jsonify({"status": "Subject created", "subject_id": cur.lastrowid}), 201

    except Exception:
        logger.error("Create subject failed", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

    finally:
        if cur:
            cur.close()
        if db:
            db.close()


#=========ASSIGN SUBJECT TO TEACHER======
@admin_bp.route("/assign_subject_teacher", methods=["POST"])
@rate_limit(10, 60)
@admin_required
def assign_subject_teacher():
    data = request.json
    if not data or "teacher_id" not in data or "subject_id" not in data:
        return jsonify({"error": "teacher_id and subject_id required"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("SELECT id FROM teachers WHERE id = %s", (data["teacher_id"],))
    if not cur.fetchone():
        return jsonify({"error": "Invalid teacher_id"}), 400

    cur.execute("SELECT id FROM subjects WHERE id = %s", (data["subject_id"],))
    if not cur.fetchone():
        return jsonify({"error": "Invalid subject_id"}), 400

    cur.execute("""
        INSERT IGNORE INTO teacher_subjects (teacher_id, subject_id)
        VALUES (%s, %s)
    """, (data["teacher_id"], data["subject_id"]))

    db.commit()
    cur.close()
    db.close()

    return jsonify({"status": "Subject assigned to teacher"}), 200

#===========ASSSIGN SUBJECT TO TEACHER =========
@admin_bp.route("/assign_subject_class", methods=["POST"])
@rate_limit(10, 60)
@admin_required
def assign_subject_class():
    data = request.json
    if not data or "class_id" not in data or "subject_id" not in data:
        return jsonify({"error": "class_id and subject_id required"}), 400

    db = get_db()
    cur = db.cursor(dictionary=True)

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


#======== TEACHER OVERVIEW=======
@admin_bp.route("/teacher_overview/<int:teacher_id>", methods=["GET"])
@admin_required
def teacher_overview(teacher_id):
    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT 
            t.id AS teacher_id,
            t.name AS teacher_name,
            s.id AS subject_id,
            s.subject_name,
            c.id AS class_id,
            c.class_name
        FROM teacher_subjects ts
        JOIN teachers t ON ts.teacher_id = t.id
        JOIN subjects s ON ts.subject_id = s.id
        JOIN class_subjects cs ON cs.subject_id = s.id
        JOIN classes c ON cs.class_id = c.id
        WHERE t.id = %s
    """, (teacher_id,))

    rows = cur.fetchall()
    cur.close()
    db.close()

    return jsonify(rows), 200
