import cv2
import dlib
import numpy as np
import os

# ---------------- CONFIG ----------------
EAR_THRESHOLD = 0.20
BLINK_FRAMES = 2
# ---------------------------------------

# Dlib face detector
detector = dlib.get_frontal_face_detector()

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "shape_predictor_68_face_landmarks.dat"
)

# ✅ Fix: model existence check
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("shape_predictor_68_face_landmarks.dat not found")

predictor = dlib.shape_predictor(MODEL_PATH)

blink_counter = 0

def eye_aspect_ratio(eye):
    # ✅ Fix: division-by-zero guard
    C = np.linalg.norm(eye[0] - eye[3])
    if C == 0:
        return 0.0

    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    return (A + B) / (2.0 * C)

def blink_detect(frame):
    global blink_counter

    # ✅ Fix: frame safety
    if frame is None:
        blink_counter = 0
        return False

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    # ✅ Fix: reject no or multiple faces
    if len(faces) != 1:
        blink_counter = 0
        return False

    face = faces[0]

    # ✅ Fix: landmark failure guard
    try:
        landmarks = predictor(gray, face)
    except Exception:
        blink_counter = 0
        return False

    # Both eyes (unchanged structure)
    left_eye = np.array(
        [(landmarks.part(i).x, landmarks.part(i).y) for i in range(36, 42)]
    )
    right_eye = np.array(
        [(landmarks.part(i).x, landmarks.part(i).y) for i in range(42, 48)]
    )

    left_ear = eye_aspect_ratio(left_eye)
    right_ear = eye_aspect_ratio(right_eye)

    # ✅ Fix: invalid EAR values
    if left_ear <= 0 or right_ear <= 0:
        blink_counter = 0
        return False

    ear = (left_ear + right_ear) / 2.0

    # -------- REAL BLINK LOGIC --------
    if ear < EAR_THRESHOLD:
        blink_counter += 1
    else:
        if blink_counter >= BLINK_FRAMES:
            blink_counter = 0
            return True   # ✅ REAL BLINK
        blink_counter = 0
    # ---------------------------------

    return False