"""Command line argument parser for crawler and annotation pipeline."""

import argparse


def parse_args():
    """Parse CLI arguments for leaf disease crawler and classification pipeline."""
    parser = argparse.ArgumentParser(description="Agricultural leaf disease crawler & VLM annotation pipeline.")
    parser.add_argument(
        "--crop",
        type=str,
        choices=["coffee", "rice", "all"],
        default="all",
        help="Target crop for data collection (coffee, rice, or all)",
    )
    parser.add_argument(
        "--search-engine",
        type=str,
        choices=["ddg", "serper"],
        default="ddg",
        help="Search engine to use (ddg or serper)",
    )
    parser.add_argument("--serper-api-key", type=str, default="", help="API key for Serper.dev")
    parser.add_argument(
        "--output-dir", type=str, default="datasets/raw/scraped_data", help="Output directory for assets"
    )
    parser.add_argument(
        "--base-url", type=str, default="http://localhost:8080/v1", help="Base URL for local VLM server"
    )
    parser.add_argument("--api-key", type=str, default="sk-no-key-needed", help="API key for VLM endpoint")
    parser.add_argument(
        "--import-file",
        type=str,
        default="datasets/raw/label_studio_import.jsonl",
        help="Path for output JSONL file",
    )
    parser.add_argument("--max_concurrent_scrapes", type=int, default=5, help="Maximum concurrent page scrapers")
    parser.add_argument("--max_concurrent_ai", type=int, default=4, help="Maximum concurrent AI classification calls")
    parser.add_argument("--dry-run", action="store_true", help="Simulate crawl pipeline without network requests")
    parser.add_argument("--mock-ai", action="store_true", help="Use deterministic mock predictions without calling VLM")

    return parser.parse_args()
