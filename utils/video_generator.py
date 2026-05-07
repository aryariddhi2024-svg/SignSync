import cv2
import os
import tempfile
import numpy as np
from pathlib import Path

TARGET_W = 640
TARGET_H = 480
FPS = 25

def _secs_per_sign(speed: float) -> float:
    """
    How many seconds each ISL sign image is displayed.
    speed=1.0 → 1.2s per sign
    speed=2.0 → 0.6s per sign (faster)
    speed=0.5 → 2.4s per sign (slower)
    """
    return max(0.3, 1.2 / speed)

def generate_isl_video(mapped: list[tuple[str, str]], speed: float = 1.0) -> str | None:
    """
    Takes a list of (token, image_path) tuples.
    Produces an MP4 video where each image is shown for a fixed duration.

    Returns absolute path to the output MP4, or None on failure.
    """
    if not mapped:
        print("[video_generator] ERROR: mapped list is empty — no images to stitch")
        return None

    try:
        out_dir = tempfile.mkdtemp()
        temp_out = os.path.join(out_dir, "temp_out.mp4")
        out_path = os.path.join(out_dir, "isl_output.mp4")

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(temp_out, fourcc, FPS, (TARGET_W, TARGET_H))

        if not writer.isOpened():
            print("[video_generator] ERROR: VideoWriter failed to open")
            return None

        frames_per_sign = max(1, int(FPS * _secs_per_sign(speed)))
        blank = np.ones((TARGET_H, TARGET_W, 3), dtype=np.uint8) * 30  # dark grey blank

        for token, file_path in mapped:
            if not os.path.exists(file_path):
                print(f"[video_generator] SKIP (not found): {file_path}")
                continue

            ext = Path(file_path).suffix.lower()

            # ── Case A: Image file ────────────────────────────────────────────
            if ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
                img = cv2.imread(file_path)
                if img is None:
                    print(f"[video_generator] SKIP (unreadable image): {file_path}")
                    continue
                frame = _fit_image(img, TARGET_W, TARGET_H)
                
                # Add text label
                cv2.putText(frame, token.upper(), (20, TARGET_H - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
                
                for _ in range(frames_per_sign):
                    writer.write(frame)

            # ── Case B: Video file (clip) ─────────────────────────────────────
            elif ext == ".mp4":
                cap = cv2.VideoCapture(file_path)
                if not cap.isOpened():
                    print(f"[video_generator] SKIP (unreadable video): {file_path}")
                    continue
                
                while True:
                    ret, img = cap.read()
                    if not ret: break
                    
                    frame = _fit_image(img, TARGET_W, TARGET_H)
                    cv2.putText(frame, token.upper(), (20, TARGET_H - 20),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
                    writer.write(frame)
                cap.release()

            # Brief blank transition between signs (0.1s)
            for _ in range(max(1, int(FPS * 0.1))):
                writer.write(blank)

        writer.release()

        # Convert to web-safe H.264 using FFmpeg so Streamlit can play it natively
        import subprocess
        print("[video_generator] Converting to web-safe H.264...")
        subprocess.run(
            ["ffmpeg", "-y", "-i", temp_out, "-vcodec", "libx264", "-pix_fmt", "yuv420p", out_path],
            capture_output=True
        )

        if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
            print("[video_generator] ERROR: output file missing or empty")
            return None

        print(f"[video_generator] SUCCESS: {out_path} ({os.path.getsize(out_path)} bytes)")
        return out_path

    except Exception as e:
        import traceback
        print("[video_generator] EXCEPTION:", traceback.format_exc())
        return None


def _fit_image(img: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
    """Resize image to fit inside target dims, pad remainder with dark grey."""
    h, w = img.shape[:2]
    scale = min(target_w / w, target_h / h)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = np.ones((target_h, target_w, 3), dtype=np.uint8) * 30
    y_off = (target_h - new_h) // 2
    x_off = (target_w - new_w) // 2
    canvas[y_off:y_off+new_h, x_off:x_off+new_w] = resized
    return canvas
