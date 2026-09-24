"""
Verification test suite comparing Original (FP32) vs Quantized (INT8) YOLO26-seg models.

Tests instance segmentation mask decoding, bounding box extraction,
and visual overlay generation on real rice and coffee leaf images.
"""

from pathlib import Path
import pytest
from PIL import Image
import numpy as np

from backend.app.services.inference import InferenceService


FP32_MODEL_PATH = Path("artifacts/yolo26_seg_joint/yolo26n_seg_joint.onnx")
INT8_MODEL_PATH = Path("artifacts/yolo26_seg_joint/yolo26n_seg_joint_int8.onnx")
CLASS_NAMES_PATH = Path("models/class_names.json")

SAMPLE_RICE_IMAGE = Path("artifacts/yolo26_seg_rice/label_qa/rice_0003164.jpg")
SAMPLE_COFFEE_IMAGE = Path("artifacts/yolo26_seg_coffee/label_qa/coffee_0006597.jpg")


@pytest.fixture(scope="module")
def class_names():
    if not CLASS_NAMES_PATH.exists():
        pytest.skip(f"Class names file not found: {CLASS_NAMES_PATH}")
    return InferenceService.load_class_names(str(CLASS_NAMES_PATH))


@pytest.fixture(scope="module")
def fp32_service(class_names):
    if not FP32_MODEL_PATH.exists():
        pytest.skip(f"FP32 model not found: {FP32_MODEL_PATH}")
    return InferenceService(str(FP32_MODEL_PATH), class_names, input_size=1024)


@pytest.fixture(scope="module")
def int8_service(class_names):
    if not INT8_MODEL_PATH.exists():
        pytest.skip(f"INT8 model not found: {INT8_MODEL_PATH}")
    return InferenceService(str(INT8_MODEL_PATH), class_names, input_size=1024)


def test_model_files_exist_and_int8_is_compressed():
    """Verify both ONNX files exist and INT8 achieves substantial size reduction."""
    assert FP32_MODEL_PATH.exists(), f"Missing {FP32_MODEL_PATH}"
    assert INT8_MODEL_PATH.exists(), f"Missing {INT8_MODEL_PATH}"

    fp32_size = FP32_MODEL_PATH.stat().st_size
    int8_size = INT8_MODEL_PATH.stat().st_size

    # Quantized model should be under 40% of FP32 size (>60% reduction)
    compression_ratio = fp32_size / int8_size
    assert compression_ratio > 2.5, f"Expected >2.5x compression, got {compression_ratio:.2f}x"
    assert int8_size < 5 * 1024 * 1024, "INT8 model should be < 5MB"


def test_fp32_segmentation_on_diseased_rice(fp32_service):
    """Verify FP32 model accurately segments leaf blast lesion on rice leaf."""
    assert SAMPLE_RICE_IMAGE.exists(), f"Missing test image: {SAMPLE_RICE_IMAGE}"
    img_bytes = SAMPLE_RICE_IMAGE.read_bytes()

    top_k, detections, annotated_bytes = fp32_service.predict_segmentation(img_bytes)

    # 1. Top-1 prediction must be LeafBlast with high confidence
    top_label, top_conf = top_k[0]
    assert top_label == "LeafBlast"
    assert top_conf > 0.85

    # 2. Detections must contain bounding box and mask polygon
    assert len(detections) >= 1
    det = detections[0]
    assert det["label"] == "LeafBlast"
    assert det["confidence"] > 0.85

    # Bbox coordinates within image bounds (640x640)
    x1, y1, x2, y2 = det["box"]
    assert 0 <= x1 < x2 <= 640
    assert 0 <= y1 < y2 <= 640

    # Mask polygon should be a simplified non-empty contour
    assert det["polygon"] is not None
    assert len(det["polygon"]) >= 3
    for pt in det["polygon"]:
        assert len(pt) == 2
        assert 0 <= pt[0] <= 640
        assert 0 <= pt[1] <= 640

    # Area percentage should be reasonable for this lesion (~10% - 20%)
    assert 5.0 <= det["area_pct"] <= 30.0

    # 3. Annotated image should be valid JPEG bytes
    assert annotated_bytes is not None
    assert annotated_bytes.startswith(b"\xff\xd8")  # JPEG header
    assert len(annotated_bytes) > 20000


def test_int8_segmentation_on_diseased_rice(int8_service):
    """Verify INT8 quantized model retains instance segmentation capabilities on rice leaf."""
    assert SAMPLE_RICE_IMAGE.exists(), f"Missing test image: {SAMPLE_RICE_IMAGE}"
    img_bytes = SAMPLE_RICE_IMAGE.read_bytes()

    top_k, detections, annotated_bytes = int8_service.predict_segmentation(img_bytes)

    top_label, top_conf = top_k[0]
    assert top_label == "LeafBlast"
    assert top_conf > 0.85

    assert len(detections) >= 1
    det = detections[0]
    assert det["label"] == "LeafBlast"
    assert det["confidence"] > 0.85

    x1, y1, x2, y2 = det["box"]
    assert 0 <= x1 < x2 <= 640
    assert 0 <= y1 < y2 <= 640

    assert det["polygon"] is not None
    assert len(det["polygon"]) >= 3

    assert 5.0 <= det["area_pct"] <= 30.0

    assert annotated_bytes is not None
    assert annotated_bytes.startswith(b"\xff\xd8")
    assert len(annotated_bytes) > 20000


def test_fp32_vs_int8_consistency_and_overlap(fp32_service, int8_service):
    """Verify quantitative consistency (label, bounding box IoU, area%) between FP32 and INT8."""
    img_bytes = SAMPLE_RICE_IMAGE.read_bytes()

    top_k_fp32, dets_fp32, _ = fp32_service.predict_segmentation(img_bytes)
    top_k_int8, dets_int8, _ = int8_service.predict_segmentation(img_bytes)

    # Class label consistency
    assert top_k_fp32[0][0] == top_k_int8[0][0] == "LeafBlast"

    # Confidence difference should be small (< 0.1)
    conf_diff = abs(top_k_fp32[0][1] - top_k_int8[0][1])
    assert conf_diff < 0.1, f"Confidence divergence too large: {conf_diff:.4f}"

    # Lesion area percentage comparison
    area_fp32 = dets_fp32[0]["area_pct"]
    area_int8 = dets_int8[0]["area_pct"]
    area_diff = abs(area_fp32 - area_int8)
    assert area_diff < 1.0, f"Area percentage difference too large: {area_diff:.2f}%"

    # Bounding box IoU calculation
    b_fp32 = dets_fp32[0]["box"]
    b_int8 = dets_int8[0]["box"]

    ix1 = max(b_fp32[0], b_int8[0])
    iy1 = max(b_fp32[1], b_int8[1])
    ix2 = min(b_fp32[2], b_int8[2])
    iy2 = min(b_fp32[3], b_int8[3])
    inter_area = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)

    area1 = (b_fp32[2] - b_fp32[0]) * (b_fp32[3] - b_fp32[1])
    area2 = (b_int8[2] - b_int8[0]) * (b_int8[3] - b_int8[1])
    union_area = area1 + area2 - inter_area

    iou = inter_area / union_area if union_area > 0 else 0.0
    assert iou > 0.85, f"Bounding box IoU between FP32 and INT8 is {iou:.3f}, expected > 0.85"


def test_healthy_leaf_yields_no_lesion_detections(fp32_service, int8_service):
    """Verify that a healthy leaf produces no diseased bbox or mask detections on both models."""
    if not SAMPLE_COFFEE_IMAGE.exists():
        pytest.skip(f"Missing sample coffee image: {SAMPLE_COFFEE_IMAGE}")
    img_bytes = SAMPLE_COFFEE_IMAGE.read_bytes()

    # FP32
    top_k_fp32, dets_fp32, ann_fp32 = fp32_service.predict_segmentation(img_bytes)
    assert top_k_fp32[0][0] == "Healthy"
    assert len(dets_fp32) == 0
    assert ann_fp32 is None

    # INT8
    top_k_int8, dets_int8, ann_int8 = int8_service.predict_segmentation(img_bytes)
    assert top_k_int8[0][0] == "Healthy"
    assert len(dets_int8) == 0
    assert ann_int8 is None
