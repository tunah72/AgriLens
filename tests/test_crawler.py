"""Unit and integration tests for leaf disease crawling and annotation pipeline."""

import argparse
import json

import httpx
import pytest

from crawl.classifier import build_classification_prompt, classify_image
from crawl.config import CROP_CLASSES, CROP_SEARCH_STRATEGIES
from crawl.pipeline import main_pipeline
from crawl.utils import convert_jsonl_to_json, fetch_image_data


def test_crop_config_contains_required_classes():
    """Verify that Coffee and Rice configs contain the expected 4 taxonomy classes."""
    assert "coffee" in CROP_CLASSES
    assert "rice" in CROP_CLASSES

    expected_rice = ["BrownSpot", "Healthy", "Hispa", "LeafBlast"]
    expected_coffee = ["LeafMiner", "PowderyMildew", "Rust", "AlgalLeafSpot"]

    assert sorted(CROP_CLASSES["rice"]) == sorted(expected_rice)
    assert sorted(CROP_CLASSES["coffee"]) == sorted(expected_coffee)


def test_search_strategy_queries_are_non_empty():
    """Verify that all disease categories have non-empty query templates."""
    for crop in ["rice", "coffee"]:
        strategy = CROP_SEARCH_STRATEGIES[crop]
        for label, queries in strategy.items():
            assert len(queries) > 0, f"Crop {crop} label {label} has empty query list"
            for q in queries:
                assert len(q.strip()) > 3, f"Query '{q}' in {crop}/{label} is too short"


@pytest.mark.asyncio
async def test_fetch_image_data_handles_error():
    """Verify that network errors return (None, None, None) safely."""
    async with httpx.AsyncClient() as client:
        # Requesting an invalid local port that immediately fails
        img_bytes, mime, b64 = await fetch_image_data("http://127.0.0.1:59999/nonexistent.jpg", client)
        assert img_bytes is None
        assert mime is None
        assert b64 is None


def test_vlm_classification_prompt_generation():
    """Verify English prompt construction for coffee and rice."""
    rice_prompt = build_classification_prompt("rice", CROP_CLASSES["rice"], "rice field symptoms")
    assert "rice plants" in rice_prompt
    assert "BrownSpot, Healthy, Hispa, LeafBlast" in rice_prompt
    assert '{"prediction": "LabelName"}' in rice_prompt
    coffee_prompt = build_classification_prompt("coffee", CROP_CLASSES["coffee"], "coffee orchard leaf rust")
    assert "coffee plants" in coffee_prompt
    assert "LeafMiner, PowderyMildew, Rust, AlgalLeafSpot" in coffee_prompt


@pytest.mark.asyncio
async def test_classify_image_with_mock():
    """Verify deterministic mock classification for offline execution."""
    prediction = await classify_image(
        crop="coffee",
        classes=CROP_CLASSES["coffee"],
        base64_image="data:image/jpeg;base64,fake",
        context="sample text",
        mock=True,
    )
    assert prediction in CROP_CLASSES["coffee"]


@pytest.mark.asyncio
async def test_crawler_dry_run_pipeline(tmp_path):
    """Verify end-to-end pipeline execution with --dry-run without network calls."""
    args = argparse.Namespace(
        crop="all",
        search_engine="ddg",
        serper_api_key="",
        output_dir=str(tmp_path / "scraped"),
        base_url="http://localhost:8080/v1",
        api_key="sk-test",
        import_file=str(tmp_path / "import.jsonl"),
        max_concurrent_scrapes=2,
        max_concurrent_ai=2,
        dry_run=True,
        mock_ai=True,
    )

    # Must complete cleanly without raising any exceptions
    await main_pipeline(args)


def test_convert_jsonl_to_json(tmp_path):
    """Verify conversion from JSONL records to standard JSON array."""
    jsonl_file = tmp_path / "data.jsonl"
    json_file = tmp_path / "data.json"

    records = [
        {"id": 1, "label": "Healthy"},
        {"id": 2, "label": "BrownSpot"},
    ]
    with open(jsonl_file, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    convert_jsonl_to_json(jsonl_file, json_file)

    assert json_file.exists()
    with open(json_file, encoding="utf-8") as f:
        loaded = json.load(f)
    assert len(loaded) == 2
    assert loaded[0]["label"] == "Healthy"
    assert loaded[1]["label"] == "BrownSpot"
