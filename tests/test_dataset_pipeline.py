"""Unit tests for dataset QA, mask verification, and shared data utilities."""

import json
import random

import numpy as np

from scripts.check_masks import check_coco_masks
from src.coco import build_ann_df, build_image_df, load_coco
from src.config import COFFEE_CLASSES, RICE_CLASSES
from src.reproducibility import set_seed


def test_check_coco_masks_detects_missing_masks(tmp_path):
    """Verify that images with empty segmentations are flagged as missing masks."""
    mock_coco = {
        "images": [
            {"id": 1, "file_name": "leaf_01.jpg"},
            {"id": 2, "file_name": "leaf_02.jpg"},
        ],
        "annotations": [
            {
                "id": 101,
                "image_id": 1,
                "category_id": 1,
                "segmentation": [[10, 10, 20, 10, 20, 20, 10, 20]],
            },
            {
                "id": 102,
                "image_id": 2,
                "category_id": 2,
                "segmentation": [],  # Empty segmentation
            },
        ],
        "categories": [{"id": 1, "name": "Rust"}, {"id": 2, "name": "BrownSpot"}],
    }

    json_path = tmp_path / "annotations.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(mock_coco, f)

    exit_code = check_coco_masks(json_path)
    assert exit_code == 1, "Expected exit code 1 when missing masks are detected"


def test_check_coco_masks_passes_valid_masks(tmp_path):
    """Verify that datasets with complete segmentations return exit code 0."""
    mock_coco = {
        "images": [
            {"id": 1, "file_name": "leaf_01.jpg"},
            {"id": 2, "file_name": "leaf_02.jpg"},
        ],
        "annotations": [
            {
                "id": 101,
                "image_id": 1,
                "category_id": 1,
                "segmentation": [[10, 10, 50, 10, 50, 50, 10, 50]],
            },
            {
                "id": 102,
                "image_id": 2,
                "category_id": 2,
                "segmentation": [[15, 15, 30, 15, 30, 30, 15, 30]],
            },
        ],
        "categories": [{"id": 1, "name": "Healthy"}],
    }

    json_path = tmp_path / "annotations.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(mock_coco, f)

    exit_code = check_coco_masks(json_path)
    assert exit_code == 0, "Expected exit code 0 when all images have masks"


def test_check_coco_masks_handles_missing_file():
    """Verify that non-existent file returns error code 2."""
    exit_code = check_coco_masks("nonexistent_coco_file.json")
    assert exit_code == 2


def test_coco_dataframe_builders(tmp_path):
    """Test load_coco, build_image_df, and build_ann_df functionality."""
    mock_coco = {
        "images": [
            {"id": 1, "file_name": "BrownSpot_001.jpg", "width": 800, "height": 600},
            {"id": 2, "file_name": "Healthy_002.jpg", "width": 1000, "height": 1000},
        ],
        "annotations": [
            {
                "id": 10,
                "image_id": 1,
                "category_id": 1,
                "bbox": [10, 20, 50, 80],
                "area": 4000,
            },
            {
                "id": 11,
                "image_id": 2,
                "category_id": 2,
                "bbox": [5, 5, 20, 20],
                "area": 400,
            },
        ],
        "categories": [
            {"id": 1, "name": "BrownSpot"},
            {"id": 2, "name": "Healthy"},
        ],
    }

    json_path = tmp_path / "coco.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(mock_coco, f)

    loaded = load_coco(json_path)
    assert len(loaded["images"]) == 2

    img_df = build_image_df(loaded, label_fn=lambda fn: fn.split("_")[0])
    assert len(img_df) == 2
    assert "aspect_ratio" in img_df.columns
    assert img_df.loc[0, "label"] == "BrownSpot"
    assert img_df.loc[1, "label"] == "Healthy"

    cat_map = {1: "BrownSpot", 2: "Healthy"}
    ann_df = build_ann_df(loaded, cat_map)
    assert len(ann_df) == 2
    assert "bbox_area" in ann_df.columns
    assert ann_df.loc[0, "class_name"] == "BrownSpot"
    assert ann_df.loc[0, "bbox_area"] == 50 * 80


def test_reproducibility_seed():
    """Verify that set_seed ensures deterministic random sampling."""
    set_seed(12345)
    py_val1 = random.random()
    np_val1 = np.random.rand()

    set_seed(12345)
    py_val2 = random.random()
    np_val2 = np.random.rand()

    assert py_val1 == py_val2
    assert np_val1 == np_val2


def test_notebooks_shared_facades():
    """Verify backward-compatible facades in notebooks/shared match src modules."""
    from notebooks.shared.config import COFFEE_CLASSES as SHARED_COFFEE
    from notebooks.shared.config import RICE_CLASSES as SHARED_RICE
    from notebooks.shared.paths import find_project_root
    from notebooks.shared.reproducibility import set_seed as shared_set_seed

    assert SHARED_RICE == RICE_CLASSES
    assert SHARED_COFFEE == COFFEE_CLASSES
    assert callable(shared_set_seed)
    assert find_project_root().exists()
