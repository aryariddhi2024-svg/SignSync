"""
setup_dataset.py
Creates the ISL dataset directory structure and generates placeholder clips
using PIL + imageio so the app works out-of-the-box without a real dataset.

Replace any folder's .mp4 files with real pre-recorded ISL gesture videos
to get genuine sign output.

Run once:
    python setup_dataset.py

Dataset sources (free):
  1. INCLUDE-50  – https://zenodo.org/record/4010759  (IIT Bombay, 50 ISL signs)
  2. ISLRTC      – https://islrtc.nic.in              (Govt. of India)
  3. OpenASL     – https://github.com/chevalierNoir/OpenASL
  4. Kaggle ISL  – https://www.kaggle.com/datasets/prathumarikeri/indian-sign-language-isl
  5. Self-record – Record gestures at 640×480, 30 fps, save as MP4
"""

import os, sys
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    import imageio
except ImportError:
    print("Installing required packages…")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "Pillow", "numpy", "imageio[ffmpeg]"])
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    import imageio

BASE = Path(__file__).parent / "isl_dataset"

# ── Word list (common ISL vocabulary) ────────────────────────────────────────
WORDS = [
    "hello", "goodbye", "thank_you", "please", "sorry",
    "help", "yes", "no", "good", "bad",
    "india", "learn", "sign", "language", "school",
    "home", "food", "water", "name", "understand",
    "welcome", "friend", "family", "love", "happy",
    "sad", "angry", "work", "play", "stop",
    "go", "come", "sit", "stand", "walk",
    "eat", "drink", "sleep", "wake", "read",
    "write", "speak", "listen", "see", "know",
    "today", "tomorrow", "yesterday", "morning", "night",
    "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "watch", "video", "computer", "phone", "book",
    "everyone", "man", "woman", "child", "teacher",
    "student", "doctor", "police", "hospital", "university",
    "namaste", "bharat", "english", "hindi", "time",
    "day", "week", "month", "year", "hour",
]

ALPHABET = list("abcdefghijklmnopqrstuvwxyz")

COLORS = {
    "word":  (26,  31,  46),   # dark navy background
    "alpha": (20,  25,  40),   # slightly different for alphabet
    "text":  (124, 106, 247),  # purple accent
    "sub":   (168, 139, 251),  # lighter purple
}


def _make_clip(label: str, bg_color: tuple, fps: int = 12, duration: float = 1.0) -> list:
    """Return list of numpy frames for *label*."""
    n_frames = int(fps * duration)
    frames   = []

    try:
        font_lg = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 64)
        font_sm = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    except Exception:
        font_lg = ImageFont.load_default()
        font_sm = font_lg

    for i in range(n_frames):
        img  = Image.new("RGB", (640, 480), color=bg_color)
        draw = ImageDraw.Draw(img)

        # pulsing circle behind text
        pulse = int(80 + 20 * abs((i / n_frames) - 0.5) * 2)
        draw.ellipse(
            [(320 - pulse, 240 - pulse), (320 + pulse, 240 + pulse)],
            fill=(COLORS["text"][0]//5, COLORS["text"][1]//5, COLORS["text"][2]//5),
        )

        # main label
        disp = label.replace("_", " ").upper()
        bbox = draw.textbbox((0, 0), disp, font=font_lg)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((640 - tw) // 2, (480 - th) // 2 - 20),
                  disp, fill=COLORS["text"], font=font_lg)

        # subtitle
        sub = "ISL GESTURE"
        bbox2 = draw.textbbox((0, 0), sub, font=font_sm)
        sw = bbox2[2] - bbox2[0]
        draw.text(((640 - sw) // 2, (480 - th) // 2 + th + 10),
                  sub, fill=COLORS["sub"], font=font_sm)

        # hand emoji top-right
        draw.text((560, 20), "🤟", font=font_sm)

        frames.append(np.array(img))

    return frames


def make_mp4(path: Path, label: str, is_alpha: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    bg = COLORS["alpha"] if is_alpha else COLORS["word"]
    frames = _make_clip(label, bg_color=bg)
    try:
        imageio.mimwrite(str(path), frames, fps=12, quality=8, macro_block_size=None)
    except Exception as e:
        print(f"  ⚠  Could not write {path.name}: {e}")


def setup():
    print("=" * 60)
    print("  SignSync – ISL Dataset Setup")
    print("=" * 60)
    print(f"\nDataset directory: {BASE}\n")

    # words
    print(f"Creating {len(WORDS)} word clips…")
    for w in WORDS:
        folder = BASE / w
        clip   = folder / f"{w}_1.mp4"
        if not clip.exists():
            make_mp4(clip, w.replace("_", " "))
            print(f"  ✓  {w}")
        else:
            print(f"  –  {w} (exists)")

    # alphabet
    print(f"\nCreating {len(ALPHABET)} alphabet clips…")
    for ch in ALPHABET:
        folder = BASE / "alphabet" / ch
        clip   = folder / f"{ch}_1.mp4"
        if not clip.exists():
            make_mp4(clip, ch, is_alpha=True)
            print(f"  ✓  {ch}")
        else:
            print(f"  –  {ch} (exists)")

    print("\n" + "=" * 60)
    print(f"  ✅  Done! {len(WORDS)} words + {len(ALPHABET)} alphabet letters")
    print("=" * 60)
    print("""
To use REAL ISL gesture videos:
  1. Download from any source listed at the top of this file
  2. Place MP4 clips inside  isl_dataset/<word>/  folders
     Example: isl_dataset/hello/hello_real.mp4
  3. The placeholder clip will be replaced automatically.

Then run the app:
  streamlit run app.py
""")


if __name__ == "__main__":
    setup()
