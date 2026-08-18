import os
from django.core.management.base import BaseCommand
from django.conf import settings
from attendance.models import Student, Course, CourseEnrollment, AttendanceLog

DEFAULT_COURSES = [
    "Advanced Neural Networks",
    "Ethics in AI",
    "Computer Vision 101"
]


class Command(BaseCommand):
    help = 'Seeds database with default courses.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Initializing EduFlow courses...'))

        for course_name in DEFAULT_COURSES:
            course, created = Course.objects.get_or_create(
                name=course_name,
                defaults={'total_sessions': 10}
            )
            self.stdout.write(f"  Course: {course.name}")

        self.stdout.write(self.style.SUCCESS(
            f"Database initialized! ({Student.objects.count()} students, {Course.objects.count()} courses)"
        ))
