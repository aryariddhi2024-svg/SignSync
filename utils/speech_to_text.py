"""
utils/speech_to_text.py
Speech recognition using OpenAI Whisper.
Falls back to a dummy transcript when Whisper is unavailable (demo mode).
"""

from __future__ import annotations
import os


def transcribe_audio(
    audio_path: str,
    model_size: str = "base",
    language: str = "en",
) -> tuple[str, str]:
    """
    Transcribe *audio_path* and return (transcript_text, detected_language).
    """
    # ── try real Whisper ──────────────────────────────────────────────────────
    try:
        import whisper  # openai-whisper

        model = whisper.load_model(model_size)

        options = {}
        if language and language != "auto":
            options["language"] = language

        result = model.transcribe(audio_path, **options)

        transcript    = result.get("text", "").strip()
        detected_lang = result.get("language", language or "en")

        print("[speech_to_text] Raw Whisper transcript:", repr(transcript))
        print("[speech_to_text] Detected language:", detected_lang)

        if not transcript or not transcript.strip():
            print("[speech_to_text] WARNING: Whisper returned empty transcript")
            return "", detected_lang

        return transcript, detected_lang

    except ImportError:
        print("openai-whisper not installed – using demo transcript.")
    except Exception as e:
        print(f"Whisper error: {e} – using demo transcript.")

    # ── demo fallback (no Whisper / no audio) ─────────────────────────────────
    demo = (
        "Hello everyone welcome to India. "
        "Today we will learn Indian Sign Language. "
        "Please help us understand better. "
        "Thank you very much for watching this video."
    )
    return demo, "en"
