# 🤟 SignSync – AI-Based Video to Indian Sign Language Converter

**MCA Final Year Project | USCS, Uttaranchal University | Session 2025-26**
**Student:** Riddhi Arya (UU2420000094) | **Mentor:** Mr. Nitin Sharma

---

## 📌 Project Overview

SignSync converts spoken video content into **Indian Sign Language (ISL)** using:

| Stage | Tool | What it does |
|---|---|---|
| Audio extraction | **FFmpeg** | Strips audio from video |
| Speech recognition | **OpenAI Whisper** | Converts speech → text |
| NLP processing | **spaCy** | Tokenises & cleans text |
| ISL mapping | **Custom dictionary** | Maps words → gesture clips |
| Video assembly | **MoviePy** | Concatenates clips → ISL video |
| Web UI | **Streamlit** | Interactive browser interface |

---

## 🚀 Quick Start (3 steps)

### Step 1 – Install system tools

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg python3-pip git

# macOS
brew install ffmpeg python
```

### Step 2 – Install Python dependencies

```bash
cd signsync
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Step 3 – Set up dataset & run

```bash
# Creates placeholder ISL clips (works immediately without a real dataset)
python setup_dataset.py

# Launch the app
streamlit run app.py
```

Open **http://localhost:8501** in your browser. ✅

---

## 📁 Project Structure

```
signsync/
├── app.py                  ← Main Streamlit application
├── requirements.txt        ← Python dependencies
├── setup_dataset.py        ← Dataset initialiser
├── README.md
│
├── utils/
│   ├── audio_extractor.py  ← FFmpeg audio extraction
│   ├── speech_to_text.py   ← OpenAI Whisper STR
│   ├── nlp_processor.py    ← spaCy NLP pipeline
│   ├── isl_mapper.py       ← Word → gesture mapping
│   └── video_generator.py  ← MoviePy ISL video assembly
│
└── isl_dataset/            ← ISL gesture video library
    ├── hello/
    │   └── hello_1.mp4
    ├── thank_you/
    │   └── thank_you_1.mp4
    ├── india/
    │   └── india_1.mp4
    ├── ...
    └── alphabet/
        ├── a/  → a_1.mp4
        ├── b/  → b_1.mp4
        └── ...
```

---

## 📦 Dataset Sources (Free & Open)

| Dataset | Signs | Link | Notes |
|---|---|---|---|
| **INCLUDE-50** | 50 ISL signs | https://zenodo.org/record/4010759 | IIT Bombay, best quality |
| **ISLRTC** | ~3,000 words | https://islrtc.nic.in | Govt. of India official |
| **Kaggle ISL** | 35 signs (A-Z + digits) | https://kaggle.com/prathumarikeri/indian-sign-language-isl | Images + video |
| **OpenASL** | ~1,000 signs | https://github.com/chevalierNoir/OpenASL | ASL but usable structure |
| **Self-record** | Unlimited | Webcam + OBS | Best for custom vocabulary |

### Adding real gesture videos

```
# Place your MP4 clip here:
isl_dataset/
└── hello/
    └── hello_real.mp4      ← replaces placeholder automatically
```

Requirements per clip:
- Format: **MP4** (H.264)
- Resolution: **640 × 480** (or higher – auto-resized)
- Duration: **1–3 seconds** per sign
- FPS: **25–30**
- Background: Solid colour preferred for clarity

---

## 🔧 Configuration

Edit preferences inside the app (**⚙ Preferences** page) or set defaults in `app.py`:

| Setting | Default | Options |
|---|---|---|
| Whisper model | `base` | tiny / base / small / medium / large |
| Language | `en` | en / hi / auto |
| Noise reduction | On | On / Off |
| Signing speed | 1.0× | 0.5× – 2.0× |
| Fingerspell unknown | On | On / Off |

> **Whisper model guide:**
> - `tiny` – fastest, ~39 MB, good for demos
> - `base` – recommended balance (~74 MB)
> - `small` – better accuracy (~244 MB)
> - `medium` / `large` – best accuracy, needs GPU

---

## 🖥 System Requirements

| Component | Minimum | Recommended |
|---|---|---|
| Python | 3.9 | 3.11 |
| RAM | 4 GB | 8 GB |
| Storage | 2 GB | 10 GB (with dataset) |
| GPU | Not required | NVIDIA (for large Whisper model) |
| OS | Ubuntu 20.04 / Windows 10 / macOS 12 | Ubuntu 22.04 |

---

## ❓ Troubleshooting

| Error | Fix |
|---|---|
| `FFmpeg not found` | `sudo apt install ffmpeg` |
| `No module named whisper` | `pip install openai-whisper` |
| `[E050] Model 'en_core_web_sm' not found` | `python -m spacy download en_core_web_sm` |
| `No speech detected` | Video must contain clear spoken audio |
| `CUDA out of memory` | Switch Whisper model to `tiny` or `base` |
| `yt-dlp download fails` | Video may be private; try a public link |
| ISL video shows placeholder | Real gesture clips not added to `isl_dataset/` |

---

## 📋 Pipeline Flow

```
User uploads video / pastes URL
         │
         ▼
  ┌─────────────────┐
  │  Validate video  │  ← format check (MP4/AVI/MOV)
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │  Extract audio   │  ← FFmpeg → 16kHz mono WAV
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ Speech → Text    │  ← OpenAI Whisper
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │  NLP Processing  │  ← spaCy: tokenise, lemmatise, drop stopwords
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │  ISL Mapping     │  ← dictionary lookup → fingerspell if missing
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │  Render Video    │  ← MoviePy concatenates gesture clips
  └────────┬────────┘
           │
  ┌────────▼────────┐
  │ Display Results  │  ← side-by-side: original + ISL output
  └─────────────────┘
```

---

## 📄 License

Academic project – USCS, Uttaranchal University. Not for commercial use.
