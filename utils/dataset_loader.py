import os
from pathlib import Path

# Use the 'isl_dataset' folder located in the project root
ARCHIVE_DIR = Path(__file__).parent.parent / "isl_dataset"

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".mp4"}

def load_isl_dataset() -> dict[str, str]:
    """
    Scans the isl_dataset folder and returns a dict:
      { "word_or_letter": "/absolute/path/to/file.ext", ... }
    """
    dataset = {}
    if not ARCHIVE_DIR.exists():
        # Fallback to a folder named 'isl_dataset' in the current working directory
        ARCHIVE_DIR_FALLBACK = Path("isl_dataset")
        if ARCHIVE_DIR_FALLBACK.exists():
            search_dir = ARCHIVE_DIR_FALLBACK
        else:
            print(f"[dataset_loader] ERROR: dataset folder not found at {ARCHIVE_DIR}")
            return dataset
    else:
        search_dir = ARCHIVE_DIR

    # Scan for files
    for file_path in sorted(search_dir.rglob("*")):
        if file_path.suffix.lower() in SUPPORTED_EXTS:
            stem_key = file_path.stem.lower().strip()
            # If filename contains index (e.g. 'hello_1'), take the word part
            if "_" in stem_key:
                key = stem_key.split("_")[0]
            else:
                key = stem_key
            
            # Prioritise videos over images if both exist
            is_video = file_path.suffix.lower() == ".mp4"
            if key not in dataset or is_video:
                dataset[key] = str(file_path.absolute())

    print(f"[dataset_loader] Loaded {len(dataset)} ISL signs from {search_dir}")
    return dataset

# Pre-load once at import time so all modules share the same dict
ISL_DATASET = load_isl_dataset()
