"""Utility functions for dataset crawling and image processing."""

import base64
import json
from pathlib import Path

import httpx


def convert_jsonl_to_json(input_file: Path, output_file: Path) -> None:
    """Convert JSON Lines file to standard JSON array format."""
    if not input_file.exists():
        return
    data = []
    with open(input_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Converted {len(data)} items to {output_file}")


async def fetch_image_data(url: str, http_client: httpx.AsyncClient):
    """Download an image and return raw bytes, mime_type, and base64 string.

    Args:
        url: Image source URL.
        http_client: Async HTTP client.

    Returns:
        Tuple of (img_bytes, mime_type, base64_data_url) or (None, None, None) on failure.
    """
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = await http_client.get(url, headers=headers, timeout=15.0, follow_redirects=True)
        response.raise_for_status()
        img_bytes = response.content

        mime_type = "image/jpeg"
        lower_url = url.lower()
        if lower_url.endswith(".png"):
            mime_type = "image/png"
        elif lower_url.endswith(".webp"):
            mime_type = "image/webp"

        b64_string = f"data:{mime_type};base64,{base64.b64encode(img_bytes).decode('utf-8')}"
        return img_bytes, mime_type, b64_string
    except Exception:
        return None, None, None


__all__ = ["convert_jsonl_to_json", "fetch_image_data"]
