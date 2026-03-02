# Photo Deduplicator — Project Spec

## Overview
A CLI tool that scans a folder for duplicate (or near-duplicate) photos, keeps the best-quality
copy in place, and moves lower-quality duplicates to a separate folder. Outputs a CSV report of
every keep/move decision with quality metrics.

---

## Requirements

### Functional
- Recursively scan a source directory for image files
- Detect **exact** and **near-duplicate** photos using perceptual hashing (pHash)
- Compare images by a configurable Hamming-distance **threshold** (default: 10, 0 = exact only)
- For each duplicate group, automatically choose the **best-quality** copy to keep
- Move lower-quality duplicates to a configurable **duplicates folder** (default: `<source>/duplicates/`)
- Support a **dry-run** mode — preview decisions without moving any files
- Generate a **CSV report** of every decision (file path, resolution, sharpness, format, size, EXIF, score)
- Print a **terminal summary** (groups found, files moved, space freed)

### Image Formats Supported
JPEG, PNG, TIFF, BMP, WebP, HEIC/HEIF, RAW (CR2, NEF, ARW, DNG, ORF, RW2)

### Quality Scoring (higher = better)
| Factor         | Weight / notes                              |
|----------------|---------------------------------------------|
| Format type    | RAW=100k, TIFF=80k, PNG=60k, JPEG=40k pts  |
| Resolution     | width × height (raw pixel count)            |
| Sharpness      | Laplacian variance × 10                     |
| File size      | size_bytes × 0.001 (compression tiebreaker) |
| EXIF present   | +5 000 pts tiebreaker                       |

### CLI Interface
```
python main.py --source <dir> [--duplicates-dir <dir>] [--threshold <int>] [--dry-run] [--report <path>]
```

---

## Architecture

```
main.py          — CLI entry point, orchestrates the 4-step pipeline
scanner.py       — Recursively finds image files (glob + extension filter)
hasher.py        — Computes pHash per image (Pillow + imagehash)
deduplicator.py  — Union-Find grouping + quality resolution + file moving
quality.py       — Composite quality score (resolution, sharpness, format, size, EXIF)
reporter.py      — CSV report writer + terminal summary printer
requirements.txt — Pillow, imagehash, opencv-python, tqdm, numpy
```

### Pipeline (4 steps)
1. **Scan** — `scan_images()` returns sorted list of image Paths, excluding duplicates dir
2. **Hash** — `compute_hashes()` returns `{Path: pHash}` dict, skips unreadable files
3. **Group** — `find_duplicate_groups()` uses Union-Find + vectorised NumPy XOR to find near-duplicates in O(n²) with fast inner loop
4. **Resolve** — `resolve_groups()` scores each image, keeps winner in place, moves losers

---

## Implementation Plan

### Phase 1 — Core CLI (DONE)
- [x] Image scanner with extension filter and exclude-dir support
- [x] Perceptual hashing with pHash (imagehash library)
- [x] Union-Find grouping with NumPy-vectorised hamming distance
- [x] Quality scorer (resolution + sharpness + format + file size + EXIF)
- [x] File mover with collision-safe naming (`_dup1`, `_dup2` suffix)
- [x] CSV reporter + terminal summary
- [x] CLI with argparse (`--source`, `--duplicates-dir`, `--threshold`, `--dry-run`, `--report`)

### Phase 2 — To Be Planned
> **Session was interrupted here.** Original plan beyond Phase 1 is not known.
> Re-state any additional requirements to continue.

Possible next steps (to confirm with user):
- [ ] GUI / web interface
- [ ] Undo/restore — move duplicates back from the duplicates folder
- [ ] Parallel hashing for large libraries (concurrent.futures)
- [ ] Video deduplication support
- [ ] Progress persistence / resume for very large scans
- [ ] Unit tests

---

## Progress Log

| Date       | What was done                                              |
|------------|------------------------------------------------------------|
| 2026-03-01 | Full Phase 1 implemented: scanner, hasher, deduplicator, quality scorer, reporter, CLI |
| 2026-03-01 | spec.md created; GitHub remote setup in progress           |

---

## Dependencies
```
Pillow>=10.0.0
imagehash>=4.3.1
opencv-python>=4.8.0
tqdm>=4.66.0
numpy>=1.24.0
```

## Running
```bash
pip install -r requirements.txt

# Dry run (safe preview)
python main.py --source "C:/Photos" --dry-run

# Move duplicates
python main.py --source "C:/Photos"

# Exact duplicates only
python main.py --source "C:/Photos" --threshold 0

# Custom duplicates folder
python main.py --source "C:/Photos" --duplicates-dir "D:/PhotoDuplicates"
```
