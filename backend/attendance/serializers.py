from rest_framework import serializers
from .models import Student, Course, CourseEnrollment, AttendanceLog


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['id', 'name', 'roll_number', 'photo_path', 'created_at']


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name', 'code', 'total_sessions']


class AttendanceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceLog
        fields = ['id', 'name', 'class_name', 'time', 'date', 'created_at']


class LoginRequestSerializer(serializers.Serializer):
    user_id = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    role = serializers.ChoiceField(choices=['teacher', 'student'], required=True)
