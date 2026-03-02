"""Score image quality to determine which duplicate to keep."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

# Higher score = preferred format
FORMAT_PRIORITY = {
    '.raw': 100, '.cr2': 100, '.nef': 100, '.arw': 100,
    '.dng': 100, '.orf': 100, '.rw2': 100,   # RAW formats
    '.tiff': 80, '.tif': 80,
    '.png': 60,
    '.webp': 50,
    '.jpeg': 40, '.jpg': 40,
    '.heic': 40, '.heif': 40,
    '.bmp': 30,
}


@dataclass
class ImageScore:
    path: Path
    resolution: int       # width * height in pixels
    sharpness: float      # Laplacian variance (higher = sharper)
    format_score: int     # based on file extension
    file_size: int        # bytes
    has_exif: bool
    total: float          # weighted composite score


def _measure_sharpness(path: Path) -> float:
    """Laplacian variance — higher means sharper, lower means more blurry."""
    try:
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return 0.0
        return float(cv2.Laplacian(img, cv2.CV_64F).var())
    except Exception:
        return 0.0


def _has_exif(path: Path) -> bool:
    """Return True if the image contains EXIF metadata."""
    try:
        with Image.open(path) as img:
            return bool(getattr(img, '_getexif', lambda: None)())
    except Exception:
        return False


def score_image(path: Path) -> Optional[ImageScore]:
    """
    Compute a composite quality score for an image file.

    Scoring weights (tuned to prioritise human perception):
      - Format type  : RAW beats JPEG by ~60,000 pts (decisive)
      - Resolution   : 12 MP ≈ 12,000,000 pts
      - Sharpness    : multiplied x10 to give it meaningful weight
      - File size    : large files (less compression) get a small bonus
      - EXIF present : small tiebreaker
    """
    try:
        stat = path.stat()
        file_size = stat.st_size

        with Image.open(path) as img:
            w, h = img.size

        resolution = w * h
        sharpness = _measure_sharpness(path)
        format_score = FORMAT_PRIORITY.get(path.suffix.lower(), 20)
        exif = _has_exif(path)

        total = (
            format_score * 1_000           # format is king
            + resolution                   # raw pixel count
            + sharpness * 10              # blur penalty
            + file_size * 0.001           # mild size bonus
            + (5_000 if exif else 0)      # tiebreaker for metadata
        )

        return ImageScore(
            path=path,
            resolution=resolution,
            sharpness=sharpness,
            format_score=format_score,
            file_size=file_size,
            has_exif=exif,
            total=total,
        )
    except Exception:
        return None
