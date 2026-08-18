import os
import sys
import glob
import django
import cv2
import numpy as np
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduflow.settings')
django.setup()

from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from attendance.models import Student, Course, CourseEnrollment, AttendanceLog
from attendance.nn.face_detector import FaceDetector

def generate_student_face(student_idx):
    f = np.full((120, 120, 3), 200, dtype=np.uint8)
    skin_tone = (180 + (student_idx * 3) % 40, 200 + (student_idx * 2) % 35, 220 + (student_idx * 4) % 25)
    cv2.ellipse(f, (60, 60), (45, 55), 0, 0, 360, skin_tone, -1)
    
    # Eyebrows
    cv2.line(f, (35, 38), (55, 38), (50, 40, 30), 4)
    cv2.line(f, (65, 38), (85, 38), (50, 40, 30), 4)
    
    # Eyes
    eye_color = ((student_idx * 15) % 200, 30, 20)
    cv2.ellipse(f, (45, 48), (10, 6), 0, 0, 360, (240, 245, 250), -1)
    cv2.circle(f, (45, 48), 5, eye_color, -1)
    cv2.ellipse(f, (75, 48), (10, 6), 0, 0, 360, (240, 245, 250), -1)
    cv2.circle(f, (75, 48), 5, eye_color, -1)
    
    # Nose
    cv2.line(f, (60, 45), (60, 68), (140, 160, 180), 3)
    cv2.line(f, (54, 68), (66, 68), (130, 150, 170), 3)
    
    # Mouth
    cv2.ellipse(f, (60, 85), (18, 7), 0, 0, 360, (110, 110, 180), -1)
    cv2.line(f, (44, 85), (76, 85), (60, 60, 120), 2)
    
    # Blur slightly
    f = cv2.GaussianBlur(f, (3, 3), 0)
    return f

def test_crowd_recognition():
    print("=" * 65)
    print("  TESTING HIGH-CAPACITY MULTI-FACE DETECTION & ATTENDANCE (20+ FACES)")
    print("=" * 65)

    client = APIClient()
    known_dir = os.path.join(os.path.dirname(__file__), "known_faces")

    # Clean slate
    Student.objects.all().delete()
    AttendanceLog.objects.all().delete()
    for f in glob.glob(os.path.join(known_dir, "*")):
        try:
            os.remove(f)
        except OSError:
            pass

    # Register 20 distinct students
    num_students = 20
    print(f"[1/4] Registering {num_students} distinct students in 'Advanced Neural Networks'...")
    student_names = [f"Student_{i+1:02d}" for i in range(num_students)]
    student_face_templates = []

    for i, name in enumerate(student_names):
        face_img = generate_student_face(i)
        student_face_templates.append(face_img)

        _, buf = cv2.imencode('.jpg', face_img)
        img_bytes = buf.tobytes()

        client.post(
            '/api/register-student/',
            {'name': name, 'class_name': 'Advanced Neural Networks', 'file': SimpleUploadedFile(f'{name}.jpg', img_bytes, 'image/jpeg')},
            format='multipart'
        )

    res_students = client.get('/api/students/')
    print(f"      - Registered in Database: {res_students.data.get('count')} students")
    assert res_students.data.get('count') == num_students

    # Build simulated classroom crowd frame (4 rows x 5 columns = 20 students)
    print("[2/4] Constructing simulated classroom crowd frame with 20 students (1280x960)...")
    crowd_frame = np.full((960, 1280, 3), 245, dtype=np.uint8)

    rows, cols = 4, 5
    for r in range(rows):
        for c in range(cols):
            idx = r * cols + c
            if idx < len(student_face_templates):
                face_sample = student_face_templates[idx]
                y_pos = 40 + r * 220
                x_pos = 40 + c * 240
                crowd_frame[y_pos:y_pos+120, x_pos:x_pos+120] = face_sample

    # Run Multi-Face Detector
    print("[3/4] Running Multi-Face Detector on 20-student classroom frame...")
    detector = FaceDetector(min_face_size=(24, 24))
    t0 = time.perf_counter()
    detected_boxes = detector.detect_faces(crowd_frame)
    det_time_ms = (time.perf_counter() - t0) * 1000.0

    print(f"      - Multi-Face Detection: {len(detected_boxes)} distinct faces detected in {det_time_ms:.1f}ms")
    assert len(detected_boxes) == 20, f"Expected 20 faces detected, got {len(detected_boxes)}"

    # Submit 20-student crowd photo for attendance marking
    print("[4/4] Submitting 20-student crowd photo to /api/mark-attendance/ ...")
    _, crowd_buf = cv2.imencode('.jpg', crowd_frame)
    crowd_bytes = crowd_buf.tobytes()

    t_start = time.perf_counter()
    res_attendance = client.post(
        '/api/mark-attendance/',
        {'class_name': 'Advanced Neural Networks', 'file': SimpleUploadedFile('crowd_scan.jpg', crowd_bytes, 'image/jpeg')},
        format='multipart'
    )
    total_ms = (time.perf_counter() - t_start) * 1000.0

    verified_count = len(res_attendance.data.get('students', []))
    print(f"      - API Status: {res_attendance.data.get('status')}")
    print(f"      - Faces Detected in Scan: {res_attendance.data.get('faces_detected')}")
    print(f"      - Verified Students Count: {verified_count}")
    print(f"      - Primary Confidence: {res_attendance.data.get('confidence')}%")
    print(f"      - Server Inference Latency: {res_attendance.data.get('inference_time_ms')}ms")
    print(f"      - Total HTTP Roundtrip: {total_ms:.1f}ms")

    assert res_attendance.data.get('status') == 'success'
    assert res_attendance.data.get('faces_detected') == 20
    assert verified_count == 20, f"Expected 20 verified students, got {verified_count}"

    # Verify Dashboard stats
    res_dash = client.get('/api/get-dashboard-data/')
    print(f"\n      - Teacher Dashboard Stats: Total = {res_dash.data['stats']['total_students']}, Present Today = {res_dash.data['stats']['present_today']}")
    assert res_dash.data['stats']['present_today'] == 20

    print("\n" + "=" * 65)
    print(f"  ALL HIGH-CAPACITY CROWD SCAN TESTS PASSED! 🎉")
    print(f"  Successfully recognized & marked attendance for {verified_count}/20 students simultaneously!")
    print("=" * 65)

if __name__ == "__main__":
    test_crowd_recognition()
