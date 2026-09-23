"""COCO annotation parser and DataFrame extraction helpers."""

import json
from collections.abc import Callable
from pathlib import Path

import pandas as pd


def load_coco(path: Path) -> dict:
    """Load a COCO-format annotation JSON file.

    Args:
        path: Path to the .json annotation file.

    Returns:
        Parsed COCO dictionary containing keys: info, images, annotations, categories.
    """
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_image_df(coco: dict, label_fn: Callable[[str], str]) -> pd.DataFrame:
    """Build a per-image DataFrame from a COCO dictionary.

    Args:
        coco: Parsed COCO annotation dictionary.
        label_fn: Function that maps file_name -> class label string.

    Returns:
        DataFrame with columns: image_id, file_name, width, height, label, aspect_ratio.
    """
    rows = []
    for img in coco.get("images", []):
        rows.append(
            {
                "image_id": img["id"],
                "file_name": img["file_name"],
                "width": img["width"],
                "height": img["height"],
                "label": label_fn(img["file_name"]),
                "aspect_ratio": img["width"] / img["height"] if img["height"] else 1.0,
            }
        )
    return pd.DataFrame(rows)


def build_ann_df(coco: dict, cat_map: dict) -> pd.DataFrame:
    """Build a per-annotation DataFrame from a COCO dictionary.

    Args:
        coco: Parsed COCO annotation dictionary.
        cat_map: Mapping of category_id -> display_name.

    Returns:
        DataFrame with columns: ann_id, image_id, category_id, class_name, area,
        bbox_w, bbox_h, bbox_area.
    """
    rows = []
    for ann in coco.get("annotations", []):
        bbox = ann.get("bbox", [0, 0, 0, 0])
        rows.append(
            {
                "ann_id": ann["id"],
                "image_id": ann["image_id"],
                "category_id": ann["category_id"],
                "class_name": cat_map.get(ann["category_id"], "unknown"),
                "area": ann.get("area", 0),
                "bbox_w": bbox[2],
                "bbox_h": bbox[3],
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df["bbox_area"] = df["bbox_w"] * df["bbox_h"]
    else:
        df["bbox_area"] = pd.Series(dtype=float)
    return df
