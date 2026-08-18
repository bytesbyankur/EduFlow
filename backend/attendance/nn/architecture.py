import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models


class LightweightFaceNet(nn.Module):
    """
    Ultra-lightweight, high-efficiency Neural Network for Face Embedding & Verification.
    Powered by MobileNetV3-Small deep feature extractor + metric projection head.
    - Input: (B, 3, 112, 112) normalized face crop tensor
    - Output: (B, embedding_dim) L2-normalized 128D/256D biometric feature vector
    - Total parameters: ~1.5M (fast CPU inference < 15ms)
    """
    def __init__(self, embedding_dim=128, num_classes=None):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.num_classes = num_classes

        # Load MobileNetV3-Small backbone with pretrained weights
        try:
            weights = models.MobileNet_V3_Small_Weights.DEFAULT
            base = models.mobilenet_v3_small(weights=weights)
        except Exception:
            base = models.mobilenet_v3_small(weights=None)

        self.backbone = base.features
        self.pool = nn.AdaptiveAvgPool2d((1, 1))

        # Deep Metric Projection Head
        self.embedding_head = nn.Sequential(
            nn.Flatten(),
            nn.Linear(576, 256),
            nn.BatchNorm1d(256),
            nn.Hardswish(inplace=True),
            nn.Linear(256, embedding_dim, bias=False),
            nn.BatchNorm1d(embedding_dim)
        )

        if num_classes is not None and num_classes > 0:
            self.classifier = nn.Linear(embedding_dim, num_classes, bias=False)
        else:
            self.classifier = None

        self._initialize_head()

    def _initialize_head(self):
        for m in self.embedding_head.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.BatchNorm1d):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def forward(self, x, return_logits=False):
        """
        Forward pass.
        Returns:
            normalized_embeddings: (B, embedding_dim) unit vector on hypersphere
            (optional) logits: (B, num_classes)
        """
        features = self.pool(self.backbone(x))
        raw_emb = self.embedding_head(features)
        norm_emb = F.normalize(raw_emb, p=2, dim=1)

        if return_logits and self.classifier is not None:
            logits = self.classifier(norm_emb)
            return norm_emb, logits

        return norm_emb

    def get_parameter_count(self):
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
