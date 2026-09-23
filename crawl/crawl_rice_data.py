"""Backward-compatible entry point for rice leaf disease data crawler."""

import asyncio
import sys
from pathlib import Path

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crawl.args import parse_args  # noqa: E402
from crawl.pipeline import main_pipeline  # noqa: E402

if __name__ == "__main__":
    args = parse_args()
    args.crop = "rice"
    asyncio.run(main_pipeline(args))
