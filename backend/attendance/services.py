import os
import glob
import cv2
import numpy as np
from django.conf import settings
from .models import Student, Course, CourseEnrollment, AttendanceLog
from .nn.engine import FaceEngine
from .db_init import ensure_database_ready

_face_engine = None

def get_face_engine() -> FaceEngine:
    global _face_engine
    if _face_engine is None:
        known_dir = get_known_faces_dir()
        _face_engine = FaceEngine.get_instance(known_faces_dir=known_dir)
    return _face_engine

def get_known_faces_dir():
    known_dir = getattr(settings, 'KNOWN_FACES_DIR', os.path.join(settings.BASE_DIR, 'known_faces'))
    os.makedirs(known_dir, exist_ok=True)
    return str(known_dir)

def sync_disk_and_database():
    """
    Ensures perfect consistency between the physical known_faces directory and the SQLite database.
    1. If a photo was manually deleted from disk, automatically prunes the corresponding DB student record.
    2. Prunes all orphan attendance logs and course enrollments for deleted students.
    3. Keeps in-memory FaceEngine embeddings strictly synced.
    """
    ensure_database_ready()
    known_dir = get_known_faces_dir()
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    
    disk_files = [
        os.path.splitext(os.path.basename(p))[0].strip().lower()
        for p in glob.glob(os.path.join(known_dir, "*"))
        if p.lower().endswith(image_extensions)
    ]
    
    # 1. Prune any student in DB whose image was deleted from known_faces
    all_students = list(Student.objects.all())
    for st in all_students:
        st_norm = st.name.strip().lower()
        has_disk_file = (st_norm in disk_files)
        if st.photo_path and os.path.exists(st.photo_path):
            has_disk_file = True
            
        if not has_disk_file:
            # Photo was deleted on disk -> Delete student, enrollments, and attendance logs
            AttendanceLog.objects.filter(student=st).delete()
            AttendanceLog.objects.filter(name__iexact=st.name).delete()
            CourseEnrollment.objects.filter(student=st).delete()
            st.delete()

    # 2. Prune orphan attendance logs for students that no longer exist
    active_names = list(Student.objects.values_list('name', flat=True))
    if not active_names:
        AttendanceLog.objects.all().delete()
    else:
        AttendanceLog.objects.exclude(name__in=active_names).delete()

    # 3. Resync engine gallery
    get_face_engine().sync_gallery(force_reload=False)

def clear_face_cache():
    """Removes cached representation files and forces gallery refresh."""
    known_dir = get_known_faces_dir()
    for cache_pattern in ["*.pkl", "*.npz"]:
        for f in glob.glob(os.path.join(known_dir, cache_pattern)):
            try:
                os.remove(f)
            except OSError:
                pass
    get_face_engine().sync_gallery(force_reload=True)

def get_roster_for_class(class_name: str) -> list[str]:
    """
    Returns the list of student names enrolled in the given class directly from database.
    """
    sync_disk_and_database()
    course = Course.objects.filter(name__iexact=class_name.strip()).first()
    if course:
        enrolled = list(
            CourseEnrollment.objects.filter(course=course)
            .values_list('student__name', flat=True)
        )
        return enrolled
    return []

def get_student_records_for_class(class_name: str) -> list[dict]:
    """
    Returns structured student records (id, name, roll_number, class_name, status) from database.
    If class_name is 'all' or empty, returns all registered students.
    """
    sync_disk_and_database()
    records = []
    
    if not class_name or class_name.lower() in ('all', 'everyone'):
        students_qs = Student.objects.all().order_by('id')
        for st in students_qs:
            courses_list = list(st.enrollments.values_list('course__name', flat=True))
            c_str = ", ".join(courses_list) if courses_list else "Not Assigned"
            records.append({
                "id": st.id,
                "name": st.name,
                "roll_number": st.roll_number,
                "class_name": c_str,
                "photo_path": st.photo_path,
                "status": "Enrolled"
            })
        return records

    course = Course.objects.filter(name__iexact=class_name.strip()).first()
    if course:
        enrollments = CourseEnrollment.objects.filter(course=course).select_related('student')
        for en in enrollments:
            st = en.student
            records.append({
                "id": st.id,
                "name": st.name,
                "roll_number": st.roll_number,
                "class_name": course.name,
                "photo_path": st.photo_path,
                "status": "Enrolled"
            })
    return records

def enroll_student_in_class(student: Student, class_name: str):
    """Enrolls a student in a course in the DB and ensures the course exists."""
    ensure_database_ready()
    course, _ = Course.objects.get_or_create(name=class_name.strip())
    CourseEnrollment.objects.get_or_create(student=student, course=course)

def save_face_image(uploaded_file, name: str) -> str:
    """Saves the student photo to known_faces and registers embedding in FaceEngine."""
    known_dir = get_known_faces_dir()
    file_path = os.path.join(known_dir, f"{name}.jpg")
    
    with open(file_path, "wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
            
    # Compute and cache embedding for the new face
    try:
        img = cv2.imread(file_path)
        if img is not None:
            engine = get_face_engine()
            engine.register_face(name, img)
    except Exception as e:
        print(f"Embedding cache error for {name}: {e}")

    return file_path

def delete_student_service(student_identifier: str) -> tuple[bool, str]:
    """
    Completely removes a student from the SQLite database, their course enrollments,
    attendance logs, physical photo file, and FaceEngine memory/npz cache.
    """
    ensure_database_ready()
    student = None
    target_name = str(student_identifier).strip()

    # 1. Try finding by numeric ID
    if target_name.isdigit():
        student = Student.objects.filter(id=int(target_name)).first()

    # 2. Try finding by Roll Number
    if not student:
        student = Student.objects.filter(roll_number__iexact=target_name).first()

    # 3. Try finding by Name
    if not student:
        student = Student.objects.filter(name__iexact=target_name).first()

    if student:
        target_name = student.name
        # Delete attendance logs
        AttendanceLog.objects.filter(student=student).delete()
        AttendanceLog.objects.filter(name__iexact=student.name).delete()
        # Delete course enrollments
        CourseEnrollment.objects.filter(student=student).delete()
        # Delete student record
        student.delete()

    # Always delete physical photo & purge FaceEngine gallery
    engine = get_face_engine()
    engine.delete_face(target_name)
    
    # Delete any lingering logs
    AttendanceLog.objects.filter(name__iexact=target_name).delete()

    return True, f"Student '{target_name}' and all associated attendance records deleted successfully"

def identify_face_in_image(image_bytes: bytes, class_name: str) -> dict:
    """
    Identifies students from image bytes using LightweightFaceNet Neural Network.
    Compares ONLY against the actual enrolled students in that class.
    """
    sync_disk_and_database()
    valid_students = get_roster_for_class(class_name)
    if not valid_students:
        return {
            "success": False,
            "detected_names": [],
            "matches": [],
            "primary_confidence": 0.0,
            "message": f"No students are enrolled in '{class_name}' yet. Please register a student first.",
            "inference_ms": 0.0,
            "model": "LightweightFaceNet-v2",
            "faces_detected": 0
        }

    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return {
                "success": False,
                "detected_names": [],
                "matches": [],
                "primary_confidence": 0.0,
                "message": "Invalid image format or corrupted buffer",
                "inference_ms": 0.0,
                "model": "LightweightFaceNet-v2",
                "faces_detected": 0
            }

        engine = get_face_engine()
        result = engine.identify_faces(img, valid_roster=valid_students)
        return result

    except Exception as e:
        return {
            "success": False,
            "detected_names": [],
            "matches": [],
            "primary_confidence": 0.0,
            "message": f"Neural Network inference error: {str(e)}",
            "inference_ms": 0.0,
            "model": "LightweightFaceNet-v2",
            "faces_detected": 0
        }
