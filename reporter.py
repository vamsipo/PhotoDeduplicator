"""Generate CSV reports and terminal summaries."""

import csv
from pathlib import Path
from typing import List

from deduplicator import Decision


def generate_report(decisions: List[Decision], report_path: Path):
    """Write a CSV with every keep/move decision and the scores that drove it."""
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "action", "file_path", "resolution_px", "sharpness",
            "format", "file_size_bytes", "has_exif", "quality_score", "group_winner",
        ])

        for decision in decisions:
            ws = decision.winner_score
            writer.writerow([
                "keep",
                str(decision.winner),
                ws.resolution,
                f"{ws.sharpness:.2f}",
                decision.winner.suffix.lower(),
                ws.file_size,
                ws.has_exif,
                f"{ws.total:.2f}",
                str(decision.winner),
            ])

            for dup_path, dup_score in zip(decision.duplicates, decision.duplicate_scores):
                action = "moved" if decision.moved else "would_move"
                writer.writerow([
                    action,
                    str(dup_path),
                    dup_score.resolution,
                    f"{dup_score.sharpness:.2f}",
                    dup_path.suffix.lower(),
                    dup_score.file_size,
                    dup_score.has_exif,
                    f"{dup_score.total:.2f}",
                    str(decision.winner),
                ])


def print_summary(decisions: List[Decision], dry_run: bool = False):
    """Print a human-readable summary to stdout."""
    total_groups = len(decisions)
    total_dupes = sum(len(d.duplicates) for d in decisions)
    total_bytes = sum(s.file_size for d in decisions for s in d.duplicate_scores)

    verb = "Would move" if dry_run else "Moved"

    print("\n" + "=" * 56)
    print("  SUMMARY")
    print("=" * 56)
    print(f"  Duplicate groups found  : {total_groups}")
    print(f"  {verb} files           : {total_dupes}")
    print(f"  Space {'to be ' if dry_run else ''}freed        : {_fmt_bytes(total_bytes)}")
    print("=" * 56)

    # Print per-group detail for small runs (avoid flooding the terminal)
    if total_groups <= 30:
        for i, d in enumerate(decisions, 1):
            ws = d.winner_score
            print(
                f"\n  Group {i}  KEEP  {d.winner.name}"
                f"  [{_fmt_res(ws.resolution)} | sharp={ws.sharpness:.0f}"
                f" | {d.winner.suffix.upper()[1:]} | {_fmt_bytes(ws.file_size)}]"
            )
            for dup, score in zip(d.duplicates, d.duplicate_scores):
                tag = "MOVE" if d.moved else "SKIP"
                print(
                    f"           {tag}  {dup.name}"
                    f"  [{_fmt_res(score.resolution)} | sharp={score.sharpness:.0f}"
                    f" | {dup.suffix.upper()[1:]} | {_fmt_bytes(score.file_size)}]"
                )
    else:
        print(f"\n  (Per-group detail suppressed for {total_groups} groups — see CSV report)")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _fmt_res(px: int) -> str:
    if px >= 1_000_000:
        return f"{px / 1_000_000:.1f} MP"
    return f"{px:,} px"
