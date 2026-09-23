"""Visualization and image-analysis utilities for exploratory data analysis."""

import random
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

_VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def setup_plot_style() -> None:
    """Apply the project-wide Matplotlib / Seaborn style."""
    import seaborn as sns

    sns.set_theme(style="whitegrid", palette="muted")
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "axes.titlesize": 14,
            "axes.labelsize": 12,
            "axes.titleweight": "bold",
            "font.family": "DejaVu Sans",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def sample_color_stats(
    data_dir: Path,
    classes: list[str],
    folder_map: dict[str, str],
    n: int = 50,
    seed: int = 42,
) -> pd.DataFrame:
    """Sample images per class and compute perceptual brightness + RGB statistics.

    Brightness uses ITU-R BT.601 luminance:
        L = 0.299 * R + 0.587 * G + 0.114 * B

    Args:
        data_dir: Directory containing one sub-folder per class.
        classes: Ordered list of display class names.
        folder_map: Mapping of display_name -> folder_name.
        n: Number of images to sample per class.
        seed: Random seed for reproducible sampling.

    Returns:
        DataFrame with columns: class, brightness, contrast, r_mean, g_mean, b_mean.
    """
    rng = random.Random(seed)
    rows = []
    for cls in classes:
        folder = folder_map.get(cls, cls)
        target_dir = data_dir / folder
        if not target_dir.exists():
            continue
        files = [f for f in target_dir.iterdir() if f.suffix.lower() in _VALID_EXTS]
        sample = rng.sample(files, min(n, len(files)))
        for fpath in sample:
            try:
                arr = np.array(Image.open(fpath).convert("RGB"), dtype=np.float32)
                R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
                lum = 0.299 * R + 0.587 * G + 0.114 * B
                rows.append(
                    {
                        "class": cls,
                        "brightness": float(lum.mean()),
                        "contrast": float(lum.std()),
                        "r_mean": float(R.mean()),
                        "g_mean": float(G.mean()),
                        "b_mean": float(B.mean()),
                    }
                )
            except Exception:
                continue
    return pd.DataFrame(rows)


def show_sample_grid(
    data_dir: Path,
    classes: list[str],
    folder_map: dict[str, str],
    palette: list[str],
    title: str,
    n_col: int = 4,
    seed: int = 42,
) -> None:
    """Display a grid of sample images: one row per class, n_col images per row.

    Args:
        data_dir: Directory containing one sub-folder per class.
        classes: Ordered list of display class names.
        folder_map: Mapping of display_name -> folder_name.
        palette: Hex colors per class for labels.
        title: Figure super-title.
        n_col: Number of sample images per class.
        seed: Random seed for reproducible sampling.
    """
    rng = random.Random(seed)
    n_rows = len(classes)
    fig, axes = plt.subplots(n_rows, n_col, figsize=(n_col * 4, n_rows * 3.2))

    if n_rows == 1:
        axes = axes[np.newaxis, :]

    fig.suptitle(title, fontsize=15, fontweight="bold", y=1.01)

    for row, (cls, color) in enumerate(zip(classes, palette)):
        folder = folder_map.get(cls, cls)
        target_dir = data_dir / folder
        files = [f for f in target_dir.iterdir() if f.suffix.lower() in _VALID_EXTS] if target_dir.exists() else []
        sample = rng.sample(files, min(n_col, len(files)))

        for col in range(n_col):
            ax = axes[row, col]
            if col < len(sample):
                ax.imshow(Image.open(sample[col]).convert("RGB"))
            else:
                ax.set_facecolor("#f0f0f0")
            ax.axis("off")
            if col == 0:
                ax.set_title(cls, fontsize=10, fontweight="bold", color=color, loc="left", pad=4)
            if row == 0:
                axes[row, col].set_title(f"Sample {col + 1}", fontsize=10, pad=4)

    plt.tight_layout()
    plt.show()


def compute_mean_histogram(
    data_dir: Path,
    cls: str,
    folder_map: dict[str, str],
    n: int = 40,
    seed: int = 42,
) -> dict[str, np.ndarray]:
    """Compute mean normalised RGB histograms over n sample images.

    Args:
        data_dir: Directory containing one sub-folder per class.
        cls: Display class name.
        folder_map: Mapping of display_name -> folder_name.
        n: Number of images to sample.
        seed: Random seed.

    Returns:
        Dict mapping "R", "G", "B" channels to normalized 256-bin histograms.
    """
    rng = random.Random(seed)
    folder = folder_map.get(cls, cls)
    target_dir = data_dir / folder
    files = [f for f in target_dir.iterdir() if f.suffix.lower() in _VALID_EXTS] if target_dir.exists() else []
    sample = rng.sample(files, min(n, len(files)))
    hists = {ch: np.zeros(256) for ch in ["R", "G", "B"]}
    count = 0
    for fpath in sample:
        try:
            arr = np.array(Image.open(fpath).convert("RGB"))
            for idx, ch in enumerate(["R", "G", "B"]):
                h = np.bincount(arr[:, :, idx].flatten(), minlength=256).astype(float)
                hists[ch] += h / (h.sum() or 1)
            count += 1
        except Exception:
            continue
    denom = count or 1
    return {ch: v / denom for ch, v in hists.items()}
