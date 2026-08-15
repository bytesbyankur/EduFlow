from django.db import models


class Student(models.Model):
    name = models.CharField(max_length=150)
    roll_number = models.CharField(max_length=50, unique=True, db_index=True)
    password = models.CharField(max_length=128, default='password123')
    photo_path = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'students'
        ordering = ['id']

    def __str__(self):
        return f"{self.name} ({self.roll_number})"


class Course(models.Model):
    name = models.CharField(max_length=150, unique=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    total_sessions = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'courses'
        ordering = ['name']

    def __str__(self):
        return self.name


class CourseEnrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'course_enrollments'
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.name} -> {self.course.name}"


class AttendanceLog(models.Model):
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='attendance_records')
    name = models.CharField(max_length=150, db_index=True)
    class_name = models.CharField(max_length=150, db_index=True)
    time = models.CharField(max_length=20)  # e.g. "14:30:15"
    date = models.CharField(max_length=20, db_index=True)  # e.g. "2026-08-15"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance_logs'
        ordering = ['-id']

    def __str__(self):
        return f"{self.name} - {self.class_name} on {self.date} {self.time}"
