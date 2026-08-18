import os
import sys
import django
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduflow.settings')
django.setup()

from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from attendance.models import Student, Course, CourseEnrollment, AttendanceLog
from attendance.db_init import ensure_database_ready

def test_recovery():
    print("=" * 65)
    print("  SIMULATING DELETION OF attendance.db & known_faces RECOVERY")
    print("=" * 65)

    db_path = os.path.join(os.path.dirname(__file__), "attendance.db")

    # 1. Simulate database deletion
    print("[1/4] Simulating attendance.db wipe...")
    # Close existing connections before removing
    from django.db import connection
    connection.close()

    if os.path.exists(db_path):
        os.remove(db_path)
        print("      - Deleted attendance.db successfully")

    # 2. Trigger API calls immediately after deletion
    client = APIClient()
    print("[2/4] Calling API on clean state (auto-healing trigger)...")
    res_health = client.get('/api/health/')
    print(f"      - Health Check Status: {res_health.status_code}, Students in DB: {res_health.data.get('total_students_db')}")
    assert res_health.status_code == 200, "Health check failed after db deletion"

    res_students = client.get('/api/students/')
    print(f"      - Registered Students in Directory: {res_students.data.get('count')} students")
    assert res_students.data.get('count') >= 5, "Initial students not seeded"

    # 3. Test Student Registration
    print("[3/4] Testing New Student Registration (Alex Rivera)...")
    # Read a sample image to register
    sample_img_path = os.path.join(os.path.dirname(__file__), "known_faces", "om.jpg")
    with open(sample_img_path, "rb") as f:
        img_bytes = f.read()

    upload_file = SimpleUploadedFile("alex_rivera.jpg", img_bytes, content_type="image/jpeg")
    res_reg = client.post(
        '/api/register-student/',
        {'name': 'Alex Rivera', 'class_name': 'Advanced Neural Networks', 'file': upload_file},
        format='multipart'
    )
    print(f"      - Registration API: {res_reg.status_code}, Status: {res_reg.data.get('status')}")
    print(f"      - Assigned Roll ID: {res_reg.data.get('roll_number')}")
    assert res_reg.data.get('status') == 'success'

    # 4. Verify New Student appears in Registered Students Directory and Class Roster
    print("[4/4] Verifying Alex Rivera in Student Directory & Class Roster...")
    res_dir = client.get('/api/students/')
    dir_names = [s['name'] for s in res_dir.data.get('student_records', [])]
    print(f"      - All Directory Students: {dir_names}")
    assert 'Alex Rivera' in dir_names, "Newly registered student NOT found in all-students directory!"

    res_roster = client.get('/api/get-class-roster/?class_name=Advanced Neural Networks')
    roster_names = res_roster.data.get('students', [])
    print(f"      - Class Roster Students: {roster_names}")
    assert 'Alex Rivera' in roster_names, "Newly registered student NOT found in class roster!"

    print("\n" + "=" * 65)
    print("  ALL DATABASE DELETION & REGISTRATION RECOVERY TESTS PASSED! 🎉")
    print("=" * 65)

if __name__ == "__main__":
    test_recovery()
