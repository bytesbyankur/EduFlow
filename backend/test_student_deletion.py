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
from attendance.models import Student, Course, CourseEnrollment

def test_deletion_flows():
    print("=" * 65)
    print("  TESTING STUDENT DELETION & DISK-DB SYNCHRONIZATION")
    print("=" * 65)

    client = APIClient()
    known_dir = os.path.join(os.path.dirname(__file__), "known_faces")

    # Step 1: Clean slate
    print("[1/5] Setting up clean test environment...")
    Student.objects.all().delete()
    for f in glob.glob(os.path.join(known_dir, "*")):
        try:
            os.remove(f)
        except OSError:
            pass

    # Step 2: Register two students (Om and Ankur)
    print("[2/5] Registering 'Om' and 'Ankur'...")
    dummy_img = np.full((300, 300, 3), 200, dtype=np.uint8)
    cv2.rectangle(dummy_img, (80, 80), (220, 220), (100, 150, 200), -1)
    _, buf = cv2.imencode('.jpg', dummy_img)
    img_bytes = buf.tobytes()

    client.post('/api/register-student/', {'name': 'Om', 'class_name': 'Advanced Neural Networks', 'file': SimpleUploadedFile('om.jpg', img_bytes, 'image/jpeg')}, format='multipart')
    client.post('/api/register-student/', {'name': 'Ankur', 'class_name': 'Advanced Neural Networks', 'file': SimpleUploadedFile('ankur.jpg', img_bytes, 'image/jpeg')}, format='multipart')

    res_dir1 = client.get('/api/students/')
    students1 = [s['name'] for s in res_dir1.data.get('student_records', [])]
    print(f"      - Registered Students: {students1}")
    assert len(students1) == 2 and 'Om' in students1 and 'Ankur' in students1

    # Step 3: Test Deleting 'Ankur' via the DELETE API
    print("[3/5] Deleting 'Ankur' via DELETE /api/students/Ankur ...")
    res_del = client.delete('/api/students/Ankur')
    print(f"      - Delete API Response: {res_del.data}")
    assert res_del.data.get('status') == 'success'

    # Verify Ankur is gone from API & disk
    res_dir2 = client.get('/api/students/')
    students2 = [s['name'] for s in res_dir2.data.get('student_records', [])]
    print(f"      - Registered Students after Delete API: {students2}")
    assert students2 == ['Om'], f"Expected only ['Om'], got {students2}"
    assert not os.path.exists(os.path.join(known_dir, "Ankur.jpg")), "Ankur.jpg was not deleted from disk"

    # Step 4: Test Manually Deleting 'Om.jpg' from disk
    print("[4/5] Simulating manual deletion of 'Om.jpg' from known_faces/ folder on disk...")
    om_file = os.path.join(known_dir, "Om.jpg")
    if os.path.exists(om_file):
        os.remove(om_file)
    print("      - Deleted Om.jpg on disk")

    # Step 5: Query API again - disk & database sync should prune Om
    print("[5/5] Querying /api/students/ after disk deletion...")
    res_dir3 = client.get('/api/students/')
    students3 = [s['name'] for s in res_dir3.data.get('student_records', [])]
    print(f"      - Registered Students after disk deletion: {students3} (Count: {len(students3)})")
    assert len(students3) == 0, f"Expected 0 students after disk deletion, got {students3}"

    res_roster = client.get('/api/get-class-roster/?class_name=Advanced Neural Networks')
    roster = res_roster.data.get('students', [])
    print(f"      - Class Roster after disk deletion: {roster} (Count: {len(roster)})")
    assert len(roster) == 0

    print("\n" + "=" * 65)
    print("  ALL STUDENT DELETION & DISK-DB SYNC TESTS PASSED! 🎉")
    print("  1. Delete API completely removes student from DB & disk.")
    print("  2. Manual disk deletion automatically prunes DB records.")
    print("=" * 65)

if __name__ == "__main__":
    test_deletion_flows()
