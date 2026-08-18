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
from attendance.models import Student, Course, CourseEnrollment, AttendanceLog

def test_deletion_and_present_refresh():
    print("=" * 65)
    print("  TESTING DELETION & PRESENT ATTENDANCE PANEL REFRESH")
    print("=" * 65)

    client = APIClient()
    known_dir = os.path.join(os.path.dirname(__file__), "known_faces")

    # Step 1: Wipe cleanly
    print("[1/6] Cleaning up test environment...")
    Student.objects.all().delete()
    AttendanceLog.objects.all().delete()
    for f in glob.glob(os.path.join(known_dir, "*")):
        try:
            os.remove(f)
        except OSError:
            pass

    # Step 2: Register two students
    print("[2/6] Registering 'Om' and 'Ankur'...")
    dummy_img = np.full((300, 300, 3), 200, dtype=np.uint8)
    cv2.rectangle(dummy_img, (80, 80), (220, 220), (100, 150, 200), -1)
    _, buf = cv2.imencode('.jpg', dummy_img)
    img_bytes = buf.tobytes()

    client.post('/api/register-student/', {'name': 'Om', 'class_name': 'Advanced Neural Networks', 'file': SimpleUploadedFile('om.jpg', img_bytes, 'image/jpeg')}, format='multipart')
    client.post('/api/register-student/', {'name': 'Ankur', 'class_name': 'Advanced Neural Networks', 'file': SimpleUploadedFile('ankur.jpg', img_bytes, 'image/jpeg')}, format='multipart')

    # Step 3: Mark attendance for both
    print("[3/6] Marking Attendance for both Om and Ankur...")
    client.post('/api/mark-attendance/', {'class_name': 'Advanced Neural Networks', 'file': SimpleUploadedFile('om.jpg', img_bytes, 'image/jpeg')}, format='multipart')
    # Create distinct log for Ankur
    st_ankur = Student.objects.get(name='Ankur')
    AttendanceLog.objects.create(student=st_ankur, name='Ankur', class_name='Advanced Neural Networks', time='10:00:00', date='2026-08-18', confidence=98.0)

    res_dash1 = client.get('/api/get-dashboard-data/')
    print(f"      - Dashboard Stats: Total Students = {res_dash1.data['stats']['total_students']}, Present Today = {res_dash1.data['stats']['present_today']}")
    print(f"      - Recent Logs Count: {len(res_dash1.data['recent_logs'])}")
    assert res_dash1.data['stats']['total_students'] == 2
    assert res_dash1.data['stats']['present_today'] == 2
    assert len(res_dash1.data['recent_logs']) == 2

    # Step 4: Delete Ankur via POST /api/delete-student
    print("[4/6] Deleting 'Ankur' via POST /api/delete-student ...")
    res_del = client.post('/api/delete-student/', {'student_id': 'Ankur'}, format='json')
    print(f"      - Delete Response: {res_del.data}")
    assert res_del.data.get('status') == 'success'

    # Verify Dashboard immediately refreshes Present count & Recent Logs
    res_dash2 = client.get('/api/get-dashboard-data/')
    print(f"      - After deleting Ankur: Total Students = {res_dash2.data['stats']['total_students']}, Present Today = {res_dash2.data['stats']['present_today']}")
    recent_names = [r[1] for r in res_dash2.data['recent_logs']]
    print(f"      - Recent Logs Names: {recent_names}")
    assert res_dash2.data['stats']['total_students'] == 1, f"Expected 1 student, got {res_dash2.data['stats']['total_students']}"
    assert res_dash2.data['stats']['present_today'] == 1, f"Expected 1 present, got {res_dash2.data['stats']['present_today']}"
    assert recent_names == ['Om'], f"Expected only ['Om'] in recent logs, got {recent_names}"

    # Step 5: Simulate deleting Om's image from disk
    print("[5/6] Simulating disk deletion of 'Om.jpg' from known_faces/ ...")
    om_file = os.path.join(known_dir, "Om.jpg")
    if os.path.exists(om_file):
        os.remove(om_file)

    res_dash3 = client.get('/api/get-dashboard-data/')
    print(f"      - After disk wipe: Total Students = {res_dash3.data['stats']['total_students']}, Present Today = {res_dash3.data['stats']['present_today']}")
    print(f"      - Recent Logs Count: {len(res_dash3.data['recent_logs'])}")
    assert res_dash3.data['stats']['total_students'] == 0
    assert res_dash3.data['stats']['present_today'] == 0
    assert len(res_dash3.data['recent_logs']) == 0

    # Step 6: Test Reset DB endpoint
    print("[6/6] Testing Reset DB endpoint...")
    res_reset = client.post('/api/reset-db/')
    print(f"      - Reset Response: {res_reset.data.get('status')}")
    assert res_reset.data.get('status') == 'success'

    print("\n" + "=" * 65)
    print("  ALL DELETION & PRESENT ATTENDANCE REFRESH TESTS PASSED! 🎉")
    print("=" * 65)

if __name__ == "__main__":
    test_deletion_and_present_refresh()
