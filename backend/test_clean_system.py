import os
import sys
import glob
import django
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduflow.settings')
django.setup()

from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from attendance.models import Student, Course, CourseEnrollment, AttendanceLog

def test_clean_lifecycle():
    print("=" * 65)
    print("  TESTING COMPLETELY CLEAN SYSTEM LIFECYCLE (ZERO MOCK CELEBRITIES)")
    print("=" * 65)

    client = APIClient()

    # Step 1: Wipe DB and clear known_faces cache
    print("[1/6] Wiping attendance.db and clearing known_faces...")
    connection.close()
    db_path = os.path.join(os.path.dirname(__file__), "attendance.db")
    if os.path.exists(db_path):
        os.remove(db_path)

    known_dir = os.path.join(os.path.dirname(__file__), "known_faces")
    for f in glob.glob(os.path.join(known_dir, "*.pkl")) + glob.glob(os.path.join(known_dir, "*.npz")):
        try:
            os.remove(f)
        except OSError:
            pass

    # Step 2: Query clean state
    print("[2/6] Querying API on completely clean state...")
    res_students = client.get('/api/students/')
    print(f"      - Students in Directory: {res_students.data.get('count')} (Expected: 0)")
    assert res_students.data.get('count') == 0, f"Expected 0 students, got {res_students.data.get('count')}"

    res_roster = client.get('/api/get-class-roster/?class_name=Advanced Neural Networks')
    print(f"      - Roster for 'Advanced Neural Networks': {res_roster.data.get('students')} (Expected: [])")
    assert len(res_roster.data.get('students')) == 0

    # Step 3: Register ONLY "om"
    print("[3/6] Registering student 'om' in 'Advanced Neural Networks'...")
    # Create synthetic test face image or use om's face image if exists
    om_img_path = os.path.join(known_dir, "om.jpg")
    if not os.path.exists(om_img_path):
        # Create a test face image
        test_img = np.full((300, 300, 3), 180, dtype=np.uint8)
        cv2.rectangle(test_img, (80, 80), (220, 220), (220, 200, 180), -1)
        cv2.imwrite(om_img_path, test_img)

    with open(om_img_path, "rb") as f:
        om_bytes = f.read()

    upload_file = SimpleUploadedFile("om.jpg", om_bytes, content_type="image/jpeg")
    res_reg = client.post(
        '/api/register-student/',
        {'name': 'om', 'class_name': 'Advanced Neural Networks', 'file': upload_file},
        format='multipart'
    )
    print(f"      - Register API Status: {res_reg.data.get('status')}")
    print(f"      - Assigned Roll: {res_reg.data.get('roll_number')}")
    assert res_reg.data.get('status') == 'success'

    # Step 4: Verify Student Directory contains ONLY 'om'
    print("[4/6] Verifying Registered Students Directory...")
    res_students_after = client.get('/api/students/')
    dir_records = res_students_after.data.get('student_records', [])
    dir_names = [s['name'] for s in dir_records]
    print(f"      - Registered Directory: {dir_names} (Count: {len(dir_names)})")
    assert dir_names == ['om'], f"Expected only ['om'], got {dir_names}"

    # Step 5: Verify Class Roster for Advanced Neural Networks has ONLY 'om'
    print("[5/6] Verifying Class Roster for 'Advanced Neural Networks'...")
    res_roster_ann = client.get('/api/get-class-roster/?class_name=Advanced Neural Networks')
    ann_students = res_roster_ann.data.get('students', [])
    print(f"      - Advanced Neural Networks Roster: {ann_students}")
    assert ann_students == ['om']

    # Step 6: Mark Attendance with Om's Face
    print("[6/6] Marking Attendance with Om's Face image...")
    scan_file = SimpleUploadedFile("scan.jpg", om_bytes, content_type="image/jpeg")
    res_att = client.post(
        '/api/mark-attendance/',
        {'class_name': 'Advanced Neural Networks', 'file': scan_file},
        format='multipart'
    )
    print(f"      - Attendance Result: {res_att.data.get('status')}")
    print(f"      - Verified Students: {res_att.data.get('students')}")
    print(f"      - Confidence: {res_att.data.get('confidence')}%")
    assert res_att.data.get('status') == 'success'
    assert res_att.data.get('students') == ['om']

    print("\n" + "=" * 65)
    print("  ALL CLEAN SYSTEM TESTS PASSED PERFECTLY! 🚀")
    print("  Zero mock celebrities. Exactly 1 registered student ('om').")
    print("=" * 65)

if __name__ == "__main__":
    test_clean_lifecycle()
