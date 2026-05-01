from __future__ import annotations

# Force UTF-8 output on Windows consoles to avoid cp1252 encode errors
import sys
import io
if hasattr(sys.stdout, "buffer") and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

"""
validate_dictionary.py
======================
Scans the isl_dataset/ directory to build a live isl_dictionary.json,
then validates every entry:
  - FOUND   : clip file exists and is readable by OpenCV
  - MISSING : clip file does not exist on disk
  - CORRUPT : file exists but OpenCV cannot read a frame from it

Outputs
-------
  isl_dictionary.json           - full discovered dictionary (word -> clip_path)
  isl_dictionary_validated.json - only FOUND (healthy) entries

Run from the signsync/ project root:
    python validate_dictionary.py
"""

import json
from pathlib import Path

# ── resolve paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent        # signsync/
DATASET_DIR  = SCRIPT_DIR / "isl_dataset"
ALPHA_DIR    = DATASET_DIR / "alphabet"

OUT_FULL      = SCRIPT_DIR / "isl_dictionary.json"
OUT_VALIDATED = SCRIPT_DIR / "isl_dictionary_validated.json"

# ── cv2 import (graceful fallback) ─────────────────────────────────────────────
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    print("[WARN] opencv-python not installed -- CORRUPT check will be skipped.")
    CV2_AVAILABLE = False


# ──────────────────────────────────────────────────────────────────────────────
# Step 1: Build dictionary from filesystem
# ──────────────────────────────────────────────────────────────────────────────

def build_dictionary() -> dict[str, str]:
    """
    Walk isl_dataset/ and return {word: absolute_clip_path}.
    Word-level folders    -> isl_dataset/<word>/<word>_1.mp4
    Alphabet sub-folders  -> isl_dataset/alphabet/<letter>/<letter>_1.mp4
    Numeric folders (1-9) -> isl_dataset/<digit>/<digit>_1.mp4
    """
    dictionary: dict[str, str] = {}

    if not DATASET_DIR.exists():
        print(f"[ERROR] Dataset directory not found: {DATASET_DIR}")
        sys.exit(1)

    for folder in sorted(DATASET_DIR.iterdir()):
        if not folder.is_dir():
            continue

        if folder.name == "alphabet":
            for letter_dir in sorted(folder.iterdir()):
                if not letter_dir.is_dir():
                    continue
                clips = sorted(letter_dir.glob("*.mp4"))
                key = letter_dir.name.lower()
                if clips:
                    dictionary[key] = str(clips[0].resolve())
                else:
                    # Empty folder -- record expected path so it shows as MISSING
                    dictionary[key] = str((letter_dir / f"{letter_dir.name}_1.mp4").resolve())
        else:
            clips = sorted(folder.glob("*.mp4"))
            key = folder.name.lower()          # e.g. "thank_you", "1", "good"
            if clips:
                dictionary[key] = str(clips[0].resolve())
            else:
                # Folder exists but empty -- record expected path
                dictionary[key] = str((folder / f"{folder.name}_1.mp4").resolve())

    return dictionary


# ──────────────────────────────────────────────────────────────────────────────
# Step 2: Validate each entry
# ──────────────────────────────────────────────────────────────────────────────

def validate_clip(clip_path: str) -> str:
    """Returns 'FOUND', 'MISSING', or 'CORRUPT'."""
    p = Path(clip_path)
    if not p.exists():
        return "MISSING"

    if not CV2_AVAILABLE:
        return "FOUND"          # cannot verify further without cv2

    cap = cv2.VideoCapture(str(p))
    if not cap.isOpened():
        cap.release()
        return "CORRUPT"

    ret, _ = cap.read()
    cap.release()
    return "FOUND" if ret else "CORRUPT"


# ──────────────────────────────────────────────────────────────────────────────
# Step 3: Report + write outputs
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 70)
    print("  ISL Dictionary Validator")
    print(f"  Dataset : {DATASET_DIR}")
    print("=" * 70)

    # ── build ──────────────────────────────────────────────────────────────────
    dictionary = build_dictionary()
    print(f"\n[INFO] Discovered {len(dictionary)} entries from filesystem.\n")

    # Save full dictionary (before validation)
    with open(OUT_FULL, "w", encoding="utf-8") as f:
        json.dump(dictionary, f, indent=2, ensure_ascii=False)
    print(f"[INFO] isl_dictionary.json written -> {OUT_FULL}\n")

    # ── validate ───────────────────────────────────────────────────────────────
    results:   dict[str, str] = {}    # key -> status
    validated: dict[str, str] = {}    # key -> clip_path  (healthy only)

    col_w = max(len(k) for k in dictionary) + 2

    for key, clip_path in sorted(dictionary.items()):
        status = validate_clip(clip_path)
        results[key] = status
        label = f"[{status}]"
        print(f"  {key:<{col_w}} {label:<10}  {clip_path}")
        if status == "FOUND":
            validated[key] = clip_path

    # ── summary ────────────────────────────────────────────────────────────────
    found   = [k for k, s in results.items() if s == "FOUND"]
    missing = [k for k, s in results.items() if s == "MISSING"]
    corrupt = [k for k, s in results.items() if s == "CORRUPT"]

    print("\n" + "=" * 70)
    print("  SUMMARY")
    print(f"  Total entries : {len(results)}")
    print(f"  FOUND         : {len(found)}")
    print(f"  MISSING       : {len(missing)}")
    print(f"  CORRUPT       : {len(corrupt)}")
    print("=" * 70)

    if missing:
        print(f"\n[MISSING] {len(missing)} entries have no clip on disk:")
        for k in missing:
            print(f"    - {k:<30}  {dictionary[k]}")

    if corrupt:
        print(f"\n[CORRUPT] {len(corrupt)} clips exist but OpenCV cannot read a frame:")
        for k in corrupt:
            print(f"    - {k:<30}  {dictionary[k]}")

    # ── write validated JSON ───────────────────────────────────────────────────
    with open(OUT_VALIDATED, "w", encoding="utf-8") as f:
        json.dump(validated, f, indent=2, ensure_ascii=False)
    print(f"\n[INFO] isl_dictionary_validated.json written ({len(validated)} entries) -> {OUT_VALIDATED}")

    if not missing and not corrupt:
        print("\n[OK] All clips are present and readable!")
    else:
        print(f"\n[WARN] {len(missing) + len(corrupt)} issue(s) found. "
              "isl_dictionary_validated.json contains only the healthy entries.")


if __name__ == "__main__":
    main()
