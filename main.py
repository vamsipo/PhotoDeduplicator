#!/usr/bin/env python3
"""
Photo Deduplicator
------------------
Scans a folder for duplicate photos, keeps the best-quality copy in place,
and moves lower-quality duplicates to a separate folder.

Usage
-----
  # Safe preview — nothing is moved
  python main.py --source "C:/Photos" --dry-run

  # Move duplicates to default location (<source>/duplicates/)
  python main.py --source "C:/Photos"

  # Custom duplicates folder
  python main.py --source "C:/Photos" --duplicates-dir "D:/PhotoDuplicates"

  # Exact duplicates only (threshold 0)
  python main.py --source "C:/Photos" --threshold 0 --dry-run
"""

import argparse
import sys
from pathlib import Path

from deduplicator import find_duplicate_groups, resolve_groups
from hasher import compute_hashes
from reporter import generate_report, print_summary
from scanner import scan_images


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Find duplicate photos, keep the best quality, "
            "move the rest to a duplicates folder."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--source", required=True, type=Path,
        help="Directory to scan for photos (searched recursively).",
    )
    parser.add_argument(
        "--duplicates-dir", type=Path, default=None,
        help="Where to move duplicates (default: <source>/duplicates/).",
    )
    parser.add_argument(
        "--threshold", type=int, default=10,
        help=(
            "Perceptual hash hamming-distance threshold. "
            "0 = exact duplicates only, 10 = near-duplicates (default), "
            "higher = more aggressive matching."
        ),
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview decisions without moving any files.",
    )
    parser.add_argument(
        "--report", type=Path, default=None,
        help="Path for the CSV report (default: <source>/dedup_report.csv).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    source_dir: Path = args.source.resolve()
    if not source_dir.is_dir():
        print(f"ERROR: '{source_dir}' is not a directory or does not exist.")
        sys.exit(1)

    duplicates_dir: Path = (
        args.duplicates_dir.resolve() if args.duplicates_dir
        else source_dir / "duplicates"
    )
    report_path: Path = args.report or source_dir / "dedup_report.csv"

    # ------------------------------------------------------------------
    if args.dry_run:
        print("*** DRY RUN — no files will be moved ***\n")

    print(f"Source      : {source_dir}")
    print(f"Duplicates  : {duplicates_dir}")
    print(f"Threshold   : {args.threshold}  (hamming distance)\n")

    # 1. Scan
    print("Step 1/4  Scanning for images...")
    image_paths = scan_images(source_dir, exclude_dir=duplicates_dir)
    print(f"          Found {len(image_paths):,} image(s)\n")

    if not image_paths:
        print("No images found. Nothing to do.")
        sys.exit(0)

    # 2. Hash
    print("Step 2/4  Computing perceptual hashes...")
    hash_dict = compute_hashes(image_paths)
    print(f"          Hashed {len(hash_dict):,} image(s)\n")

    # 3. Group
    print(f"Step 3/4  Finding duplicate groups (threshold={args.threshold})...")
    all_groups = find_duplicate_groups(hash_dict, threshold=args.threshold)
    dup_groups = [g for g in all_groups if len(g) >= 2]
    print(f"          Found {len(dup_groups):,} duplicate group(s)\n")

    if not dup_groups:
        print("No duplicates found — your library is already clean!")
        sys.exit(0)

    # 4. Resolve
    print("Step 4/4  Scoring quality and resolving duplicates...")
    decisions = resolve_groups(dup_groups, duplicates_dir, dry_run=args.dry_run)

    # Report
    generate_report(decisions, report_path)
    print_summary(decisions, dry_run=args.dry_run)

    if args.dry_run:
        print(
            f"\nRun without --dry-run to actually move the files listed above."
        )
    print(f"\nCSV report : {report_path}")


if __name__ == "__main__":
    main()
