import cv2
import numpy as np
import mediapipe as mp
import threading
import time
import os
import glob
from datetime import datetime
from deepface import DeepFace
from .models import Student, AttendanceLog
from .services import get_known_faces_dir, clear_deepface_cache

class VideoCamera:
    def __init__(self):
        self.video = None
        self.lock = threading.Lock()
        self.current_frame = None
        self.is_recognizing = False
        self.last_detection_time = 0
        self.recognition_cooldown = 1.0  # Rapid recognition cooldown
        self.active_class = "Computer Vision 101"
        self.last_matched_student = None
        self.match_display_until = 0

        # In-memory face embeddings cache: { name: normalized_numpy_vector }
        self.known_embeddings = {}
        self.embeddings_lock = threading.Lock()
        self.embeddings_loaded = False

        # MediaPipe Face Detection
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detector = self.mp_face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.55
        )

        self.is_running = False
        self.thread = None

        # Pre-load embeddings in background thread
        threading.Thread(target=self._refresh_known_embeddings, daemon=True).start()

    def _open_camera(self):
        """Attempts to cleanly open camera device using Linux V4L2 backend, falling back to default."""
        if self.video is not None and self.video.isOpened():
            return True
        try:
            self.video = cv2.VideoCapture(0, cv2.CAP_V4L2)
            if not self.video or not self.video.isOpened():
                self.video = cv2.VideoCapture(0)
            if self.video and self.video.isOpened():
                self.video.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            return self.video is not None and self.video.isOpened()
        except Exception as err:
            print(f"[VideoCamera] Camera open error: {err}")
            return False

    def _refresh_known_embeddings(self):
        """Precomputes normalized face embeddings for all known face photos in memory."""
        try:
            db_dir = get_known_faces_dir()
            if not os.path.exists(db_dir):
                return

            new_embeddings = {}
            for f in os.listdir(db_dir):
                if f.lower().endswith(('.jpg', '.png', '.jpeg')):
                    raw_name = os.path.splitext(f)[0]
                    clean_name = raw_name.replace('_face', '').replace('_', ' ').strip().title()
                    file_path = os.path.join(db_dir, f)
                    
                    try:
                        rep = DeepFace.represent(
                            img_path=file_path,
                            model_name="Facenet",
                            enforce_detection=False
                        )
                        if rep and len(rep) > 0:
                            # Pick largest face to avoid background artifacts
                            best_rep = max(rep, key=lambda r: (r.get('facial_area', {}).get('w', 0) * r.get('facial_area', {}).get('h', 0)) if isinstance(r, dict) else 0)
                            vec = np.array(best_rep['embedding'], dtype=np.float32)
                            norm = np.linalg.norm(vec)
                            if norm > 0:
                                unit_vec = vec / norm
                                if clean_name not in new_embeddings:
                                    new_embeddings[clean_name] = []
                                new_embeddings[clean_name].append(unit_vec)
                    except Exception as e:
                        print(f"[Embedding Error] {clean_name}: {e}")

            with self.embeddings_lock:
                self.known_embeddings = new_embeddings
                self.embeddings_loaded = True
            print(f"[Biometrics Engine] Successfully cached embeddings for {len(new_embeddings)} distinct students.")
        except Exception as err:
            print(f"[Biometrics Engine] Cache refresh error: {err}")

    def start_camera(self):
        """Starts the capture thread if not already running."""
        with self.lock:
            if not self.is_running:
                self.is_running = True
                self.thread = threading.Thread(target=self._capture_loop, daemon=True)
                self.thread.start()

    def stop_camera(self):
        """Cleanly releases /dev/video0 and terminates the capture loop."""
        self.is_running = False
        with self.lock:
            if self.video and self.video.isOpened():
                try:
                    self.video.release()
                except Exception as e:
                    print(f"[VideoCamera] Release error: {e}")
            self.video = None
            self.current_frame = None
            self.is_recognizing = False

    def release(self):
        self.stop_camera()

    def set_active_class(self, class_name):
        self.active_class = class_name
        # Refresh embedding cache when class or students change
        threading.Thread(target=self._refresh_known_embeddings, daemon=True).start()

    def _get_fallback_frame(self, message="Camera Initializing..."):
        """Generates a synthetic high-resolution black image with clear HUD text overlay."""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw tech border
        cv2.rectangle(img, (15, 15), (625, 465), (99, 102, 241), 2)
        cv2.rectangle(img, (20, 20), (620, 80), (30, 41, 59), -1)
        
        # Header text
        cv2.putText(img, "EDUFLOW BIOMETRIC SCANNER", (35, 55), cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 2)
        cv2.putText(img, f"Status: {message}", (35, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (52, 211, 153), 2)
        cv2.putText(img, f"Class: {self.active_class}", (35, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (148, 163, 184), 2)
        cv2.putText(img, "Connecting to webcam hardware (/dev/video0)...", (35, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 116, 139), 1)
        
        # Timestamp
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(img, now_str, (35, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 116, 139), 1)
        
        ret, jpeg = cv2.imencode('.jpg', img)
        return jpeg.tobytes() if ret else None

    def _capture_loop(self):
        consecutive_failures = 0

        while self.is_running:
            if self.video is None or not self.video.isOpened():
                if not self._open_camera():
                    time.sleep(0.5)
                    continue

            success, frame = self.video.read()

            if not success or frame is None:
                consecutive_failures += 1
                if consecutive_failures > 15:
                    if self.video:
                        try:
                            self.video.release()
                        except Exception:
                            pass
                    self.video = None
                    consecutive_failures = 0
                time.sleep(0.05)
                continue

            consecutive_failures = 0
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.face_detector.process(rgb_frame)

            active_matched_name = self.last_matched_student if time.time() < self.match_display_until else None

            # Render High-Contrast Top HUD Banner
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 65), (15, 23, 42), -1)
            cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
            
            # Status Text on Top HUD
            cv2.putText(frame, f"CLASS: {self.active_class}", (20, 26), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
            
            if active_matched_name:
                cv2.putText(frame, f"STATUS: VERIFIED - {active_matched_name.upper()} (ATTENDANCE LOGGED)", (20, 52), cv2.FONT_HERSHEY_DUPLEX, 0.55, (52, 211, 153), 2)
            else:
                cv2.putText(frame, "STATUS: AI BIOMETRICS ACTIVE (SCANNING FACES)", (20, 52), cv2.FONT_HERSHEY_DUPLEX, 0.55, (129, 140, 248), 1)

            if results.detections:
                face_crops = []
                for detection in results.detections:
                    bboxC = detection.location_data.relative_bounding_box
                    x, y = int(bboxC.xmin * w), int(bboxC.ymin * h)
                    bw, bh = int(bboxC.width * w), int(bboxC.height * h)
                    x, y = max(0, x), max(0, y)
                    bw = min(bw, w - x)
                    bh = min(bh, h - y)

                    # Bounding Box
                    box_color = (16, 185, 129) if active_matched_name else (124, 58, 237)
                    cv2.rectangle(frame, (x, y), (x + bw, y + bh), box_color, 2)

                    # Face label badge
                    label_text = f" {active_matched_name} " if active_matched_name else " STUDENT FACE "
                    label_bg = (16, 185, 129) if active_matched_name else (99, 102, 241)
                    badge_y = max(24, y)
                    cv2.rectangle(frame, (x, badge_y - 24), (x + bw, badge_y), label_bg, -1)
                    cv2.putText(frame, label_text, (x + 4, badge_y - 7), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                    face_crop = frame[y:y+bh, x:x+bw]
                    if face_crop.size > 0 and face_crop.shape[0] > 20 and face_crop.shape[1] > 20:
                        face_crops.append(face_crop.copy())

                # Trigger non-blocking multi-face vector recognition
                current_time = time.time()
                if face_crops and not self.is_recognizing and (current_time - self.last_detection_time > self.recognition_cooldown):
                    self.last_detection_time = current_time
                    self.is_recognizing = True
                    threading.Thread(
                        target=self._process_multi_recognition,
                        args=(face_crops, self.active_class),
                        daemon=True
                    ).start()

            with self.lock:
                self.current_frame = frame.copy()

            time.sleep(0.02)  # Smooth 50 FPS

    def _process_multi_recognition(self, face_crops, current_class):
        try:
            if not self.known_embeddings:
                self._refresh_known_embeddings()

            with self.embeddings_lock:
                cached_embs = dict(self.known_embeddings)

            if not cached_embs:
                return

            verified_names = []
            for face_crop in face_crops:
                try:
                    rep = DeepFace.represent(
                        img_path=face_crop,
                        model_name="Facenet",
                        detector_backend="skip",
                        enforce_detection=False
                    )
                    if not rep or len(rep) == 0:
                        continue

                    q_vec = np.array(rep[0]['embedding'], dtype=np.float32)
                    q_norm = np.linalg.norm(q_vec)
                    if q_norm == 0:
                        continue
                    q_unit = q_vec / q_norm

                    best_name = None
                    min_dist = 1.0
                    for name, vecs in cached_embs.items():
                        if isinstance(vecs, list):
                            person_dist = min(float(1.0 - np.dot(q_unit, v)) for v in vecs)
                        else:
                            person_dist = float(1.0 - np.dot(q_unit, vecs))
                        if person_dist < min_dist:
                            min_dist = person_dist
                            best_name = name

                    if min_dist <= 0.38 and best_name and best_name not in verified_names:
                        verified_names.append(best_name)
                        self._record_attendance(best_name, current_class)
                        print(f"[Biometrics Engine] Verified {best_name} (dist: {min_dist:.3f})")
                except Exception as crop_err:
                    print(f"[Biometrics Engine] Face crop error: {crop_err}")

            if verified_names:
                self.last_matched_student = ", ".join(verified_names)
                self.match_display_until = time.time() + 4.0

        except Exception as e:
            print(f"[Biometrics Engine] Recognition error: {e}")
        finally:
            self.is_recognizing = False

    def _record_attendance(self, name, class_name):
        today = datetime.now().strftime("%Y-%m-%d")
        now_time = datetime.now().strftime("%H:%M:%S")

        student = Student.objects.filter(name__iexact=name).first()
        if not student:
            student = Student.objects.filter(roll_number__iexact=name).first()

        actual_name = student.name if student else name
        target_class = class_name or self.active_class or "General"

        log, created = AttendanceLog.objects.get_or_create(
            name=actual_name,
            class_name=target_class,
            date=today,
            defaults={"student": student, "time": now_time}
        )
        if not created and not log.student and student:
            log.student = student
            log.save()
        print(f"[Attendance Logged] {actual_name} in {target_class} ({today} {now_time})")

    def get_jpeg_frame(self):
        """Returns the current JPEG frame, or a fallback HUD frame if initializing."""
        if not self.is_running:
            self.start_camera()

        with self.lock:
            if self.current_frame is None:
                return self._get_fallback_frame("Warming up camera feed...")
            ret, jpeg = cv2.imencode('.jpg', self.current_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                return jpeg.tobytes()
            return self._get_fallback_frame("Encoding frame...")

    def get_frame(self):
        """Alias for get_jpeg_frame."""
        return self.get_jpeg_frame()

# Lazy instance manager
_camera_instance = None

def get_camera_instance():
    global _camera_instance
    if _camera_instance is None:
        _camera_instance = VideoCamera()
    return _camera_instance

class CameraProxy:
    def __getattr__(self, name):
        return getattr(get_camera_instance(), name)

camera_instance = CameraProxy()