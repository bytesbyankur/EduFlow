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


# ================= CREATE TEACHER =================
@admin_bp.route("/create_teacher", methods=["POST"])
@admin_required
@rate_limit(20, 60)
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