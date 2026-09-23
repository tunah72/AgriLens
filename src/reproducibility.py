"""Reproducibility utilities for ML pipelines and data processing."""

import os
import random

import numpy as np


def set_seed(seed: int = 42) -> None:
    """Set random seeds for python, random, numpy, and environment.

    Args:
        seed: Integer seed value.
    """
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
