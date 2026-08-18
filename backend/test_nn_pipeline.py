import os
import sys
import glob
import django
import cv2
import numpy as np

# Setup Django Environment
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eduflow.settings')
django.setup()

from attendance.nn.architecture import LightweightFaceNet
from attendance.nn.face_detector import FaceDetector
from attendance.nn.engine import FaceEngine
from attendance.services import identify_face_in_image, get_face_engine, enroll_student_in_class
from attendance.models import Student, Course, CourseEnrollment, AttendanceLog

def test_pipeline():
    print("=" * 60)
    print("  Testing EduFlow Dynamic Lightweight NN Pipeline")
    print("=" * 60)

    # 1. Test Architecture
    model = LightweightFaceNet(embedding_dim=128)
    param_count = model.get_parameter_count()
    print(f"[1/5] LightweightFaceNet initialized. Parameter Count: {param_count:,}")
    assert 500_000 < param_count < 3_000_000, "Parameter count outside expected range"

    # 2. Test Face Detector
    detector = FaceDetector(target_size=(112, 112))
    known_dir = os.path.join(os.path.dirname(__file__), "known_faces")
    
    # Check for available images in known_faces or synthesize one for test
    img_files = [f for f in os.listdir(known_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    if not img_files:
        test_img_path = os.path.join(known_dir, "om.jpg")
        test_img = np.full((300, 300, 3), 180, dtype=np.uint8)
        cv2.rectangle(test_img, (80, 80), (220, 220), (220, 200, 180), -1)
        cv2.imwrite(test_img_path, test_img)
        img_files = ["om.jpg"]

    test_image_name = os.path.splitext(img_files[0])[0]
    test_image_path = os.path.join(known_dir, img_files[0])

    img = cv2.imread(test_image_path)
    faces = detector.detect_faces(img)
    print(f"[2/5] FaceDetector processed {img_files[0]} (Detected: {len(faces)} face region(s))")

    # 3. Test Embedding Extraction & Normalization
    engine = FaceEngine.get_instance(known_faces_dir=known_dir)
    engine.sync_gallery(force_reload=True)
    print(f"[3/5] FaceEngine Gallery Synced with {len(engine.gallery_embeddings)} student faces:")
    for name, emb in engine.gallery_embeddings.items():
        norm = np.linalg.norm(emb)
        print(f"      - {name}: embedding shape {emb.shape}, L2-norm: {norm:.4f}")
        assert np.isclose(norm, 1.0, atol=1e-3), f"Embedding for {name} is not L2-normalized"

    # 4. Enroll test student in DB for testing
    course, _ = Course.objects.get_or_create(name="Advanced Neural Networks")
    student, _ = Student.objects.get_or_create(
        name=test_image_name,
        defaults={'roll_number': 'REG-2025-001', 'password': 'password123'}
    )
    CourseEnrollment.objects.get_or_create(student=student, course=course)

    # 5. Test Face Identification & Confidence Scoring
    print(f"[4/5] Testing Face Recognition on '{test_image_name}'...")
    with open(test_image_path, "rb") as f:
        image_bytes = f.read()

    res = identify_face_in_image(image_bytes, class_name="Advanced Neural Networks")
    print(f"      Result Status: {res.get('success')}")
    print(f"      Detected Names: {res.get('detected_names')}")
    print(f"      Confidence Score: {res.get('primary_confidence')}%")
    print(f"      Inference Latency: {res.get('inference_ms')} ms")
    print(f"      Message: {res.get('message')}")

    assert res.get("success") is True, f"Recognition failed: {res.get('message')}"
    assert test_image_name in res.get("detected_names"), f"{test_image_name} not detected"
    assert res.get("primary_confidence") >= 80.0, "Confidence score too low for exact match"

    # 6. Test Cross-Class Rejection when not enrolled
    print("[5/5] Testing Cross-Class Rejection (Scanning for 'Ethics in AI' where not enrolled)...")
    res_ethics = identify_face_in_image(image_bytes, class_name="Ethics in AI")
    print(f"      Ethics in AI check (Should be False) - Success: {res_ethics.get('success')}")
    assert res_ethics.get("success") is False, "Should not verify student for class where they are not enrolled"

    print("\n" + "=" * 60)
    print("  ALL NEURAL NETWORK PIPELINE TESTS PASSED! 🎉")
    print("=" * 60)

if __name__ == "__main__":
    test_pipeline()
