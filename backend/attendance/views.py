import random
from datetime import datetime, timedelta

from django.http import HttpResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status

from .models import Student, Course, CourseEnrollment, AttendanceLog
from .services import (
    DEFAULT_CLASS_ROSTERS,
    get_roster_for_class,
    enroll_student_in_class,
    save_face_image,
    identify_face_in_image,
)


@api_view(['GET'])
def health_check(request):
    return Response({
        "status": "healthy",
        "service": "EduFlow Django Backend API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    })


@api_view(['POST'])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def login_view(request):
    user_id = request.data.get('user_id', '').strip()
    password = request.data.get('password', '').strip()
    role = request.data.get('role', '').strip().lower()

    if role == 'teacher':
        if user_id == "admin" and password == "admin":
            return Response({
                "status": "success",
                "name": "Professor Miller",
                "role": "teacher"
            })
        return Response(
            {"status": "error", "detail": "Invalid Faculty Credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    elif role == 'student':
        student = Student.objects.filter(roll_number__iexact=user_id, password=password).first()
        if not student:
            # Also allow login with exact student name for convenience
            student = Student.objects.filter(name__iexact=user_id, password=password).first()

        if student:
            return Response({
                "status": "success",
                "name": student.name,
                "roll_number": student.roll_number,
                "role": "student"
            })
        return Response(
            {"status": "error", "detail": "Invalid Student ID or Password"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    return Response(
        {"status": "error", "detail": "Invalid role specified"},
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def mark_attendance_view(request):
    class_name = request.data.get('class_name', '').strip()
    uploaded_file = request.FILES.get('file')

    if not class_name:
        return Response({"status": "failed", "message": "Class name is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not uploaded_file:
        return Response({"status": "failed", "message": "No image file provided"}, status=status.HTTP_400_BAD_REQUEST)

    image_bytes = uploaded_file.read()
    success, detected_names, msg = identify_face_in_image(image_bytes, class_name)

    if not success:
        return Response({"status": "failed", "message": msg})

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    saved_names = []
    for name in detected_names:
        student_obj = Student.objects.filter(name__iexact=name).first()
        actual_name = student_obj.name if student_obj else name
        
        # Check if already marked for THIS CLASS today
        already_marked = AttendanceLog.objects.filter(
            name__iexact=name,
            class_name=class_name,
            date=today_str
        ).exists()

        if not already_marked:
            AttendanceLog.objects.create(
                student=student_obj,
                name=actual_name,
                class_name=class_name,
                time=time_str,
                date=today_str
            )
        saved_names.append(actual_name)

    return Response({
        "status": "success",
        "students": saved_names,
        "class_name": class_name,
        "timestamp": f"{today_str} {time_str}"
    })


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def register_student_view(request):
    name = request.data.get('name', '').strip()
    class_name = request.data.get('class_name', '').strip()
    uploaded_file = request.FILES.get('file')

    if not name:
        return Response({"status": "error", "message": "Student name is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not class_name:
        return Response({"status": "error", "message": "Class selection is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not uploaded_file:
        return Response({"status": "error", "message": "Student photo is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 1. Save photo
        photo_path = save_face_image(uploaded_file, name)

        # 2. Generate Roll Number
        count = Student.objects.count() + 1
        reg_id = f"REG-2025-{count:03d}"

        # 3. Create or update student record
        student, created = Student.objects.get_or_create(
            name=name,
            defaults={
                'roll_number': reg_id,
                'password': 'password123',
                'photo_path': photo_path
            }
        )
        if not created:
            reg_id = student.roll_number
            student.photo_path = photo_path
            student.save()

        # 4. Enroll in class
        enroll_student_in_class(student, class_name)

        msg = f"Student {name} registered! ID: {reg_id} (Added to {class_name})"
        return Response({
            "status": "success",
            "message": msg,
            "roll_number": reg_id,
            "name": name,
            "class_name": class_name
        })

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_student_stats_view(request, student_name):
    student_name = student_name.strip()
    today = datetime.now()

    # Total Present Count
    total_present = AttendanceLog.objects.filter(name__iexact=student_name).count()

    # Daily Activity (Past 7 days)
    daily_activity = []
    for i in range(6, -1, -1):
        target_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        count = AttendanceLog.objects.filter(name__iexact=student_name, date=target_date).count()
        daily_activity.append(count)

    # Course stats
    enrolled_courses = []
    all_class_names = list(Course.objects.values_list('name', flat=True))
    for c_name in DEFAULT_CLASS_ROSTERS.keys():
        if c_name not in all_class_names:
            all_class_names.append(c_name)

    for course_name in all_class_names:
        roster = get_roster_for_class(course_name)
        # Check if student is in roster (case-insensitive)
        if any(s.lower() == student_name.lower() for s in roster):
            class_present = AttendanceLog.objects.filter(
                name__iexact=student_name,
                class_name=course_name
            ).count()

            sessions_so_far = 10
            class_rate = round((class_present / sessions_so_far) * 100, 1)

            status_label = "On Track"
            if class_rate < 75:
                status_label = "At Risk"
            if class_rate < 50:
                status_label = "Critical"

            enrolled_courses.append({
                "name": course_name,
                "present": class_present,
                "rate": class_rate,
                "status": status_label
            })

    # Academic deterministic mock stats
    random.seed(student_name)
    gpa = round(random.uniform(2.5, 4.0), 2)
    credits_earned = random.randint(10, 25)
    class_rank = random.randint(1, 50)

    overall_rate = (
        round(sum(c['rate'] for c in enrolled_courses) / len(enrolled_courses), 1)
        if enrolled_courses else 0.0
    )

    return Response({
        "name": student_name,
        "attendance_rate": overall_rate,
        "present_days": total_present,
        "total_days": 30,
        "gpa": gpa,
        "credits": credits_earned,
        "rank": f"#{class_rank}",
        "courses": enrolled_courses,
        "graph_data": daily_activity
    })


@api_view(['GET'])
def get_student_history_view(request, student_name):
    logs = AttendanceLog.objects.filter(
        name__iexact=student_name.strip()
    ).order_by('-date', '-time')

    history = [
        {"date": log.date, "time": log.time, "class": log.class_name}
        for log in logs
    ]
    return Response({"history": history})


@api_view(['GET'])
def get_dashboard_data_view(request):
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    total_students = Student.objects.count()
    present_today = AttendanceLog.objects.filter(date=today_str).values('name').distinct().count()

    recent_logs_qs = AttendanceLog.objects.all().order_by('-id')[:10]
    
    # Format log tuples: [roll_number, name, time, class_name]
    recent_logs = []
    for log in recent_logs_qs:
        student = log.student or Student.objects.filter(name=log.name).first()
        roll = student.roll_number if student else "N/A"
        recent_logs.append([roll, log.name, log.time, log.class_name])

    return Response({
        "stats": {
            "total_students": total_students,
            "present_today": present_today
        },
        "recent_logs": recent_logs
    })


@api_view(['GET'])
def get_class_roster_view(request):
    class_name = request.query_params.get('class_name', 'Advanced Neural Networks').strip()
    students = get_roster_for_class(class_name)
    return Response({
        "class": class_name,
        "students": students,
        "count": len(students)
    })


@api_view(['GET'])
def get_courses_list_view(request):
    all_class_names = list(Course.objects.values_list('name', flat=True))
    for c_name in DEFAULT_CLASS_ROSTERS.keys():
        if c_name not in all_class_names:
            all_class_names.append(c_name)
    return Response({"courses": all_class_names})


@api_view(['GET'])
def export_csv_view(request):
    logs = AttendanceLog.objects.all().order_by('-id')
    csv_content = "ID,Name,Class,Time,Date\n"
    for log in logs:
        csv_content += f"{log.id},{log.name},{log.class_name},{log.time},{log.date}\n"

    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'
    return response


@api_view(['POST'])
def reset_db_view(request):
    # Clear attendance logs
    AttendanceLog.objects.all().delete()
    return Response({"message": "Attendance records reset successfully", "status": "success"})
