import os
from datetime import datetime, timedelta
import random

from django.core.management.base import BaseCommand
from django.conf import settings
from attendance.models import Student, Course, CourseEnrollment, AttendanceLog
from attendance.services import DEFAULT_CLASS_ROSTERS


class Command(BaseCommand):
    help = 'Seeds database with initial students, courses, enrollments, and demo attendance logs.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Seeding EduFlow database...'))

        # 1. Seed Students
        initial_students = [
            ("Barack Obama", "REG-2025-001", "password123"),
            ("Rashmika Mandana", "REG-2025-002", "password123"),
            ("Elon Musk", "REG-2025-003", "password123"),
            ("Taylor Swift", "REG-2025-004", "password123"),
            ("Sraddha Kapoor", "REG-2025-005", "password123"),
        ]

        student_objs = {}
        for name, roll_no, pwd in initial_students:
            known_img = os.path.join(settings.KNOWN_FACES_DIR, f"{name}.jpg")
            photo_path = known_img if os.path.exists(known_img) else None
            student, created = Student.objects.get_or_create(
                roll_number=roll_no,
                defaults={
                    'name': name,
                    'password': pwd,
                    'photo_path': photo_path
                }
            )
            if not created and student.name != name:
                student.name = name
                student.save()
            student_objs[name] = student
            self.stdout.write(f"  Student: {student.name} ({student.roll_number})")

        # 2. Seed Courses & Enrollments
        for course_name, student_names in DEFAULT_CLASS_ROSTERS.items():
            course, _ = Course.objects.get_or_create(
                name=course_name,
                defaults={'total_sessions': 10}
            )
            for s_name in student_names:
                st = student_objs.get(s_name) or Student.objects.filter(name=s_name).first()
                if st:
                    CourseEnrollment.objects.get_or_create(student=st, course=course)
            self.stdout.write(f"  Course: {course.name} ({len(student_names)} students enrolled)")

        # 3. Seed Demo Attendance Logs if empty
        if AttendanceLog.objects.count() == 0:
            self.stdout.write("  Generating past 7-day demo attendance logs...")
            today = datetime.now()
            for days_ago in range(6, -1, -1):
                date_val = (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                for s_name, student in student_objs.items():
                    # Randomize attendance chance for demo richness
                    for c_name, enrolled_list in DEFAULT_CLASS_ROSTERS.items():
                        if s_name in enrolled_list:
                            # 75% chance of presence on weekdays
                            if random.random() < 0.75:
                                hour = random.randint(9, 16)
                                minute = random.randint(10, 59)
                                sec = random.randint(10, 59)
                                time_val = f"{hour:02d}:{minute:02d}:{sec:02d}"
                                AttendanceLog.objects.create(
                                    student=student,
                                    name=s_name,
                                    class_name=c_name,
                                    time=time_val,
                                    date=date_val
                                )

        self.stdout.write(self.style.SUCCESS(
            f"Database successfully seeded! ({Student.objects.count()} students, {Course.objects.count()} courses, {AttendanceLog.objects.count()} attendance logs)"
        ))
