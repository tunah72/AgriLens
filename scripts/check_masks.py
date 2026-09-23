"""Verify that all images in a COCO annotation dataset contain valid segmentation masks."""

import argparse
import json
import sys
from pathlib import Path


def check_coco_masks(json_path: str | Path, limit: int = 10) -> int:
    """Check a COCO annotation file for images missing segmentation masks.

    Args:
        json_path: Path to the COCO JSON annotation file.
        limit: Maximum number of missing image IDs to display in summary.

    Returns:
        Exit code: 0 if all images have masks, 1 if missing masks found, 2 on file/IO error.
    """
    path = Path(json_path)
    if not path.exists():
        print(f"Error: Annotation file not found at: {path}")
        return 2

    print(f"Validating segmentation masks in: {path}...")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except MemoryError:
        print("Error: Out of memory loading annotation file. Consider using a streaming parser.")
        return 2
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return 2

    images = {img["id"]: img.get("file_name", "unknown") for img in data.get("images", [])}
    annotations = data.get("annotations", [])

    images_with_masks = set()
    for ann in annotations:
        image_id = ann.get("image_id")
        seg = ann.get("segmentation")

        has_mask = False
        if isinstance(seg, list) and len(seg) > 0:
            has_mask = any(len(poly) >= 6 for poly in seg if isinstance(poly, list))
        elif isinstance(seg, dict) and seg.get("counts"):
            has_mask = True

        if has_mask:
            images_with_masks.add(image_id)

    all_image_ids = set(images.keys())
    missing_mask_ids = all_image_ids - images_with_masks

    print("-" * 50)
    print(f"Total images in dataset:        {len(all_image_ids):>6}")
    print(f"Images with valid masks:        {len(images_with_masks):>6}")
    print(f"Images missing masks:           {len(missing_mask_ids):>6}")
    print("-" * 50)

    if missing_mask_ids:
        print(f"\nWarning: Found {len(missing_mask_ids)} image(s) lacking segmentation masks.")
        sorted_missing = sorted(list(missing_mask_ids))
        for img_id in sorted_missing[:limit]:
            print(f"  - ID {img_id}: {images.get(img_id, 'Unknown filename')}")
        if len(missing_mask_ids) > limit:
            print(f"  ... and {len(missing_mask_ids) - limit} more.")
        return 1

    print("\nSuccess: All images have at least one valid segmentation mask.")
    return 0


def main():
    """CLI entry point for mask validation."""
    parser = argparse.ArgumentParser(description="Audit COCO datasets to detect images missing segmentation masks.")
    parser.add_argument(
        "json_path",
        nargs="?",
        default="datasets/final/coffee_leaf_disease/annotations.coco.json",
        help="Path to COCO JSON annotation file",
    )
    parser.add_argument(
        "--json",
        dest="flag_json",
        default=None,
        help="Explicit flag path to COCO JSON annotation file",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of missing IDs to display",
    )
    args = parser.parse_args()

    target = args.flag_json or args.json_path
    exit_code = check_coco_masks(target, limit=args.limit)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
