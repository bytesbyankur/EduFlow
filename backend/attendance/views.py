import random
import cv2
import numpy as np
from datetime import datetime, timedelta

from django.http import HttpResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status

from .models import Student, Course, CourseEnrollment, AttendanceLog
from .db_init import ensure_database_ready
from .services import (
    get_roster_for_class,
    get_student_records_for_class,
    enroll_student_in_class,
    save_face_image,
    delete_student_service,
    sync_disk_and_database,
    identify_face_in_image,
    get_face_engine,
)


@api_view(['GET'])
def health_check(request):
    ensure_database_ready()
    sync_disk_and_database()
    engine = get_face_engine()
    return Response({
        "status": "healthy",
        "service": "EduFlow Neural Attendance API",
        "version": "2.1.0",
        "nn_model": "LightweightFaceNet-v2",
        "parameters": f"{engine.model.get_parameter_count():,}",
        "gallery_size": len(engine.gallery_embeddings),
        "total_students_db": Student.objects.count(),
        "device": str(engine.device),
        "timestamp": datetime.now().isoformat()
    })


@api_view(['GET'])
def get_model_info_view(request):
    ensure_database_ready()
    sync_disk_and_database()
    engine = get_face_engine()
    param_count = engine.model.get_parameter_count()
    return Response({
        "model_name": "LightweightFaceNet-v2",
        "architecture": "MobileNetV3-SE CNN (Inverted Residual + Squeeze-and-Excitation)",
        "parameter_count": param_count,
        "input_resolution": "112x112 RGB",
        "embedding_dim": 128,
        "metric": "L2-Normalized Cosine Distance",
        "verification_threshold": engine.match_threshold,
        "active_gallery_faces": len(engine.gallery_embeddings),
        "device": str(engine.device),
        "registered_students": list(engine.gallery_embeddings.keys()),
        "status": "Active & Ready"
    })


@api_view(['POST'])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def login_view(request):
    ensure_database_ready()
    sync_disk_and_database()
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
    ensure_database_ready()
    sync_disk_and_database()
    class_name = request.data.get('class_name', '').strip()
    uploaded_file = request.FILES.get('file')

    if not class_name:
        return Response({"status": "failed", "message": "Class name is required"}, status=status.HTTP_400_BAD_REQUEST)
    if not uploaded_file:
        return Response({"status": "failed", "message": "No image file provided"}, status=status.HTTP_400_BAD_REQUEST)

    image_bytes = uploaded_file.read()
    res = identify_face_in_image(image_bytes, class_name)

    if not res.get("success", False):
        return Response({
            "status": "failed",
            "message": res.get("message", "Verification failed"),
            "confidence": res.get("primary_confidence", 0.0),
            "matches": res.get("matches", []),
            "inference_time_ms": res.get("inference_ms", 0.0),
            "faces_detected": res.get("faces_detected", 0),
            "model": res.get("model", "LightweightFaceNet-v2")
        })

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    saved_names = []
    matches_detail = []
    
    for match in res.get("matches", []):
        if not match.get("is_verified", False):
            continue

        name = match["name"]
        conf = match.get("confidence", 95.0)
        student_obj = Student.objects.filter(name__iexact=name).first()
        actual_name = student_obj.name if student_obj else name
        roll_num = student_obj.roll_number if student_obj else "N/A"

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
                date=today_str,
                confidence=conf
            )
            is_newly_logged = True
        else:
            is_newly_logged = False

        if actual_name not in saved_names:
            saved_names.append(actual_name)

        matches_detail.append({
            "name": actual_name,
            "roll_number": roll_num,
            "confidence": conf,
            "similarity": match.get("similarity", 0.95),
            "is_newly_logged": is_newly_logged,
            "status": "Verified & Logged" if is_newly_logged else "Already Marked"
        })

    return Response({
        "status": "success",
        "students": saved_names,
        "matches": matches_detail,
        "confidence": res.get("primary_confidence", 95.0),
        "class_name": class_name,
        "timestamp": f"{today_str} {time_str}",
        "inference_time_ms": res.get("inference_ms", 12.0),
        "model": res.get("model", "LightweightFaceNet-v2"),
        "faces_detected": res.get("faces_detected", len(saved_names))
    })


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def register_student_view(request):
    ensure_database_ready()
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
        # 1. Save photo and generate neural embedding
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

        msg = f"Student {name} registered successfully! ID: {reg_id} (Enrolled in {class_name})"
        return Response({
            "status": "success",
            "message": msg,
            "roll_number": reg_id,
            "name": name,
            "class_name": class_name,
            "photo_path": photo_path,
            "embedding_registered": True
        })

    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE', 'POST', 'GET'])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def delete_student_view(request, student_id=None):
    """
    Deletes a student from database, enrollments, logs, physical photo, and memory/npz cache.
    Accepts identifier via URL param, JSON body, or form data.
    """
    ensure_database_ready()
    data = request.data if isinstance(request.data, dict) else {}
    identifier = (
        student_id
        or data.get('student_id')
        or data.get('name')
        or data.get('id')
        or data.get('roll_number')
        or request.query_params.get('student_id')
        or request.query_params.get('name')
        or request.query_params.get('id')
    )

    if not identifier:
        return Response(
            {"status": "error", "message": "Student identifier (name or ID) is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    success, msg = delete_student_service(str(identifier))
    return Response({
        "status": "success" if success else "error",
        "message": msg,
        "deleted_identifier": str(identifier)
    })


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def compare_faces_view(request):
    ensure_database_ready()
    file1 = request.FILES.get('image1')
    file2 = request.FILES.get('image2')

    if not file1 or not file2:
        return Response({"status": "error", "message": "Both image1 and image2 are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        engine = get_face_engine()
        img1 = cv2.imdecode(np.frombuffer(file1.read(), np.uint8), cv2.IMREAD_COLOR)
        img2 = cv2.imdecode(np.frombuffer(file2.read(), np.uint8), cv2.IMREAD_COLOR)

        crop1 = engine.detector.get_primary_face(img1)
        crop2 = engine.detector.get_primary_face(img2)

        emb1 = engine.compute_embedding(crop1)
        emb2 = engine.compute_embedding(crop2)

        sim = float(np.dot(emb1, emb2))
        confidence = engine.calculate_confidence(sim)
        is_match = sim >= engine.match_threshold

        return Response({
            "status": "success",
            "is_match": is_match,
            "similarity": round(sim, 4),
            "confidence": confidence,
            "threshold": engine.match_threshold,
            "model": "LightweightFaceNet-v2"
        })
    except Exception as e:
        return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_student_stats_view(request, student_name):
    ensure_database_ready()
    sync_disk_and_database()
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

    for course_name in all_class_names:
        roster = get_roster_for_class(course_name)
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
    ensure_database_ready()
    sync_disk_and_database()
    logs = AttendanceLog.objects.filter(
        name__iexact=student_name.strip()
    ).order_by('-date', '-time')

    history = [
        {
            "date": log.date,
            "time": log.time,
            "class": log.class_name,
            "confidence": getattr(log, 'confidence', 95.0) or 95.0
        }
        for log in logs
    ]
    return Response({"history": history})


@api_view(['GET'])
def get_dashboard_data_view(request):
    ensure_database_ready()
    sync_disk_and_database()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    active_students_qs = Student.objects.all().order_by('id')
    total_students = active_students_qs.count()
    active_names = list(active_students_qs.values_list('name', flat=True))

    if total_students == 0 or not active_names:
        return Response({
            "stats": {
                "total_students": 0,
                "present_today": 0
            },
            "recent_logs": []
        })

    # Present today count matching ONLY currently registered active students
    present_today = (
        AttendanceLog.objects.filter(date=today_str, name__in=active_names)
        .values('name')
        .distinct()
        .count()
    )

    # Recent logs matching ONLY currently registered active students
    recent_logs_qs = AttendanceLog.objects.filter(name__in=active_names).order_by('-id')[:10]
    
    recent_logs = []
    for log in recent_logs_qs:
        student = log.student or Student.objects.filter(name__iexact=log.name).first()
        roll = student.roll_number if student else "N/A"
        conf = getattr(log, 'confidence', 95.0) or 95.0
        recent_logs.append([roll, log.name, log.time, log.class_name, conf])

    return Response({
        "stats": {
            "total_students": total_students,
            "present_today": present_today
        },
        "recent_logs": recent_logs
    })


@api_view(['GET'])
def get_class_roster_view(request):
    ensure_database_ready()
    sync_disk_and_database()
    class_name = request.query_params.get('class_name', 'Advanced Neural Networks').strip()
    students = get_roster_for_class(class_name)
    student_records = get_student_records_for_class(class_name)
    return Response({
        "class": class_name,
        "students": students,
        "student_records": student_records,
        "count": len(students)
    })


@api_view(['GET'])
def get_all_students_view(request):
    ensure_database_ready()
    sync_disk_and_database()
    student_records = get_student_records_for_class('all')
    return Response({
        "students": [s["name"] for s in student_records],
        "student_records": student_records,
        "count": len(student_records)
    })


@api_view(['GET'])
def get_courses_list_view(request):
    ensure_database_ready()
    all_class_names = list(Course.objects.values_list('name', flat=True))
    return Response({"courses": all_class_names})


@api_view(['GET'])
def export_csv_view(request):
    ensure_database_ready()
    sync_disk_and_database()
    active_names = list(Student.objects.values_list('name', flat=True))
    logs = AttendanceLog.objects.filter(name__in=active_names).order_by('-id')
    csv_content = "ID,Name,Class,Time,Date,Confidence\n"
    for log in logs:
        conf = getattr(log, 'confidence', 95.0) or 95.0
        csv_content += f"{log.id},{log.name},{log.class_name},{log.time},{log.date},{conf}%\n"

    response = HttpResponse(csv_content, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'
    return response


@api_view(['POST', 'GET'])
def reset_db_view(request):
    ensure_database_ready()
    AttendanceLog.objects.all().delete()
    return Response({
        "message": "Attendance records reset successfully",
        "status": "success",
        "stats": {
            "total_students": Student.objects.count(),
            "present_today": 0
        },
        "recent_logs": []
    })
