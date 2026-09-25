"""
Domain Guard Service - Out-of-Distribution (OOD) and Foliage Validation.
Validates whether an uploaded image contains a plausible agricultural leaf specimen
before or during model inference to prevent spurious predictions on documents,
certificates, human faces, or non-plant objects.
"""

from dataclasses import dataclass
import cv2
import numpy as np


@dataclass
class DomainCheckResult:
    is_valid_leaf: bool
    reason: str | None = None
    reason_en: str | None = None
    plant_ratio: float = 0.0
    is_document: bool = False

class DomainGuard:
    """Pre-inference and post-inference sanity checks for leaf images."""

    @staticmethod
    def check_image(image_bytes: bytes) -> DomainCheckResult:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return DomainCheckResult(
                is_valid_leaf=True,
                reason=None,
            )

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # 1. Document / Paper text check (e.g. certificates, invoices, books):
        # Characterized by high white/light background, low overall saturation, and dense text strokes
        white_mask = gray > 210
        white_ratio = float(white_mask.mean())
        dark_mask = gray < 100
        dark_ratio = float(dark_mask.mean())
        mean_sat = float(hsv[:, :, 1].mean())

        # Check if the image layout matches printed/scanned document or certificate
        is_document = white_ratio > 0.65 and mean_sat < 45.0 and 0.008 < dark_ratio < 0.35
        if is_document:
            return DomainCheckResult(
                is_valid_leaf=False,
                is_document=True,
                reason="Hình ảnh có đặc điểm của tài liệu, văn bản hoặc giấy tờ, không phải lá cây lúa hoặc cà phê.",
                reason_en="Image characteristics match a document, text, or paper sheet, not a rice or coffee leaf.",
            )

        # 2. Plant foliage / chlorophyll / necrotic tissue check:
        # Green hue: [25, 95], Saturation >= 25, Value >= 25
        green_mask = (
            (hsv[:, :, 0] >= 25)
            & (hsv[:, :, 0] <= 95)
            & (hsv[:, :, 1] >= 25)
            & (hsv[:, :, 2] >= 25)
        )
        # Necrotic / yellow-brown lesion hue: [10, 25], Saturation >= 25, Value >= 25
        brown_mask = (
            (hsv[:, :, 0] >= 10)
            & (hsv[:, :, 0] < 25)
            & (hsv[:, :, 1] >= 25)
            & (hsv[:, :, 2] >= 25)
        )
        plant_mask = green_mask | brown_mask
        plant_ratio = float(plant_mask.mean())

        # If plant tissue accounts for less than 5% of the total frame, it is out of domain
        if plant_ratio < 0.05:
            return DomainCheckResult(
                is_valid_leaf=False,
                plant_ratio=plant_ratio,
                reason="Không phát hiện đủ mô thực vật hoặc phiến lá cây trong ảnh (tỷ lệ mô lá < 5%).",
                reason_en="Insufficient plant tissue or foliage detected in the image (foliage ratio < 5%).",
            )

        return DomainCheckResult(
            is_valid_leaf=True,
            plant_ratio=plant_ratio,
            is_document=False,
        )

    @staticmethod
    def filter_spurious_detections(
        detections: list[dict],
        min_individual_area_pct: float = 0.3,
        min_total_area_pct: float = 0.5,
    ) -> list[dict]:
        """
        Filter out tiny artifact / noise detections that lack agronomic significance.
        Spurious detections on non-leaf textures typically occupy < 0.3% of the image.
        """
        if not detections:
            return []

        # Filter individual detections that are tiny speckles
        valid_dets = [
            d for d in detections if d.get("area_pct", 0.0) >= min_individual_area_pct
        ]

        # If the combined lesion area is negligible, discard as spurious noise
        total_area = sum(d.get("area_pct", 0.0) for d in valid_dets)
        if total_area < min_total_area_pct:
            return []

        return valid_dets
