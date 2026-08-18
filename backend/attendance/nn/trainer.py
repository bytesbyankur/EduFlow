import os
import glob
import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

from .architecture import LightweightFaceNet
from .face_detector import FaceDetector


class FaceDataset(Dataset):
    """Dataset for training and fine-tuning LightweightFaceNet."""
    def __init__(self, images_dir: str, detector: FaceDetector, augment: bool = True):
        self.detector = detector
        self.augment = augment
        self.samples = []
        self.class_to_idx = {}

        # Scan directory for images
        exts = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
        all_files = [p for p in glob.glob(os.path.join(images_dir, "*")) if p.lower().endswith(exts)]

        classes = sorted(list(set(os.path.splitext(os.path.basename(p))[0] for p in all_files)))
        self.class_to_idx = {c: i for i, c in enumerate(classes)}

        for p in all_files:
            c = os.path.splitext(os.path.basename(p))[0]
            self.samples.append((p, self.class_to_idx[c]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        img = cv2.imread(img_path)
        if img is None:
            # Create a blank fallback image
            img = np.zeros((112, 112, 3), dtype=np.uint8)

        faces = self.detector.detect_faces(img)
        face_crop = faces[0]['crop_bgr'] if faces else img

        if self.augment:
            # Random horizontal flip
            if np.random.rand() > 0.5:
                face_crop = cv2.flip(face_crop, 1)
            # Slight brightness perturbation
            gamma = np.random.uniform(0.85, 1.15)
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            face_crop = cv2.LUT(face_crop, table)

        tensor = self.detector.preprocess_face(face_crop).squeeze(0)  # (3, 112, 112)
        return tensor, torch.tensor(label, dtype=torch.long)


def train_or_finetune_model(
    known_faces_dir: str,
    epochs: int = 15,
    lr: float = 1e-3,
    output_weights_path: str = None
) -> dict:
    """
    Trains / fine-tunes the LightweightFaceNet on registered student faces
    using Cross-Entropy with cosine metric representations.
    """
    detector = FaceDetector(target_size=(112, 112))
    dataset = FaceDataset(known_faces_dir, detector, augment=True)
    num_classes = len(dataset.class_to_idx)

    if num_classes < 2:
        return {"status": "skipped", "message": "Need at least 2 registered classes to train"}

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = LightweightFaceNet(embedding_dim=128, num_classes=num_classes).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    loader = DataLoader(dataset, batch_size=min(8, len(dataset)), shuffle=True)

    model.train()
    history = []

    for epoch in range(epochs):
        epoch_loss = 0.0
        correct = 0
        total = 0

        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()

            norm_emb, logits = model(images, return_logits=True)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item() * images.size(0)
            preds = logits.argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)

        acc = (correct / max(1, total)) * 100.0
        avg_loss = epoch_loss / max(1, total)
        history.append({"epoch": epoch + 1, "loss": round(avg_loss, 4), "accuracy": round(acc, 2)})

    if output_weights_path is None:
        output_weights_path = os.path.join(
            os.path.dirname(__file__), "weights", "lightweight_facenet.pth"
        )
    os.makedirs(os.path.dirname(output_weights_path), exist_ok=True)
    torch.save(model.state_dict(), output_weights_path)

    return {
        "status": "success",
        "num_classes": num_classes,
        "classes": list(dataset.class_to_idx.keys()),
        "final_accuracy": history[-1]["accuracy"],
        "history": history,
        "weights_saved_to": output_weights_path
    }
