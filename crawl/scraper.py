"""Web scraping and asset downloading module."""

import json
import logging
import uuid
from pathlib import Path

import httpx

from crawl.utils import fetch_image_data

logger = logging.getLogger(__name__)


async def scrape_url(
    url: str,
    label: str,
    crawler,
    http_client: httpx.AsyncClient,
    output_dir: str | Path,
    semaphore,
    pending_file: Path,
    processed_log: Path,
    file_lock,
) -> None:
    """Crawl a URL, save images and context to disk, and record pending tasks.

    Args:
        url: Webpage URL to crawl.
        label: Target disease label associated with query.
        crawler: AsyncWebCrawler instance.
        http_client: Async httpx client for asset downloading.
        output_dir: Root output directory.
        semaphore: Concurrency semaphore.
        pending_file: Path to pending_images.jsonl.
        processed_log: Path to processed_urls.txt.
        file_lock: Async lock for file writes.
    """
    async with semaphore:
        tasks_to_add = []
        try:
            result = await crawler.arun(url=url)
            if not result.success or not result.media.get("images"):
                return

            for img in result.media["images"]:
                img_url = img.get("src")
                if not img_url or img_url.endswith((".svg", ".gif", ".ico")):
                    continue

                context_text = (img.get("alt") or "") + " " + (img.get("desc") or "")
                context_text = context_text.strip()

                img_bytes, mime_type, base64_image = await fetch_image_data(img_url, http_client)
                if not base64_image:
                    continue

                unique_id = str(uuid.uuid4())[:8]
                img_filename = f"img_{unique_id}.{mime_type.split('/')[-1]}"
                txt_filename = f"text_{unique_id}.txt"

                img_save_path = Path(output_dir) / "images" / label / img_filename
                txt_save_path = Path(output_dir) / "context" / label / txt_filename
                img_save_path.parent.mkdir(parents=True, exist_ok=True)
                txt_save_path.parent.mkdir(parents=True, exist_ok=True)

                with open(img_save_path, "wb") as f:
                    f.write(img_bytes)
                with open(txt_save_path, "w", encoding="utf-8") as f:
                    f.write(f"Source: {url}\nContext: {context_text}")

                task_metadata = {
                    "image_path": str(img_save_path.absolute()),
                    "context": context_text,
                    "source_url": url,
                    "local_txt": str(txt_save_path.absolute()),
                    "base64": base64_image,
                }
                tasks_to_add.append(task_metadata)

            if tasks_to_add:
                async with file_lock:
                    with open(pending_file, "a", encoding="utf-8") as f:
                        for t in tasks_to_add:
                            f.write(json.dumps(t, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
        finally:
            async with file_lock:
                with open(processed_log, "a", encoding="utf-8") as f:
                    f.write(url + "\n")
