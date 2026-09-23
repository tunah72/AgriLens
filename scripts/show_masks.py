"""Overlay segmentation masks onto input images for visual QA and inspection."""

import argparse
import json
import os
from pathlib import Path, PurePath

import matplotlib
import numpy as np
from PIL import Image, ImageDraw


def overlay_masks(image: np.ndarray | Image.Image, masks: np.ndarray) -> Image.Image:
    """Composite colored segmentation masks over the base image."""
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)

    image = image.convert("RGBA")

    if hasattr(masks, "cpu"):
        masks = masks.cpu().numpy()

    masks = (255 * masks).astype(np.uint8)

    n_masks = masks.shape[0]
    cmap = matplotlib.colormaps.get_cmap("rainbow").resampled(n_masks)
    colors = [tuple(int(c * 255) for c in cmap(i)[:3]) for i in range(n_masks)]

    for mask, color in zip(masks, colors):
        mask_img = Image.fromarray(mask)
        overlay = Image.new("RGBA", image.size, color + (100,))
        image.paste(overlay, (0, 0), mask_img)

    return image


def _normalize_path(value: str) -> str:
    return str(PurePath(value.replace("\\", "/"))).lower()


def _find_image_entry(images: list[dict], image_path: str) -> dict | None:
    target_path = _normalize_path(image_path)
    target_name = os.path.basename(target_path)

    for img in images:
        entry_file_name = _normalize_path(img.get("file_name", ""))
        if entry_file_name == target_path:
            return img

    for img in images:
        entry_file_name = _normalize_path(img.get("file_name", ""))
        if os.path.basename(entry_file_name) == target_name:
            return img

    return None


def load_coco_masks(json_path: str, image_path: str, image_size: tuple) -> np.ndarray:
    """Parse a COCO JSON file to generate mask arrays for a specific image."""
    with open(json_path, encoding="utf-8") as f:
        coco_data = json.load(f)

    target_image = _find_image_entry(coco_data.get("images", []), image_path)
    if not target_image:
        raise ValueError(f"Image '{image_path}' not found in COCO file: {json_path}")

    image_id = target_image["id"]
    annotations = [ann for ann in coco_data.get("annotations", []) if ann.get("image_id") == image_id]

    masks = []
    width, height = image_size
    for ann in annotations:
        seg = ann.get("segmentation")
        if not seg:
            continue

        mask_img = Image.new("L", (width, height), 0)
        draw = ImageDraw.Draw(mask_img)

        if isinstance(seg, list):
            for polygon in seg:
                if len(polygon) >= 6:
                    draw.polygon(polygon, outline=1, fill=1)
        elif isinstance(seg, dict) and seg.get("counts"):
            try:
                from pycocotools import mask as mask_util

                binary_mask = mask_util.decode(seg)
                masks.append(binary_mask)
                continue
            except ImportError:
                print("Warning: RLE masks require 'pycocotools' for decoding.")
                continue

        masks.append(np.array(mask_img, dtype=np.uint8))

    if not masks:
        raise ValueError(f"No mask annotations found for '{image_path}'.")

    return np.stack(masks)


def main():
    """CLI entry point for mask visualization."""
    parser = argparse.ArgumentParser(description="Overlay mask annotations onto an image for inspection.")
    parser.add_argument("--image-path", "--image_path", required=True, help="Path to input image file (.jpg, .png)")
    parser.add_argument(
        "--annotation-path", "--annotation_path", required=True, help="Path to annotation file (.json or .npy)"
    )
    args = parser.parse_args()

    image_path = Path(args.image_path)
    ann_path = Path(args.annotation_path)

    if not image_path.exists():
        print(f"Error: Image not found at '{image_path}'")
        return

    if not ann_path.exists():
        print(f"Error: Annotation file not found at '{ann_path}'")
        return

    try:
        print(f"Loading image: {image_path}")
        image = Image.open(image_path)

        if ann_path.suffix.lower() == ".json":
            print(f"Loading COCO masks from: {ann_path}")
            masks = load_coco_masks(str(ann_path), str(image_path), image.size)
        else:
            print(f"Loading NumPy masks from: {ann_path}")
            masks = np.load(ann_path, allow_pickle=True)

        print(f"Compositing {masks.shape[0]} mask(s)...")
        result_image = overlay_masks(image, masks)

        result_image.convert("RGB").save(args.output)
        print(f"Saved visualization to: {args.output}")

        if not args.no_show:
            result_image.show()

    except Exception as e:
        print(f"Error during mask visualization: {e}")


if __name__ == "__main__":
    main()
