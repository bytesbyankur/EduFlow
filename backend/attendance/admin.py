from django.contrib import admin
from .models import Student, Course, CourseEnrollment, AttendanceLog


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'name', 'created_at')
    search_fields = ('name', 'roll_number')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'total_sessions')
    search_fields = ('name', 'code')


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at')
    list_filter = ('course',)


@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'class_name', 'date', 'time', 'created_at')
    list_filter = ('class_name', 'date')
    search_fields = ('name', 'class_name')
