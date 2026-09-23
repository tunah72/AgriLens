"""Unified data collection, web scraping, and VLM annotation pipeline."""

import asyncio
import json
import sys
from pathlib import Path

import httpx
from crawl4ai import AsyncWebCrawler
from openai import AsyncOpenAI
from tqdm.asyncio import tqdm

# Ensure project root in sys.path when running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crawl.args import parse_args  # noqa: E402
from crawl.classifier import classify_task  # noqa: E402
from crawl.config import CROP_CLASSES, CROP_SEARCH_STRATEGIES  # noqa: E402
from crawl.scraper import scrape_url  # noqa: E402
from crawl.search import generate_target_urls  # noqa: E402
from crawl.utils import convert_jsonl_to_json  # noqa: E402


async def run_crop_pipeline(crop: str, args) -> None:
    """Execute scraping and classification pipeline for a single crop.

    Args:
        crop: Target crop ('coffee' or 'rice').
        args: Parsed command-line arguments.
    """
    classes = CROP_CLASSES[crop]
    search_strategy = CROP_SEARCH_STRATEGIES[crop]

    output_dir = Path(args.output_dir) / crop
    output_dir.mkdir(parents=True, exist_ok=True)

    pending_file = output_dir / "pending_images.jsonl"
    processed_log = output_dir / "processed_urls.txt"
    final_file = Path(args.import_file)
    if final_file.suffix == ".jsonl":
        final_file = final_file.parent / f"{final_file.stem}_{crop}.jsonl"

    print(f"\n{'=' * 60}")
    print(f"Starting Data Pipeline for Crop: {crop.upper()}")
    print(f"Classes: {', '.join(classes)}")
    print(f"Output Directory: {output_dir}")
    print(f"{'=' * 60}\n")

    if args.dry_run:
        print(f"[DRY-RUN] Simulating pipeline execution for '{crop}'...")
        total_queries = sum(len(q) for q in search_strategy.values())
        print(f"[DRY-RUN] Configured {len(search_strategy)} disease categories with {total_queries} search queries.")
        for label, queries in search_strategy.items():
            print(f"  - [{label}]: {len(queries)} queries (e.g., '{queries[0]}')")
        print(f"[DRY-RUN] Output JSONL would be: {final_file}")
        print(f"[DRY-RUN] Completed dry-run for '{crop}'. No network requests made.")
        return

    file_lock = asyncio.Lock()

    # Step 1: Discover URLs & Web Scraping
    print("\n[Step 1/2] Discovering target URLs and scraping web pages...")
    processed_urls = set()
    if processed_log.exists():
        processed_urls = set(processed_log.read_text(encoding="utf-8").splitlines())

    all_urls = generate_target_urls(args, search_strategy)
    urls_to_process = {u: label for u, label in all_urls.items() if u not in processed_urls}

    if urls_to_process:
        print(f"Scraping {len(urls_to_process)} new URLs (concurrency: {args.max_concurrent_scrapes})...")
        semaphore = asyncio.Semaphore(args.max_concurrent_scrapes)
        async with AsyncWebCrawler(verbose=False) as crawler:
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                tasks = [
                    scrape_url(
                        url=u,
                        label=label,
                        crawler=crawler,
                        http_client=http_client,
                        output_dir=output_dir,
                        semaphore=semaphore,
                        pending_file=pending_file,
                        processed_log=processed_log,
                        file_lock=file_lock,
                    )
                    for u, label in urls_to_process.items()
                ]
                for f in tqdm.as_completed(tasks, desc=f"Scraping [{crop}]", total=len(tasks)):
                    await f
    else:
        print("No new URLs to scrape.")

    # Step 2: VLM Classification & Pre-labeling
    print("\n[Step 2/2] VLM Classification & Pre-labeling...")
    if not pending_file.exists():
        print("No pending images found. Skipping classification.")
        return

    processed_images = set()
    if final_file.exists():
        with open(final_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        record = json.loads(line)
                        processed_images.add(record.get("data", {}).get("image"))
                    except json.JSONDecodeError:
                        pass

    pending_tasks = []
    with open(pending_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                task = json.loads(line)
                if task.get("image_path") not in processed_images:
                    pending_tasks.append(task)

    if pending_tasks:
        print(f"Classifying {len(pending_tasks)} images (concurrency: {args.max_concurrent_ai})...")
        ai_client = None if args.mock_ai else AsyncOpenAI(base_url=args.base_url, api_key=args.api_key)
        ai_semaphore = asyncio.Semaphore(args.max_concurrent_ai)

        tasks = [
            classify_task(
                task_data=task,
                ai_client=ai_client,
                crop=crop,
                classes=classes,
                semaphore=ai_semaphore,
                final_file=final_file,
                file_lock=file_lock,
                mock=args.mock_ai,
            )
            for task in pending_tasks
        ]
        for f in tqdm.as_completed(tasks, desc=f"Classifying [{crop}]", total=len(tasks)):
            await f

        pending_file.unlink(missing_ok=True)
    else:
        print("All pending images have already been classified.")

    print(f"\nPipeline Complete for [{crop}]! Data saved to {final_file}")
    json_export = final_file.parent / f"{final_file.stem}.json"
    convert_jsonl_to_json(final_file, json_export)


async def main_pipeline(args) -> None:
    """Orchestrate data crawling and annotation across selected crops."""
    crops_to_run = ["coffee", "rice"] if args.crop == "all" else [args.crop]

    for crop in crops_to_run:
        await run_crop_pipeline(crop, args)


if __name__ == "__main__":
    cli_args = parse_args()
    asyncio.run(main_pipeline(cli_args))
