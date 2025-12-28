import cv2
import dlib
import numpy as np
import os

# Dlib face detector
detector = dlib.get_frontal_face_detector()

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "shape_predictor_68_face_landmarks.dat"
)

predictor = dlib.shape_predictor(MODEL_PATH)

def eye_aspect_ratio(eye):
    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    return (A + B) / (2.0 * C)

def blink_detect(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = detector(gray)

    for face in faces:
        landmarks = predictor(gray, face)

        left_eye = np.array(
            [(landmarks.part(i).x, landmarks.part(i).y) for i in range(36, 42)]
        )

        ear = eye_aspect_ratio(left_eye)

        if ear < 0.20:
            return True

    return False
