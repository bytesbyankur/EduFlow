import os
import time
import glob
import logging
import cv2
import numpy as np
import torch

from .architecture import LightweightFaceNet
from .face_detector import FaceDetector

logger = logging.getLogger(__name__)


class FaceEngine:
    """
    Core Neural Network Face Recognition & Verification Engine.
    Powered by LightweightFaceNet + High-Efficiency Cosine Metric Matching.
    Supports concurrent multi-face recognition for 20+ students in classroom group scans.
    """
    _instance = None

    def __init__(self, known_faces_dir: str = None, weights_path: str = None):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = LightweightFaceNet(embedding_dim=128)
        self.model.to(self.device)
        self.model.eval()

        self.detector = FaceDetector(target_size=(112, 112), min_face_size=(24, 24))
        self.known_faces_dir = known_faces_dir or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "known_faces")
        )
        os.makedirs(self.known_faces_dir, exist_ok=True)

        self.weights_path = weights_path or os.path.join(
            os.path.dirname(__file__), "weights", "lightweight_facenet.pth"
        )
        
        self._load_or_init_weights()

        # In-memory Gallery Cache: { student_name: np.ndarray(128,) }
        self.gallery_embeddings: dict[str, np.ndarray] = {}
        self.cache_file = os.path.join(self.known_faces_dir, "nn_embeddings_cache.npz")
        
        self.match_threshold = 0.48  # Cosine similarity threshold for verification
        self.sync_gallery(force_reload=True)

    @classmethod
    def get_instance(cls, known_faces_dir: str = None):
        if cls._instance is None:
            cls._instance = cls(known_faces_dir=known_faces_dir)
        return cls._instance

    def _load_or_init_weights(self):
        """Loads weights from disk if available."""
        if os.path.exists(self.weights_path):
            try:
                state = torch.load(self.weights_path, map_location=self.device)
                self.model.load_state_dict(state, strict=False)
                return
            except Exception as e:
                logger.warning(f"Could not load weights from {self.weights_path}: {e}")

        os.makedirs(os.path.dirname(self.weights_path), exist_ok=True)
        try:
            torch.save(self.model.state_dict(), self.weights_path)
        except Exception:
            pass

    def compute_embedding(self, face_bgr: np.ndarray) -> np.ndarray:
        """
        Extracts 128D L2-normalized biometric embedding from single cropped BGR face.
        """
        tensor = self.detector.preprocess_face(face_bgr).to(self.device)
        with torch.no_grad():
            emb = self.model(tensor)
            emb_np = emb.cpu().numpy().flatten()
            norm = np.linalg.norm(emb_np)
            if norm > 0:
                emb_np = emb_np / norm
        return emb_np

    def sync_gallery(self, force_reload: bool = False):
        """
        Builds or refreshes the in-memory gallery of student embeddings from known_faces directory.
        Always extracts the primary/prominent face crop for each registered student image.
        If images were deleted from disk, automatically purges them from cache.
        """
        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
        all_image_paths = [
            p for p in glob.glob(os.path.join(self.known_faces_dir, "*"))
            if p.lower().endswith(image_extensions)
        ]

        if not all_image_paths:
            self.gallery_embeddings = {}
            if os.path.exists(self.cache_file):
                try:
                    os.remove(self.cache_file)
                except Exception:
                    pass
            return

        if not force_reload and os.path.exists(self.cache_file):
            try:
                data = np.load(self.cache_file)
                cached_names = data.files
                disk_names = [os.path.splitext(os.path.basename(p))[0].strip() for p in all_image_paths]
                if set(cached_names) == set(disk_names):
                    self.gallery_embeddings = {name: data[name] for name in cached_names}
                    return
            except Exception as e:
                logger.warning(f"Cache load failed, rebuilding: {e}")

        self.gallery_embeddings = {}
        for img_path in all_image_paths:
            student_name = os.path.splitext(os.path.basename(img_path))[0].strip()
            try:
                img = cv2.imread(img_path)
                if img is None:
                    continue
                face_crop = self.detector.get_primary_face(img)
                emb = self.compute_embedding(face_crop)
                self.gallery_embeddings[student_name] = emb
            except Exception as e:
                logger.error(f"Error computing embedding for {student_name}: {e}")

        # Save cache
        if self.gallery_embeddings:
            try:
                np.savez(self.cache_file, **self.gallery_embeddings)
            except Exception as e:
                logger.warning(f"Failed to write embeddings cache: {e}")
        elif os.path.exists(self.cache_file):
            try:
                os.remove(self.cache_file)
            except Exception:
                pass

    def register_face(self, student_name: str, image_bgr: np.ndarray) -> np.ndarray:
        """
        Registers or updates a student face, extracts primary face embedding, and updates gallery.
        """
        face_crop = self.detector.get_primary_face(image_bgr)
        emb = self.compute_embedding(face_crop)

        # Update in-memory gallery
        self.gallery_embeddings[student_name] = emb

        # Save cache
        try:
            np.savez(self.cache_file, **self.gallery_embeddings)
        except Exception:
            pass

        return emb

    def delete_face(self, student_name: str) -> bool:
        """
        Removes a student's face from the known_faces folder, memory gallery, and cache file.
        """
        norm_name = student_name.strip().lower()
        removed = False

        image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
        for p in glob.glob(os.path.join(self.known_faces_dir, "*")):
            if p.lower().endswith(image_extensions):
                base = os.path.splitext(os.path.basename(p))[0].strip().lower()
                if base == norm_name:
                    try:
                        os.remove(p)
                        removed = True
                    except Exception:
                        pass

        # Remove from in-memory dictionary
        to_delete = [k for k in self.gallery_embeddings.keys() if k.strip().lower() == norm_name]
        for k in to_delete:
            del self.gallery_embeddings[k]
            removed = True

        # Resave cache file
        if self.gallery_embeddings:
            try:
                np.savez(self.cache_file, **self.gallery_embeddings)
            except Exception:
                pass
        elif os.path.exists(self.cache_file):
            try:
                os.remove(self.cache_file)
            except Exception:
                pass

        return removed

    def calculate_confidence(self, cosine_similarity: float) -> float:
        """
        Calibrates cosine similarity [-1, 1] into an intuitive 0-100% confidence level.
        """
        sim = float(cosine_similarity)
        th = self.match_threshold

        if sim >= th:
            normalized_progress = (sim - th) / max(0.001, (1.0 - th))
            confidence = 80.0 + 19.5 * (normalized_progress ** 0.7)
        elif sim >= (th - 0.12):
            progress = (sim - (th - 0.12)) / 0.12
            confidence = 60.0 + 19.9 * progress
        else:
            confidence = max(0.0, (sim / max(0.001, (th - 0.12))) * 59.9)

        return round(float(np.clip(confidence, 0.0, 99.8)), 1)

    def identify_faces(
        self,
        image_bgr: np.ndarray,
        valid_roster: list[str] = None
    ) -> dict:
        """
        High-capacity Multi-Face inference pipeline:
        1. Detects all distinct faces with NMS (supports 20+ students simultaneously)
        2. Batches face crops into GPU/CPU tensor
        3. Computes LightweightFaceNet embeddings in one vectorized forward pass
        4. Matches each face against gallery using vectorized cosine similarity matrix
        5. Validates against enrolled class roster and marks all verified students
        """
        start_time = time.perf_counter()
        
        if image_bgr is None or image_bgr.size == 0:
            return {
                "success": False,
                "faces_detected": 0,
                "matches": [],
                "detected_names": [],
                "primary_confidence": 0.0,
                "message": "Invalid or empty image frame",
                "inference_ms": 0.0
            }

        # 1. Face Detection with NMS (no artificial upper limit)
        detected_faces = self.detector.detect_faces(image_bgr)
        num_faces = len(detected_faces)

        if num_faces == 0:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "success": False,
                "faces_detected": 0,
                "matches": [],
                "detected_names": [],
                "primary_confidence": 0.0,
                "message": "No face detected in scanner view",
                "inference_ms": round(elapsed_ms, 2)
            }

        # 2. Sync gallery from disk
        self.sync_gallery(force_reload=False)

        if not self.gallery_embeddings:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "success": False,
                "faces_detected": num_faces,
                "matches": [],
                "detected_names": [],
                "primary_confidence": 0.0,
                "message": "No registered face records found in gallery. Please register a student first.",
                "inference_ms": round(elapsed_ms, 2)
            }

        gallery_names = list(self.gallery_embeddings.keys())
        gallery_matrix = np.array([self.gallery_embeddings[name] for name in gallery_names])  # (N, 128)

        # Prepare normalized roster lookup
        roster_lookup = {}
        if valid_roster is not None:
            for s in valid_roster:
                roster_lookup[s.strip().lower()] = s.strip()
            
            if len(roster_lookup) == 0:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return {
                    "success": False,
                    "faces_detected": num_faces,
                    "matches": [],
                    "detected_names": [],
                    "primary_confidence": 0.0,
                    "message": "No students are enrolled in this course roster",
                    "inference_ms": round(elapsed_ms, 2)
                }

        # 3. Vectorized Batch Embedding Extraction for ALL detected faces
        face_crops = [f['crop_bgr'] for f in detected_faces]
        batch_tensor = self.detector.preprocess_batch_faces(face_crops).to(self.device)
        
        with torch.no_grad():
            batch_emb = self.model(batch_tensor).cpu().numpy()  # (K, 128)

        # 4. Vectorized Matrix Multiplication: (K, 128) x (128, N) = (K, N)
        similarity_matrix = np.dot(batch_emb, gallery_matrix.T)

        matches = []
        verified_names = []
        highest_conf = 0.0
        used_identities = set()

        for i, face in enumerate(detected_faces):
            similarities = similarity_matrix[i]  # (N,)
            sorted_indices = np.argsort(-similarities)

            # Prioritize enrolled candidates in class roster
            best_idx = None
            for candidate_idx in sorted_indices:
                candidate_name = gallery_names[int(candidate_idx)]
                candidate_lower = candidate_name.strip().lower()
                if candidate_name not in used_identities:
                    if valid_roster is None or candidate_lower in roster_lookup:
                        best_idx = int(candidate_idx)
                        break

            # Fallback to any other non-assigned registered face
            if best_idx is None:
                for candidate_idx in sorted_indices:
                    candidate_name = gallery_names[int(candidate_idx)]
                    if candidate_name not in used_identities:
                        best_idx = int(candidate_idx)
                        break
            if best_idx is None:
                best_idx = int(sorted_indices[0])

            best_sim = float(similarities[best_idx])
            best_name = gallery_names[best_idx]
            used_identities.add(best_name)

            confidence = self.calculate_confidence(best_sim)

            # Check enrollment and threshold
            is_enrolled = True
            matched_official_name = best_name
            if valid_roster is not None:
                matched_official_name = roster_lookup.get(best_name.strip().lower(), None)
                is_enrolled = matched_official_name is not None

            is_verified = (best_sim >= self.match_threshold) and is_enrolled

            if is_verified:
                status_str = "Verified"
            elif not is_enrolled:
                status_str = "Not Enrolled in Class"
            else:
                status_str = f"Low Confidence ({confidence}%)"

            match_info = {
                "name": matched_official_name or best_name,
                "raw_name": best_name,
                "confidence": confidence,
                "similarity": round(best_sim, 4),
                "is_verified": is_verified,
                "is_enrolled": is_enrolled,
                "bounding_box": face['box'],
                "status": status_str
            }
            matches.append(match_info)

            if is_verified:
                if match_info["name"] not in verified_names:
                    verified_names.append(match_info["name"])
                if confidence > highest_conf:
                    highest_conf = confidence
            elif confidence > highest_conf:
                highest_conf = confidence

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        if verified_names:
            msg = f"Verified: {', '.join(verified_names)} ({highest_conf}% confidence)"
            success = True
        elif matches and not any(m['is_enrolled'] for m in matches):
            msg = f"Faces recognized, but students are not enrolled in this course"
            success = False
        else:
            msg = "Faces not recognized in this class roster / Low similarity"
            success = False

        return {
            "success": success,
            "faces_detected": num_faces,
            "matches": matches,
            "detected_names": verified_names,
            "primary_confidence": highest_conf if success else (matches[0]['confidence'] if matches else 0.0),
            "message": msg,
            "model": "LightweightFaceNet-v2 (MobileNetV3-SE CNN Multi-Face)",
            "inference_ms": round(elapsed_ms, 2)
        }
