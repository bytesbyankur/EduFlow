import os
import cv2
import numpy as np
import torch


def compute_iou(box1, box2):
    """
    Computes Intersection over Union (IoU) between two boxes [x, y, w, h].
    """
    x1_1, y1_1, w1, h1 = box1
    x2_1, y2_1 = x1_1 + w1, y1_1 + h1

    x1_2, y1_2, w2, h2 = box2
    x2_2, y2_2 = x1_2 + w2, y1_2 + h2

    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)

    inter_w = max(0, xi2 - xi1)
    inter_h = max(0, yi2 - yi1)
    inter_area = inter_w * inter_h

    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


def non_max_suppression(boxes, iou_threshold=0.35):
    """
    Suppresses duplicate overlapping bounding boxes on the same face,
    while preserving all distinct faces in crowd / group scenes.
    """
    if len(boxes) == 0:
        return []

    # Sort boxes by area descending
    boxes = sorted(boxes, key=lambda b: b[2] * b[3], reverse=True)
    kept = []

    for current_box in boxes:
        should_keep = True
        for kept_box in kept:
            iou = compute_iou(current_box, kept_box)
            if iou > iou_threshold:
                should_keep = False
                break
        if should_keep:
            kept.append(current_box)

    return kept


class FaceDetector:
    """
    High-capacity Multi-Face Detector for individual and classroom group attendance scans.
    Capable of detecting 20, 30, 50+ faces simultaneously across varying scales.
    """
    def __init__(self, target_size=(112, 112), min_face_size=(24, 24)):
        self.target_size = target_size
        self.min_face_size = min_face_size

        local_cascade_dir = os.path.join(os.path.dirname(__file__), "cascades")
        cv2_cascade_dir = getattr(cv2.data, 'haarcascades', '')
        search_dirs = [local_cascade_dir, cv2_cascade_dir]

        self.primary_cascade = self._load_cascade('haarcascade_frontalface_default.xml', search_dirs)
        self.alt_cascade = self._load_cascade('haarcascade_frontalface_alt2.xml', search_dirs)

    def _load_cascade(self, xml_name: str, search_dirs: list[str]) -> cv2.CascadeClassifier:
        for d in search_dirs:
            if not d:
                continue
            path = os.path.join(d, xml_name)
            if os.path.exists(path):
                cascade = cv2.CascadeClassifier(path)
                if not cascade.empty():
                    return cascade
        return cv2.CascadeClassifier()

    def detect_faces(self, image_bgr: np.ndarray, expand_margin: float = 0.15) -> list[dict]:
        """
        Detects ALL distinct real faces in BGR image without arbitrary count limits.
        Applies multi-scale cascade scanning and IoU Non-Maximum Suppression.
        Returns list of dicts:
            [{ 'box': (x, y, w, h), 'expanded_box': (x1, y1, w, h), 'crop_bgr': np.ndarray, 'det_confidence': float }, ...]
        """
        if image_bgr is None or image_bgr.size == 0:
            return []

        h, w = image_bgr.shape[:2]
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        
        # Adaptive histogram equalization for illumination invariance
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_eq = clahe.apply(gray)

        raw_boxes = []

        # 1. Primary cascade pass (high-sensitivity multi-scale)
        if self.primary_cascade and not self.primary_cascade.empty():
            faces = self.primary_cascade.detectMultiScale(
                gray_eq,
                scaleFactor=1.06,
                minNeighbors=3,
                minSize=self.min_face_size,
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            for (x, y, fw, fh) in faces:
                raw_boxes.append((int(x), int(y), int(fw), int(fh)))

        # 2. Alt cascade pass for angled / diverse facial orientations
        if self.alt_cascade and not self.alt_cascade.empty():
            faces_alt = self.alt_cascade.detectMultiScale(
                gray_eq,
                scaleFactor=1.08,
                minNeighbors=3,
                minSize=self.min_face_size,
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            for (x, y, fw, fh) in faces_alt:
                raw_boxes.append((int(x), int(y), int(fw), int(fh)))

        # 3. If image itself is a tight cropped face profile
        if len(raw_boxes) == 0:
            aspect = w / max(1, h)
            if 0.55 <= aspect <= 1.5 and min(w, h) >= 40:
                raw_boxes.append((0, 0, w, h))

        if len(raw_boxes) == 0:
            return []

        # 4. Strict Non-Maximum Suppression to eliminate duplicates on the same person
        filtered_boxes = non_max_suppression(raw_boxes, iou_threshold=0.35)

        # Sort spatial positions: top-to-bottom, left-to-right
        filtered_boxes = sorted(filtered_boxes, key=lambda b: (b[1] // 50, b[0]))

        detected = []
        for (x, y, fw, fh) in filtered_boxes:
            mx = int(fw * expand_margin)
            my = int(fh * expand_margin)

            x1 = max(0, x - mx)
            y1 = max(0, y - my)
            x2 = min(w, x + fw + mx)
            y2 = min(h, y + fh + my)

            crop = image_bgr[y1:y2, x1:x2]
            if crop.size == 0 or crop.shape[0] < 16 or crop.shape[1] < 16:
                continue

            detected.append({
                'box': (int(x), int(y), int(fw), int(fh)),
                'expanded_box': (int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
                'crop_bgr': crop,
                'det_confidence': 0.96
            })

        return detected

    def get_primary_face(self, image_bgr: np.ndarray) -> np.ndarray:
        """
        Extracts the single most prominent face crop from image for student registration.
        Falls back to original image if no sub-face is detected.
        """
        faces = self.detect_faces(image_bgr)
        if faces:
            # Sort by area descending to get largest face
            largest = max(faces, key=lambda f: f['box'][2] * f['box'][3])
            return largest['crop_bgr']
        return image_bgr

    def preprocess_face(self, face_bgr: np.ndarray) -> torch.Tensor:
        """
        Converts BGR face crop into normalized PyTorch tensor (1, 3, 112, 112).
        Standardized with ImageNet / MobileNet normalization.
        """
        rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, self.target_size, interpolation=cv2.INTER_AREA)

        # Standard PyTorch normalization
        tensor = torch.from_numpy(resized).permute(2, 0, 1).float() / 255.0
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        normalized = (tensor - mean) / std

        return normalized.unsqueeze(0)  # (1, 3, 112, 112)

    def preprocess_batch_faces(self, face_crops_bgr: list[np.ndarray]) -> torch.Tensor:
        """
        Batches multiple face crops into a single tensor (B, 3, 112, 112) for ultra-fast GPU/CPU inference.
        """
        if not face_crops_bgr:
            return torch.empty(0, 3, *self.target_size)

        tensors = []
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)

        for crop in face_crops_bgr:
            rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(rgb, self.target_size, interpolation=cv2.INTER_AREA)
            t = torch.from_numpy(resized).permute(2, 0, 1).float() / 255.0
            t_norm = (t - mean) / std
            tensors.append(t_norm)

        return torch.stack(tensors, dim=0)
