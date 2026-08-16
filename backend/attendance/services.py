import os
import glob
import cv2
import numpy as np
from django.conf import settings
from deepface import DeepFace
from .models import Student, Course, CourseEnrollment

DEFAULT_CLASS_ROSTERS = {
    "Advanced Neural Networks": ["Taylor Swift", "Rashmika Mandana", "Elon Musk"],
    "Ethics in AI": ["Barack Obama", "Taylor Swift", "Sraddha Kapoor"],
    "Computer Vision 101": ["Rashmika Mandana", "Elon Musk", "Taylor Swift"]
}

def get_known_faces_dir():
    known_dir = getattr(settings, 'KNOWN_FACES_DIR', os.path.join(settings.BASE_DIR, 'known_faces'))
    os.makedirs(known_dir, exist_ok=True)
    return str(known_dir)

def clear_deepface_cache():
    """Removes DeepFace representations .pkl cache files."""
    known_dir = get_known_faces_dir()
    for pkl_file in glob.glob(os.path.join(known_dir, "*.pkl")):
        try:
            os.remove(pkl_file)
        except OSError:
            pass

def get_roster_for_class(class_name: str) -> list[str]:
    """
    Returns the list of student names enrolled in the given class.
    Checks CourseEnrollment database first, falls back to in-memory/defaults if empty.
    """
    course = Course.objects.filter(name=class_name).first()
    if course:
        enrolled = list(CourseEnrollment.objects.filter(course=course).values_list('student__name', flat=True))
        if enrolled:
            return enrolled
    
    # Fallback to default in-memory dictionary
    return DEFAULT_CLASS_ROSTERS.get(class_name, [])

def enroll_student_in_class(student: Student, class_name: str):
    """Enrolls a student in a course in the DB and ensures the course exists."""
    course, _ = Course.objects.get_or_create(name=class_name)
    CourseEnrollment.objects.get_or_create(student=student, course=course)
    
    # Also update in-memory roster if present
    if class_name in DEFAULT_CLASS_ROSTERS:
        if student.name not in DEFAULT_CLASS_ROSTERS[class_name]:
            DEFAULT_CLASS_ROSTERS[class_name].append(student.name)
    else:
        DEFAULT_CLASS_ROSTERS[class_name] = [student.name]

def save_face_image(uploaded_file, name: str) -> str:
    """Saves the student photo to the known_faces directory."""
    known_dir = get_known_faces_dir()
    file_path = os.path.join(known_dir, f"{name}.jpg")
    
    with open(file_path, "wb+") as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
            
    clear_deepface_cache()
    return file_path

def identify_face_in_image(image_bytes: bytes, class_name: str) -> tuple[bool, list[str], str]:
    """
    Identifies students from an image buffer using DeepFace.
    Returns: (is_success, detected_names, message)
    """
    valid_students = get_roster_for_class(class_name)
    if not valid_students:
        return False, [], "No students enrolled in this class"

    known_dir = get_known_faces_dir()
    valid_face_images = [
        f for f in os.listdir(known_dir) 
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]
    if not valid_face_images:
        return False, [], "No face records registered in known_faces directory yet."

    temp_scan_path = os.path.join(settings.BASE_DIR, "temp_scan.jpg")
    
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return False, [], "Invalid image data received"
            
        cv2.imwrite(temp_scan_path, img)

        dfs = DeepFace.find(
            img_path=temp_scan_path,
            db_path=known_dir,
            model_name="VGG-Face",
            detector_backend="mtcnn",
            enforce_detection=False,
            silent=True
        )

        detected_names = []
        for df in dfs:
            if not df.empty:
                for _, row in df.iterrows():
                    path = row['identity']
                    # Extracted filename without extension is student name
                    name = os.path.splitext(os.path.basename(path))[0]
                    
                    # Verify student is registered in this class (case-insensitive)
                    matched_student = next(
                        (s for s in valid_students if s.strip().lower() == name.strip().lower()), 
                        None
                    )
                    if matched_student:
                        if matched_student not in detected_names:
                            detected_names.append(matched_student)
                        break

        if detected_names:
            return True, detected_names, "Success"
        else:
            return False, [], "Student not found in this class roster"

    except Exception as e:
        return False, [], f"Face recognition error: {str(e)}"
