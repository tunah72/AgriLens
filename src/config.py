"""Centralized configuration for dataset classes, folder mappings, and visual palettes."""

# Reproducibility
RANDOM_SEED: int = 42

# Disease class definitions
RICE_CLASSES: list[str] = ["BrownSpot", "Healthy", "Hispa", "LeafBlast"]
COFFEE_CLASSES: list[str] = ["LeafMiner", "PowderyMildew", "Rust", "AlgalLeafSpot"]

# Folder-name -> display-name mappings
RICE_FOLDER: dict[str, str] = {cls: cls for cls in RICE_CLASSES}
COFFEE_FOLDER: dict[str, str] = {name: str(i) for i, name in enumerate(COFFEE_CLASSES)}

# Visualization color palettes
PALETTE_RICE: list[str] = ["#D95F02", "#1B9E77", "#7570B3", "#E7298A"]
PALETTE_COFFEE: list[str] = ["#A6761D", "#E6AB02", "#66A61E", "#E7298A"]
