================================================================================
  PHOTO DEDUPLICATOR
  Find duplicate photos, keep the best quality, move the rest.
================================================================================

WHAT IT DOES
------------
Scans a folder for duplicate (or near-duplicate) photos. For each group of
duplicates it automatically keeps the highest-quality copy in place and moves
the others to a separate folder. A CSV report is written so you can review
every decision.

Quality is judged by: image resolution, sharpness, file format (RAW beats
JPEG), file size, and whether EXIF metadata is present.

Supported formats: JPEG, PNG, TIFF, BMP, WebP, HEIC/HEIF, RAW (CR2, NEF,
ARW, DNG, ORF, RW2).


REQUIREMENTS
------------
Python 3.8 or later.

Install dependencies (one time):

  pip install -r requirements.txt


USAGE
-----

1. SAFE PREVIEW — see what would happen without moving anything:

   python main.py --source "C:\Photos" --dry-run

2. RUN FOR REAL — move duplicates to <source>\duplicates\:

   python main.py --source "C:\Photos"

3. CUSTOM DUPLICATES FOLDER:

   python main.py --source "C:\Photos" --duplicates-dir "D:\PhotoDuplicates"

4. EXACT DUPLICATES ONLY (pixel-perfect matches, no near-duplicates):

   python main.py --source "C:\Photos" --threshold 0 --dry-run

5. AGGRESSIVE NEAR-DUPLICATE MATCHING (catches more, use with dry-run first):

   python main.py --source "C:\Photos" --threshold 20 --dry-run

6. CUSTOM REPORT PATH:

   python main.py --source "C:\Photos" --report "C:\Reports\dedup.csv"


OPTIONS
-------
  --source          (required) Folder to scan. Searched recursively.
  --duplicates-dir  Where to move duplicates. Default: <source>\duplicates\
  --threshold       Perceptual hash sensitivity. Default: 10.
                      0  = exact duplicates only
                      10 = near-duplicates (recommended)
                      20+ = more aggressive (may produce false positives)
  --dry-run         Preview only. No files are moved.
  --report          Path for the CSV report. Default: <source>\dedup_report.csv


OUTPUT
------
After running you will find:

  <source>\duplicates\     — duplicate files moved here, organised into
                             subfolders matching their original parent folder.

  <source>\dedup_report.csv — one row per file with columns:
    action           keep | moved | would_move (dry-run)
    file_path        full path to the file
    resolution_px    width x height in pixels
    sharpness        Laplacian variance (higher = sharper)
    format           file extension
    file_size_bytes  raw byte size
    has_exif         True / False
    quality_score    composite score used to pick the winner
    group_winner     path of the file kept for this duplicate group

The terminal also prints a summary: groups found, files moved, space freed.


TIPS
----
- Always run with --dry-run first to review decisions before committing.
- The duplicates folder is excluded from scanning, so re-running is safe.
- If a duplicate filename already exists in the destination, a suffix like
  _dup1, _dup2 is added automatically — no files are ever overwritten.
- To recover a moved file, simply move it back from the duplicates folder.


EXAMPLES
--------
Preview duplicates in a holiday photos folder:

  python main.py --source "C:\Users\Pictures\Holiday2024" --dry-run

Clean up, moving duplicates to an external drive:

  python main.py --source "C:\Users\Pictures" \
                 --duplicates-dir "E:\DuplicatePhotos" \
                 --threshold 10

================================================================================
