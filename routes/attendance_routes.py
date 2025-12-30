from flask import Blueprint, request, jsonify
import cv2, datetime
import numpy as np
from functools import wraps

from db import get_db
from utils.face_utils import get_embedding, match_face
from utils.spoofing import blink_detect
from utils.auth import verify_token
from config import CAMERA_INDEX, PRESENCE_THRESHOLD, ATTENDANCE_SCAN_WINDOW
from routes.session_routes import session_data

attendance_bp = Blueprint("attendance", __name__)

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


@attendance_bp.route("/detect_faces", methods=["POST"])
@auth_required
def detect_faces():
    data = request.json
    if not data or "class_id" not in data:
        return jsonify({"error": "class_id required"}), 400

    class_id = data["class_id"]

    if class_id not in session_data:
        return jsonify({"error": "Session not started"}), 400

    if session_data[class_id]["teacher_id"] != request.user["teacher_id"]:
        return jsonify({"error": "Unauthorized session"}), 403

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT id, face_embedding
        FROM students
        WHERE class_id = %s
    """, (class_id,))

    students = {
        row[0]: np.frombuffer(row[1], dtype=np.float64)
        for row in cur.fetchall()
    }

    cap = cv2.VideoCapture(CAMERA_INDEX)
    start_time = datetime.datetime.now()

    while (datetime.datetime.now() - start_time).seconds < ATTENDANCE_SCAN_WINDOW:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)

        if not blink_detect(frame):
            continue

        emb = get_embedding(frame)
        student_id = match_face(emb, students)

        if student_id:
            session_data[class_id]["students"].setdefault(
                student_id, []
            ).append(datetime.datetime.now())

    cap.release()
    return jsonify({"status": "detection complete"})


@attendance_bp.route("/end_session", methods=["POST"])
@auth_required
def end_session():
    data = request.json
    if not data or "class_id" not in data:
        return jsonify({"error": "class_id required"}), 400

    class_id = data["class_id"]

    if class_id not in session_data:
        return jsonify({"error": "Session not found"}), 400

    if session_data[class_id]["teacher_id"] != request.user["teacher_id"]:
        return jsonify({"error": "Unauthorized session"}), 403

    subject_id = session_data[class_id]["subject_id"]
    teacher_id = session_data[class_id]["teacher_id"]
    today = datetime.date.today()

    db = get_db()
    cur = db.cursor()

    for student_id, timestamps in session_data[class_id]["students"].items():
        presence_score = len(timestamps) / ATTENDANCE_SCAN_WINDOW

        if presence_score >= PRESENCE_THRESHOLD:
            status = "PRESENT"
        elif presence_score > 0.3:
            status = "LATE"
        else:
            status = "ABSENT"

        cur.execute("""
            INSERT INTO attendance
            (student_id, subject_id, teacher_id, date, status, presence_score)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            status=VALUES(status),
            presence_score=VALUES(presence_score)
        """, (
            student_id, subject_id, teacher_id,
            today, status, presence_score
        ))

    db.commit()
    session_data.pop(class_id, None)

    return jsonify({"status": "attendance marked"})


@attendance_bp.route("/attendance_report", methods=["GET"])
@auth_required
def attendance_report():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT s.name, sub.subject_name, a.date, a.status, a.presence_score
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        JOIN subjects sub ON a.subject_id = sub.id
    """)

    return jsonify(cur.fetchall())
