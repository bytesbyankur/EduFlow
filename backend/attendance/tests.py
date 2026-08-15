from django.test import TestCase, Client
from attendance.models import Student, Course, CourseEnrollment, AttendanceLog

class AttendanceApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = Student.objects.create(
            name="Test Student",
            roll_number="REG-2025-999",
            password="password123"
        )
        self.course = Course.objects.create(
            name="Advanced Neural Networks",
            code="ANN-101",
            total_sessions=10
        )
        CourseEnrollment.objects.create(student=self.student, course=self.course)
        AttendanceLog.objects.create(
            student=self.student,
            name=self.student.name,
            class_name=self.course.name,
            time="10:00:00",
            date="2026-08-15"
        )

    def test_health_check(self):
        res = self.client.get('/health/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['status'], 'healthy')

    def test_teacher_login(self):
        res = self.client.post('/login', {'user_id': 'admin', 'password': 'admin', 'role': 'teacher'}, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['role'], 'teacher')

    def test_student_login(self):
        res = self.client.post('/login', {'user_id': 'REG-2025-999', 'password': 'password123', 'role': 'student'}, content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['role'], 'student')
        self.assertEqual(res.json()['name'], 'Test Student')

    def test_get_dashboard_data(self):
        res = self.client.get('/get-dashboard-data')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn('stats', data)
        self.assertIn('recent_logs', data)

    def test_get_student_stats(self):
        res = self.client.get('/student/stats/Test Student')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['name'], 'Test Student')
        self.assertIn('attendance_rate', data)
        self.assertIn('courses', data)
        self.assertIn('graph_data', data)

    def test_get_class_roster(self):
        res = self.client.get('/get-class-roster?class_name=Advanced Neural Networks')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data['class'], 'Advanced Neural Networks')
