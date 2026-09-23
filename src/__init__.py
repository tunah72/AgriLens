"""Canonical utilities for plant disease detection and dataset management."""

from src.config import (
    COFFEE_CLASSES,
    COFFEE_FOLDER,
    PALETTE_COFFEE,
    PALETTE_RICE,
    RANDOM_SEED,
    RICE_CLASSES,
    RICE_FOLDER,
)
from src.paths import find_project_root, get_project_root, setup_logger

__all__ = [
    "RANDOM_SEED",
    "RICE_CLASSES",
    "COFFEE_CLASSES",
    "RICE_FOLDER",
    "COFFEE_FOLDER",
    "PALETTE_RICE",
    "PALETTE_COFFEE",
    "find_project_root",
    "get_project_root",
    "setup_logger",
]
