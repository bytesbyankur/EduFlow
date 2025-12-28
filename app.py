from flask import Flask, request, jsonify
import cv2, datetime, numpy as np
from db import get_db
from utils.face_utils import get_embedding, match_face
from utils.spoofing import blink_detect
from config import PRESENCE_THRESHOLD, CAMERA_INDEX
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# session_data[class_id] = {
#   "subject_id": x,
#   "teacher_id": y,
#   "students": { student_id: [timestamps] }
# }
session_data = {}

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    db = get_db()
    cur = db.cursor()

    cur.execute(
        "SELECT id, password FROM teachers WHERE username=%s",
        (data["username"],)
    )
    row = cur.fetchone()

    if row and row[1] == data["password"]:
        return jsonify({"teacher_id": row[0]})

    return jsonify({"error": "Invalid credentials"}), 401


# ---------------- START SESSION ----------------
@app.route("/start_session", methods=["POST"])
def start_session():
    teacher_id = request.json["teacher_id"]

    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT c.id, s.id
        FROM classes c
        JOIN subjects s ON c.subject_id = s.id
        WHERE s.teacher_id = %s
    """, (teacher_id,))

    row = cur.fetchone()
    if not row:
        return jsonify({"error": "No class found for teacher"}), 400

    class_id, subject_id = row

    session_data[class_id] = {
        "teacher_id": teacher_id,
        "subject_id": subject_id,
        "students": {}
    }

    return jsonify({
        "class_id": class_id,
        "subject_id": subject_id,
        "status": "session started"
    })

# ---------------- FACE DETECTION ----------------
@app.route("/detect_faces", methods=["POST"])
def detect_faces():
    class_id = request.json["class_id"]

    if class_id not in session_data:
        return jsonify({"error": "Session not started"}), 400

    db = get_db()
    cur = db.cursor()

    # ✅ Load ONLY students of this class
    cur.execute("""
        SELECT id, face_embedding
        FROM students
        WHERE class_id = %s
    """, (class_id,))

    students = {row[0]: row[1] for row in cur.fetchall()}

    cap = cv2.VideoCapture(CAMERA_INDEX)
    start_time = datetime.datetime.now()

    while (datetime.datetime.now() - start_time).seconds < 30:
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




# ---------------- END SESSION ----------------
@app.route("/end_session", methods=["POST"])
def end_session():
    class_id = request.json["class_id"]

    if class_id not in session_data:
        return jsonify({"error": "Session not found"}), 400

    subject_id = session_data[class_id]["subject_id"]
    teacher_id = session_data[class_id]["teacher_id"]
    today = datetime.date.today()

    db = get_db()
    cur = db.cursor()

    for student_id, timestamps in session_data[class_id]["students"].items():
        presence_score = len(timestamps) / 30

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


# ---------------- REPORT ----------------
@app.route("/attendance_report", methods=["GET"])
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


if __name__ == "__main__":
    app.run(debug=True)
