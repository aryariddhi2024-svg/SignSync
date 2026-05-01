import os
from pathlib import Path

# Root of the ISL image archive folder.
# Change this path to wherever your archive folder is located.
ARCHIVE_DIR = Path(r"C:\Users\Lenovo\Downloads\archive")

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def load_isl_dataset() -> dict[str, str]:
    """
    Scans the archive folder and returns a dict:
      { "word_or_letter": "/absolute/path/to/image.jpg", ... }

    Rules:
    - Filename without extension is used as the key (lowercased).
    - e.g.  archive/Hello.jpg  →  key: "hello"
    - e.g.  archive/A.png      →  key: "a"
    - Subfolders are also scanned recursively.
    - If multiple images exist for the same key, the first one found is used.
    """
    dataset = {}
    if not ARCHIVE_DIR.exists():
        print(f"[dataset_loader] ERROR: archive folder not found at {ARCHIVE_DIR}")
        return dataset

    for img_path in sorted(ARCHIVE_DIR.rglob("*")):
        if img_path.suffix.lower() in SUPPORTED_EXTS:
            stem_key = img_path.stem.lower().strip()
            parent_key = img_path.parent.name.lower().strip()

            # If filename is a number (e.g., '1.jpg' inside 'A/'), use the folder name instead.
            if stem_key.isnumeric() and parent_key not in ('archive', 'indian'):
                key = parent_key
            else:
                key = stem_key

            if key and key not in dataset:
                dataset[key] = str(img_path)

    print(f"[dataset_loader] Loaded {len(dataset)} ISL signs from {ARCHIVE_DIR}")
    return dataset

# Pre-load once at import time so all modules share the same dict
ISL_DATASET = load_isl_dataset()
