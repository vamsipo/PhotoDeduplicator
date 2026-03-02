"""Compute perceptual hashes for images."""

from pathlib import Path
from typing import Dict, List, Optional

import imagehash
from PIL import Image
from tqdm import tqdm


def compute_hash(path: Path) -> Optional[imagehash.ImageHash]:
    """Compute perceptual hash (pHash) for a single image. Returns None on error."""
    try:
        with Image.open(path) as img:
            img = img.convert("RGB")
            return imagehash.phash(img)
    except Exception:
        return None


def compute_hashes(paths: List[Path]) -> Dict[Path, imagehash.ImageHash]:
    """Compute perceptual hashes for all images, showing a progress bar."""
    result: Dict[Path, imagehash.ImageHash] = {}
    failed = 0
    for path in tqdm(paths, desc="Hashing", unit="img"):
        h = compute_hash(path)
        if h is not None:
            result[path] = h
        else:
            failed += 1
    if failed:
        print(f"  Warning: {failed} image(s) could not be read and were skipped.")
    return result
