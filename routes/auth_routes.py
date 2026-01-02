from flask import Blueprint, jsonify
import cv2
import numpy as np
from db import get_db
from utils.face_utils import get_embedding, match_face
from utils.spoofing import blink_detect
from utils.auth import generate_token
from config import CAMERA_INDEX

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/teacher/login_face", methods=["POST"])
def teacher_login_face():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return jsonify({"error": "Camera error"}), 500

    frame = cv2.flip(frame, 1)

    if not blink_detect(frame):
        return jsonify({"error": "Blink not detected"}), 403

    emb = get_embedding(frame)
    if emb is None:
        return jsonify({"error": "Face not detected"}), 400

    cur.execute("""
        SELECT id, face_embedding
        FROM teachers
        WHERE face_embedding IS NOT NULL
    """)

    teachers = {
        row["id"]: np.frombuffer(row["face_embedding"], dtype=np.float64)
        for row in cur.fetchall()
    }

    teacher_id = match_face(emb, teachers)

    if not teacher_id:
        return jsonify({"error": "Teacher not recognized"}), 401

    token = generate_token({"teacher_id": teacher_id})

    cur.close()
    db.close()

    return jsonify({
        "token": token,
        "teacher_id": teacher_id
    }), 200

@auth_bp.route("/student/login_face", methods=["POST"])
def student_login_face():
    db = get_db()
    cur = db.cursor(dictionary=True)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return jsonify({"error": "Camera error"}), 500

    frame = cv2.flip(frame, 1)

    if not blink_detect(frame):
        return jsonify({"error": "Blink not detected"}), 403

    emb = get_embedding(frame)
    if emb is None:
        return jsonify({"error": "Face not detected"}), 400

    cur.execute("""
        SELECT id, regd_no, face_embedding
        FROM students
        WHERE face_embedding IS NOT NULL
    """)

    students = {
        row["id"]: np.frombuffer(row["face_embedding"], dtype=np.float64)
        for row in cur.fetchall()
    }

    student_id = match_face(emb, students)

    if not student_id:
        return jsonify({"error": "Student not recognized"}), 401

    token = generate_token({"student_id": student_id})

    cur.close()
    db.close()

    return jsonify({
        "token": token,
        "student_id": student_id
    }), 200
