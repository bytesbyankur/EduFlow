import cv2
import time
import numpy as np
from utils.face_utils import get_embedding, match_face
from utils.spoofing import blink_detect
from db import get_db
from config import CAMERA_INDEX


def capture_teacher_face():
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        print("❌ Camera not accessible")
        return None

    print("✅ Camera opened")

    db = get_db()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT id, face_embedding
        FROM teachers
        WHERE face_embedding IS NOT NULL
    """)

    teachers = {
        row["id"]: np.frombuffer(row["face_embedding"], dtype=np.float64)
        for row in cur.fetchall()
    }

    teacher_id = None
    start_time = time.time()

    # Capture for 2 seconds max
    while time.time() - start_time < 2:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)

        if blink_detect(frame):
            emb = get_embedding(frame)
            if emb is None:
                continue

            teacher_id = match_face(emb, teachers)
            if teacher_id:
                print("✅ Teacher recognized:", teacher_id)
                break

    cap.release()
    cur.close()
    db.close()

    print("🔒 Camera released")
    return teacher_id
