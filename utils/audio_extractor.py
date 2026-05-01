"""
utils/audio_extractor.py
Extracts audio from a video file using FFmpeg.
"""

import subprocess, os, tempfile
from pathlib import Path


def extract_audio(video_path: str, noise_reduce: bool = False) -> str | None:
    """
    Extract audio from *video_path* and return path to a WAV file.
    Returns None on failure.
    """
    try:
        out_dir  = tempfile.mkdtemp()
        wav_path = os.path.join(out_dir, "audio.wav")

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-vn",                  # no video
            "-acodec", "pcm_s16le", # 16-bit PCM – required by Whisper
            "-ar", "16000",         # 16 kHz sample rate
            "-ac", "1",             # mono
            wav_path,
        ]

        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=300
        )


        print("[audio_extractor] FFmpeg stdout:", result.stdout)
        print("[audio_extractor] FFmpeg stderr:", result.stderr)
        print("[audio_extractor] FFmpeg returncode:", result.returncode)

        if result.returncode != 0:
            print("[audio_extractor] FFmpeg FAILED — audio extraction error")
            return None

        if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
            print("[audio_extractor] Audio file missing or zero-size after extraction")
            return None

        print(f"[audio_extractor] Audio extracted successfully: {wav_path} "
              f"({os.path.getsize(wav_path)} bytes)")
        return wav_path

    except FileNotFoundError:
        print("FFmpeg not found. Install with: sudo apt install ffmpeg")
        return None
    except Exception as e:
        print(f"Audio extraction error: {e}")
        return None
