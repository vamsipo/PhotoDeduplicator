"""Group duplicate images and resolve which copy to keep."""

import shutil
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import imagehash
import numpy as np
from tqdm import tqdm

from quality import ImageScore, score_image


@dataclass
class Decision:
    winner: Path
    duplicates: List[Path]
    winner_score: ImageScore
    duplicate_scores: List[ImageScore]
    moved: bool  # False during dry-run


# ---------------------------------------------------------------------------
# Union-Find (disjoint set) for grouping near-duplicate images
# ---------------------------------------------------------------------------

class _UnionFind:
    def __init__(self):
        self._parent: Dict[Path, Path] = {}

    def find(self, x: Path) -> Path:
        if x not in self._parent:
            self._parent[x] = x
        if self._parent[x] != x:
            self._parent[x] = self.find(self._parent[x])
        return self._parent[x]

    def union(self, x: Path, y: Path):
        px, py = self.find(x), self.find(y)
        if px != py:
            self._parent[px] = py

    def get_groups(self) -> List[List[Path]]:
        groups: Dict[Path, List[Path]] = defaultdict(list)
        for path in self._parent:
            groups[self.find(path)].append(path)
        return list(groups.values())


# ---------------------------------------------------------------------------
# Duplicate grouping
# ---------------------------------------------------------------------------

def find_duplicate_groups(
    hash_dict: Dict[Path, imagehash.ImageHash],
    threshold: int = 10,
) -> List[List[Path]]:
    """
    Return lists of paths whose perceptual hashes are within `threshold`
    hamming distance of each other.

    Uses a vectorised numpy inner loop so it stays fast for large collections
    (< 1 second per 10 k images on typical hardware).
    """
    paths = list(hash_dict.keys())
    n = len(paths)

    if n == 0:
        return []

    # Each pHash is an 8x8 bool grid → flatten to (n, 64) uint8 array
    raw = np.array(
        [hash_dict[p].hash.flatten().astype(np.uint8) for p in paths]
    )  # shape (n, 64)

    uf = _UnionFind()
    for p in paths:          # register every path so singletons appear in groups
        uf.find(p)

    for i in tqdm(range(n - 1), desc="Grouping", unit="img"):
        # Vectorised XOR + sum gives hamming distances to all j > i at once
        distances = (raw[i] ^ raw[i + 1:]).sum(axis=1)
        for j_offset in np.where(distances <= threshold)[0]:
            uf.union(paths[i], paths[i + 1 + int(j_offset)])

    return uf.get_groups()


# ---------------------------------------------------------------------------
# Quality resolution & file moving
# ---------------------------------------------------------------------------

def _safe_move(src: Path, dst_dir: Path) -> Path:
    """Move src into dst_dir, appending a counter suffix on name collisions."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / src.name
    stem, suffix = src.stem, src.suffix
    counter = 1
    while dst.exists():
        dst = dst_dir / f"{stem}_dup{counter}{suffix}"
        counter += 1
    shutil.move(str(src), str(dst))
    return dst


def resolve_groups(
    groups: List[List[Path]],
    duplicates_dir: Path,
    dry_run: bool = False,
) -> List[Decision]:
    """
    For each duplicate group:
      - Score every image
      - Keep the highest-scoring one in place
      - Move (or flag in dry-run) the rest to duplicates_dir
    """
    decisions: List[Decision] = []

    for group in tqdm(groups, desc="Resolving", unit="group"):
        scored = [(p, score_image(p)) for p in group]
        valid = [(p, s) for p, s in scored if s is not None]

        if len(valid) < 2:
            continue  # couldn't score enough images to make a decision

        # Best quality first
        valid.sort(key=lambda x: x[1].total, reverse=True)

        winner_path, winner_score = valid[0]
        losers = valid[1:]

        if not dry_run:
            for loser_path, _ in losers:
                # Preserve the immediate parent folder name for traceability
                dest_subdir = duplicates_dir / loser_path.parent.name
                _safe_move(loser_path, dest_subdir)
                # Move any sidecar files with the same stem (e.g. RAW alongside JPG)
                for sidecar in loser_path.parent.glob(f"{loser_path.stem}.*"):
                    if sidecar != loser_path and sidecar.is_file():
                        _safe_move(sidecar, dest_subdir)

        decisions.append(Decision(
            winner=winner_path,
            duplicates=[p for p, _ in losers],
            winner_score=winner_score,
            duplicate_scores=[s for _, s in losers],
            moved=not dry_run,
        ))

    return decisions
