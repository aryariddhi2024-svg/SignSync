"""
organize_dataset.py
────────────────────────────────────────────────────────────────
Automatically scans the Kaggle ISL dataset folder and copies
every image/video into the correct SignSync isl_dataset/ folder.

Supports the Kaggle dataset structure:
  downloads/archive/Indian/A/  → images or videos of letter A
  downloads/archive/Indian/B/  → images or videos of letter B
  ...
  downloads/archive/Indian/Hello/    → Hello sign
  downloads/archive/Indian/ThankYou/ → Thank You sign
  etc.

If the dataset contains IMAGES (jpg/png) instead of videos,
this script converts them into short MP4 clips automatically.

HOW TO RUN:
  1. Put this file inside your signsync/ folder
  2. Run: python organize_dataset.py
  3. It will ask you where your downloaded dataset is
────────────────────────────────────────────────────────────────
"""

import os, sys, shutil
from pathlib import Path

# ── auto-install dependencies if missing ──────────────────────
def ensure(pkg, import_name=None):
    try:
        __import__(import_name or pkg)
    except ImportError:
        print(f"Installing {pkg}...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

ensure("Pillow", "PIL")
ensure("numpy")
ensure("imageio")

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio

# ─────────────────────────────────────────────────────────────
SIGNSYNC_ROOT = Path(__file__).parent          # signsync/ folder
ISL_DEST      = SIGNSYNC_ROOT / "isl_dataset"  # destination

# Map common Kaggle folder names → SignSync word folder names
NAME_MAP = {
    # Letters (A-Z handled automatically)
    # Common words in Kaggle ISL dataset
    "hello"        : "hello",
    "hi"           : "hello",
    "thankyou"     : "thank_you",
    "thank_you"    : "thank_you",
    "thankuou"     : "thank_you",
    "please"       : "please",
    "sorry"        : "sorry",
    "help"         : "help",
    "yes"          : "yes",
    "no"           : "no",
    "good"         : "good",
    "bad"          : "bad",
    "iloveyou"     : "love",
    "i_love_you"   : "love",
    "love"         : "love",
    "india"        : "india",
    "name"         : "name",
    "friend"       : "friend",
    "family"       : "family",
    "home"         : "home",
    "school"       : "school",
    "water"        : "water",
    "food"         : "food",
    "stop"         : "stop",
    "go"           : "go",
    "come"         : "come",
    "understand"   : "understand",
    "welcome"      : "welcome",
    "happy"        : "happy",
    "sad"          : "sad",
    "namaste"      : "namaste",
    "bye"          : "goodbye",
    "goodbye"      : "goodbye",
    "eat"          : "eat",
    "drink"        : "drink",
    "sleep"        : "sleep",
    "walk"         : "walk",
    "sit"          : "sit",
    "stand"        : "stand",
    "read"         : "read",
    "write"        : "write",
    "listen"       : "listen",
    "speak"        : "speak",
    "know"         : "know",
    "work"         : "work",
    "play"         : "play",
    "teacher"      : "teacher",
    "student"      : "student",
    "doctor"       : "doctor",
    "man"          : "man",
    "woman"        : "woman",
    "child"        : "child",
    "one"          : "one",
    "two"          : "two",
    "three"        : "three",
    "four"         : "four",
    "five"         : "five",
    "six"          : "six",
    "seven"        : "seven",
    "eight"        : "eight",
    "nine"         : "nine",
    "ten"          : "ten",
}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

# ─────────────────────────────────────────────────────────────

def image_to_mp4(image_path: Path, dest_path: Path, duration_frames: int = 15):
    """Convert a single image into a short MP4 clip (15 frames = ~1.2s at 12fps)."""
    try:
        img    = Image.open(image_path).convert("RGB").resize((640, 480))
        frame  = np.array(img)
        frames = [frame] * duration_frames
        imageio.mimwrite(str(dest_path), frames, fps=12, quality=8, macro_block_size=None)
        return True
    except Exception as e:
        print(f"    ⚠  Could not convert {image_path.name}: {e}")
        return False


def normalize_name(folder_name: str) -> str:
    """Convert a folder name to a SignSync key."""
    key = folder_name.lower().strip().replace(" ", "_").replace("-", "_")
    return NAME_MAP.get(key, key)


def is_single_letter(name: str) -> bool:
    return len(name) == 1 and name.isalpha()


def find_dataset_root(start: Path) -> list[Path]:
    """
    Walk *start* and find all leaf folders that contain image/video files.
    Returns list of those leaf folders.
    """
    leaves = []
    for root, dirs, files in os.walk(start):
        r = Path(root)
        has_media = any(
            Path(f).suffix.lower() in IMAGE_EXTS | VIDEO_EXTS for f in files
        )
        if has_media:
            leaves.append(r)
    return leaves


def process_folder(src_folder: Path, label: str, idx: int):
    """Copy/convert files from src_folder into isl_dataset/<label>/"""
    # decide destination
    if is_single_letter(label):
        dest_dir = ISL_DEST / "alphabet" / label.lower()
    else:
        dest_dir = ISL_DEST / label.lower()

    dest_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(src_folder.iterdir())
    copied = 0

    for f in files:
        if not f.is_file():
            continue
        ext = f.suffix.lower()

        if ext in VIDEO_EXTS:
            dest = dest_dir / f"{label.lower()}_{idx + 1}{ext}"
            if not dest.exists():
                shutil.copy2(f, dest)
                copied += 1
            break  # one clip per word is enough

        elif ext in IMAGE_EXTS:
            dest = dest_dir / f"{label.lower()}_{idx + 1}.mp4"
            if not dest.exists():
                if image_to_mp4(f, dest):
                    copied += 1
            break  # one image → one clip

    return copied


# ─────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  SignSync – ISL Dataset Organiser")
    print("=" * 60)
    print()

    # ── ask user for dataset path ─────────────────────────────
    print("Where is your downloaded Kaggle ISL dataset?")
    print("(Paste the full path, e.g.  C:\\Users\\Lenovo\\Downloads\\archive)")
    print()
    raw = input("Dataset path: ").strip().strip('"').strip("'")
    src = Path(raw)

    if not src.exists():
        print(f"\n❌ Path not found: {src}")
        print("   Please check and run again.")
        return

    print(f"\n🔍 Scanning: {src}")
    leaves = find_dataset_root(src)

    if not leaves:
        print("❌ No image or video files found in that folder.")
        print("   Make sure you extracted the ZIP first.")
        return

    print(f"   Found {len(leaves)} sub-folders with media files.\n")

    total_copied = 0
    skipped      = []

    for i, folder in enumerate(sorted(leaves)):
        raw_name  = folder.name          # e.g. "A", "Hello", "ThankYou"
        label     = normalize_name(raw_name)
        n         = process_folder(folder, label, i)
        total_copied += n

        if n > 0:
            dest = ("alphabet/" + label if is_single_letter(label) else label)
            print(f"  ✅  {raw_name:20s} → isl_dataset/{dest}/")
        else:
            skipped.append(raw_name)

    print()
    print("=" * 60)
    print(f"  ✅  Done! {total_copied} clips organised.")
    if skipped:
        print(f"  ⚠   {len(skipped)} folders skipped (already existed or empty):")
        for s in skipped[:10]:
            print(f"       – {s}")
    print("=" * 60)
    print(f"""
Next steps:
  1. Run the app:   streamlit run app.py
                    (or: python -m streamlit run app.py)
  2. Upload any video and click Convert to ISL
  3. You will now see REAL ISL gesture clips in the output!
""")


if __name__ == "__main__":
    main()
