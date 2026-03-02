"""Scan a directory tree for image files."""

from pathlib import Path
from typing import List, Set

IMAGE_EXTENSIONS: Set[str] = {
    '.jpg', '.jpeg', '.png', '.tiff', '.tif',
    '.bmp', '.webp', '.heic', '.heif',
    '.raw', '.cr2', '.nef', '.arw', '.dng', '.orf', '.rw2',
}


def scan_images(source_dir: Path, exclude_dir: Path = None) -> List[Path]:
    """Recursively find all image files under source_dir."""
    images = []
    for path in source_dir.rglob("*"):
        if exclude_dir and _is_relative_to(path, exclude_dir):
            continue
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(path)
    return sorted(images)


def _is_relative_to(path: Path, parent: Path) -> bool:
    """Check if path is inside parent (compatible with Python < 3.9)."""
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
