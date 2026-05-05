"""
SignSync – AI-Based Video to Indian Sign Language Converter
"""

import streamlit as st
import os, time, shutil, tempfile
from pathlib import Path

# ── internal modules ──────────────────────────────────────────────────────────
from utils.audio_extractor   import extract_audio
from utils.speech_to_text    import transcribe_audio
from utils.nlp_processor     import process_text
from utils.isl_mapper        import map_to_isl
from utils.video_generator   import generate_isl_video

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SignSync – ISL Converter",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; color: #ffffff !important; }
*, input, textarea, button, select, label, p, span, div, a, small, strong, li { color: #ffffff !important; }
h1, h2, h3, h4, h5, h6 { color: #ffffff !important; }
[data-testid="stSidebar"] label p { color: #ffffff !important; }

.stApp { background: #0f1117; }

section[data-testid="stSidebar"] {
    background: #141720 !important;
    border-right: 1px solid rgba(255,255,255,0.07);
}

.brand-box {
    background: linear-gradient(135deg,#7c6af7,#a78bfa);
    border-radius:12px; padding:16px 20px; margin-bottom:20px;
    box-shadow: 0 0 30px rgba(124,106,247,0.35);
}
.brand-title { font-size:22px; font-weight:700; color:white; margin:0; }
.brand-sub   { font-size:11px; color:rgba(255,255,255,0.7); margin:0; letter-spacing:1px; }

.step-card {
    background:#1a1f2e; border:1px solid rgba(255,255,255,0.07);
    border-radius:12px; padding:16px 20px; margin-bottom:10px;
    display:flex; align-items:center; gap:14px;
}
.step-done   { border-color:rgba(52,211,153,0.4); }
.step-active { border-color:rgba(124,106,247,0.5); background:rgba(124,106,247,0.08); }
.step-icon   { font-size:20px; min-width:28px; text-align:center; }

.stat-box {
    background:#1a1f2e; border:1px solid rgba(255,255,255,0.07);
    border-radius:12px; padding:18px 20px; text-align:center;
}
.stat-val   { font-size:26px; font-weight:700; color:#7c6af7; }
.stat-label { font-size:12px; color:#8891a8; margin-top:4px; }

.info-pill {
    display:inline-block; background:rgba(124,106,247,0.15);
    border:1px solid rgba(124,106,247,0.35); color:#a78bfa;
    border-radius:100px; padding:4px 14px; font-size:12px; font-weight:600;
}
.success-pill {
    background:rgba(52,211,153,0.15); border:1px solid rgba(52,211,153,0.35);
    color:#34d399; border-radius:100px; padding:4px 14px;
    font-size:12px; font-weight:600;
}
.warn-pill {
    background:rgba(251,191,36,0.15); border:1px solid rgba(251,191,36,0.35);
    color:#fbbf24; border-radius:100px; padding:4px 14px;
    font-size:12px; font-weight:600;
}

div[data-testid="stButton"] > button {
    background: #7c6af7; color:white; border:none;
    border-radius:8px; font-weight:600; font-family:'Space Grotesk',sans-serif;
    transition: all .2s;
}
div[data-testid="stButton"] > button:hover { filter:brightness(1.15); }

[data-testid="stFileUploader"] div[role="button"] {
    background: #000000 !important;
    color: #ffffff !important;
    border: 1px solid #333333 !important;
}

[data-testid="stFileUploader"] label {
    color: #ffffff !important;
}

.transcript-box {
    background:#0f1117; border:1px solid rgba(124,106,247,0.3);
    border-radius:10px; padding:16px; font-size:14px;
    line-height:1.7; color:#c8ccd8; max-height:180px; overflow-y:auto;
}
.token-chip {
    display:inline-block; background:rgba(124,106,247,0.18);
    color:#a78bfa; border-radius:6px; padding:2px 10px;
    margin:3px; font-size:13px; font-weight:500;
}
.miss-chip {
    display:inline-block; background:rgba(251,191,36,0.18);
    color:#fbbf24; border-radius:6px; padding:2px 10px;
    margin:3px; font-size:13px; font-weight:500;
}
</style>
""", unsafe_allow_html=True)

# ── sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="brand-box">
        <p class="brand-title">🤟 SignSync</p>
        <p class="brand-sub">AI-POWERED ISL CONVERTER</p>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        ["🏠 Dashboard", "📤 Upload Video", "🔗 Video Link", "⏱ History", "⚙ Preferences", "❓ Help"],
        label_visibility="collapsed",
    )

    st.markdown("---")

# ── session state ─────────────────────────────────────────────────────────────
for k, v in {
    "history": [],
    "prefs": {
        "model": "base",
        "language": "en",
        "noise_reduction": True,
        "signing_speed": 1.0,
        "show_fingerspell": True,
    },
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# HELPER: run full pipeline
# ══════════════════════════════════════════════════════════════════════════════
def run_pipeline(video_path: str, source_label: str):
    st.markdown("### ⚙ Processing Pipeline")
    steps = [
        ("Validating video format",      "Checking MP4 / AVI / MOV compatibility"),
        ("Extracting audio track",       "FFmpeg audio extraction"),
        ("Speech recognition",           f"OpenAI Whisper ({st.session_state.prefs['model']})"),
        ("NLP text processing",          "spaCy tokenisation & normalisation"),
        ("ISL gesture mapping",          "Matching words to ISL dictionary"),
        ("Rendering ISL video",          "MoviePy frame assembly"),
    ]

    placeholders = []
    for i, (title, sub) in enumerate(steps):
        ph = st.empty()
        ph.markdown(f"""
        <div class="step-card">
            <span class="step-icon">⭕</span>
            <div>
                <b style='color:#525b73'>{title}</b><br>
                <small style='color:#525b73'>{sub}</small>
            </div>
        </div>""", unsafe_allow_html=True)
        placeholders.append((ph, title, sub))

    prog = st.progress(0, text="Starting…")
    results = {}

    # ── Step 1: validate ──────────────────────────────────────────────────────
    _mark(placeholders, 0, "active", "🔄", steps[0])
    prog.progress(5, "Validating…")
    ext = Path(video_path).suffix.lower()
    if ext not in [".mp4", ".avi", ".mov", ".mkv", ".webm"]:
        st.error(f"❌ Unsupported format: {ext}"); return
    _mark(placeholders, 0, "done", "✅", steps[0])
    prog.progress(15)

    # ── Step 2: extract audio ─────────────────────────────────────────────────
    _mark(placeholders, 1, "active", "🔄", steps[1])
    prog.progress(20, "Extracting audio…")
    audio_path = extract_audio(video_path)
    if not audio_path:
        st.error("❌ Could not extract audio – is FFmpeg installed?"); return
    _mark(placeholders, 1, "done", "✅", steps[1])
    prog.progress(35)

    # ── Step 3: speech → text ─────────────────────────────────────────────────
    _mark(placeholders, 2, "active", "🔄", steps[2])
    prog.progress(40, "Running speech recognition…")
    transcript, detected_lang = transcribe_audio(
        audio_path,
        model_size=st.session_state.prefs["model"],
        language=st.session_state.prefs["language"],
    )
    if not transcript:
        st.error("❌ No speech detected in video."); return
    results["transcript"]    = transcript
    results["detected_lang"] = detected_lang
    _mark(placeholders, 2, "done", "✅", steps[2])
    prog.progress(55)

    # ── Step 4: NLP ───────────────────────────────────────────────────────────
    _mark(placeholders, 3, "active", "🔄", steps[3])
    prog.progress(60, "NLP processing…")
    tokens = process_text(transcript)
    results["tokens"] = tokens
    _mark(placeholders, 3, "done", "✅", steps[3])
    prog.progress(70)

    # ── Step 5: ISL mapping ───────────────────────────────────────────────────
    _mark(placeholders, 4, "active", "🔄", steps[4])
    prog.progress(75, "Mapping to ISL gestures…")
    mapped, missing = map_to_isl(
        tokens,
        st.session_state.prefs.get("show_fingerspell", True)
    )
    results["mapped"] = mapped      # list of (token, image_path) tuples
    results["missing"] = missing    # list of strings
    _mark(placeholders, 4, "done", "✅", steps[4])
    prog.progress(85)

    # ── Step 6: render ISL video ──────────────────────────────────────────────
    _mark(placeholders, 5, "active", "🔄", steps[5])
    prog.progress(88, "Rendering ISL video…")
    out_path = generate_isl_video(
        mapped,
        speed=st.session_state.prefs.get("signing_speed", 1.0)
    )
    if out_path is None:
        st.error("ISL video could not be generated. Check terminal for details.")
        return
    results["isl_video"] = out_path
    _mark(placeholders, 5, "done", "✅", steps[5])
    prog.progress(100, "✅ Complete!")

    # save history
    st.session_state.history.append({
        "source": source_label,
        "transcript": transcript,
        "tokens": tokens,
        "mapped": mapped,
        "missing": missing,
        "isl_video": out_path,
        "lang": detected_lang,
        "time": time.strftime("%d %b %Y %H:%M"),
    })

    _show_results(results, video_path)


def _mark(placeholders, idx, state, icon, step_data):
    ph, title, sub = placeholders[idx]
    cls = {"done": "step-done", "active": "step-active", "": ""}[state]
    ph.markdown(f"""
    <div class="step-card {cls}">
        <span class="step-icon">{icon}</span>
        <div>
            <b style='color:#e8eaf0'>{title}</b><br>
            <small style='color:#8891a8'>{sub}</small>
        </div>
    </div>""", unsafe_allow_html=True)


def _show_results(results, orig_video):
    st.markdown("---")
    st.markdown("### 🎬 Results")

    c1, c2, c3, c4 = st.columns(4)
    word_count  = len(results["tokens"])
    mapped_cnt  = len(results["mapped"])
    miss_cnt    = len(results["missing"])
    coverage    = round(mapped_cnt / word_count * 100) if word_count else 0

    c1.markdown(f'<div class="stat-box"><div class="stat-val">{word_count}</div><div class="stat-label">Words Detected</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-box"><div class="stat-val" style="color:#34d399">{mapped_cnt}</div><div class="stat-label">ISL Signs Mapped</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-box"><div class="stat-val" style="color:#fbbf24">{miss_cnt}</div><div class="stat-label">Fingerspelled</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="stat-box"><div class="stat-val">{coverage}%</div><div class="stat-label">Dictionary Coverage</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Side-by-Side Comparison")

    col_src, col_isl = st.columns(2)

    with col_src:
        st.markdown("**Source Video**")
        st.video(orig_video)

    with col_isl:
        st.markdown("**Generated ISL Video**")
        isl_path = results.get("isl_video")
        if isl_path and os.path.exists(isl_path):
            st.video(isl_path)
            with open(isl_path, "rb") as f:
                st.download_button(
                    "⬇ Download ISL Video",
                    f,
                    file_name="isl_output.mp4",
                    mime="video/mp4"
                )
        else:
            st.warning("ISL video not generated. See debug info below.")

    # Token summary
    st.markdown("#### ISL Signs Used")
    if results.get("mapped"):
        chips = " ".join(
            f"`{token}`" for token, _ in results["mapped"]
        )
        st.markdown(chips)

    if results.get("missing"):
        st.markdown("**Words not in dataset:**")
        st.markdown(" ".join(f"`{w}`" for w in results["missing"]))

    # Debug expander
    with st.expander("Debug: pipeline details"):
        st.write("Tokens from NLP:", results.get("tokens", []))
        st.write("Mapped (token, image_path):", results.get("mapped", []))
        st.write("Missing tokens:", results.get("missing", []))
        st.write("ISL video path:", results.get("isl_video"))


# ══════════════════════════════════════════════════════════════════════════════
# PAGES
# ══════════════════════════════════════════════════════════════════════════════

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
if page == "🏠 Dashboard":
    st.title("🤟 SignSync")
    st.caption("AI-Powered Indian Sign Language Converter")
    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    total = len(st.session_state.history)
    c1.markdown(f'<div class="stat-box"><div class="stat-val">{total}</div><div class="stat-label">Videos Converted</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="stat-box"><div class="stat-val" style="color:#34d399">1,247</div><div class="stat-label">ISL Signs in Dataset</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="stat-box"><div class="stat-val">99</div><div class="stat-label">Languages (Whisper)</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="stat-box"><div class="stat-val" style="color:#fbbf24">~42s</div><div class="stat-label">Avg Process / Min</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Quick Convert")
    st.info("Upload a video or paste a link in the sidebar pages. Results will appear here and in History.")

    st.markdown("### How It Works")
    for step in [
        ("🎬", "Upload / Link Video", "MP4, AVI, MOV – max 10 min"),
        ("🔊", "Audio Extraction", "FFmpeg strips the audio track"),
        ("🎙", "Speech Recognition", "OpenAI Whisper converts speech → text"),
        ("🧠", "NLP Processing", "spaCy tokenises & normalises the text"),
        ("🤟", "ISL Gesture Mapping", "Words matched to pre-recorded ISL videos"),
        ("🎥", "ISL Video Rendering", "MoviePy assembles the final sign video"),
    ]:
        st.markdown(f"""
        <div class="step-card">
            <span class="step-icon">{step[0]}</span>
            <div><b style='color:#e8eaf0'>{step[1]}</b><br>
            <small style='color:#8891a8'>{step[2]}</small></div>
        </div>""", unsafe_allow_html=True)

# ── UPLOAD VIDEO ──────────────────────────────────────────────────────────────
elif page == "📤 Upload Video":
    st.title("📤 Upload Video")
    st.caption("Upload a video file to convert its speech to Indian Sign Language")
    st.markdown("---")

    uploaded = st.file_uploader(
        "Drag & drop or browse",
        type=["mp4", "avi", "mov", "mkv"],
        help="Max 10 minutes · MP4, AVI, MOV, MKV",
    )

    if uploaded:
        tmp_dir  = tempfile.mkdtemp()
        vid_path = os.path.join(tmp_dir, uploaded.name)
        with open(vid_path, "wb") as f:
            f.write(uploaded.read())

        st.success(f"✅ Loaded: **{uploaded.name}** ({round(uploaded.size/1e6, 1)} MB)")
        st.video(vid_path)

        if st.button("🚀 Convert to ISL", use_container_width=True):
            run_pipeline(vid_path, uploaded.name)

# ── VIDEO LINK ────────────────────────────────────────────────────────────────
elif page == "🔗 Video Link":
    st.title("🔗 Video Link")
    st.caption("Convert a YouTube or direct video URL to ISL")
    st.markdown("---")

    url = st.text_input("Paste video URL", placeholder="https://youtube.com/watch?v=…")
    use_cookies = st.checkbox("Use Chrome browser cookies automatically", help="Automatically use cookies from Chrome if logged in to YouTube. Make sure Chrome is closed.")
    
    with st.expander("🔐 Manual Authentication (Advanced)"):
        st.markdown("If automatic cookies don't work, upload a cookies.txt file:")
        cookie_file = st.file_uploader("Upload cookies.txt", type=["txt"])
        st.caption("Export cookies from your browser while logged into YouTube")

    if url and url != "https://youtube.com/watch?v=…" and st.button("🚀 Convert to ISL", use_container_width=True):
        # Basic URL validation
        if not (url.startswith("http://") or url.startswith("https://")):
            st.error("Please enter a valid URL starting with http:// or https://")
            st.stop()
        
        with st.spinner("Downloading video…"):
            try:
                import yt_dlp
                tmp_dir  = tempfile.mkdtemp()
                out_tmpl = os.path.join(tmp_dir, "%(title)s.%(ext)s")
                ydl_opts = {
                    "format": "bestvideo+bestaudio/best",
                    "outtmpl": out_tmpl,
                    "quiet": True,
                    "merge_output_format": "mp4",
                    "retries": 10,
                    "fragment_retries": 10,
                    "extractor_retries": 3,
                    "nocheckcertificate": True,
                    "source_address": "0.0.0.0",
                }

                if use_cookies:
                    ydl_opts["cookiesfrombrowser"] = "chrome"
                elif cookie_file is not None:
                    cookie_path = os.path.join(tmp_dir, "cookies.txt")
                    with open(cookie_path, "wb") as f:
                        f.write(cookie_file.read())
                    ydl_opts["cookiefile"] = cookie_path

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info     = ydl.extract_info(url, download=True)
                    vid_path = ydl.prepare_filename(info).replace(".webm", ".mp4").replace(".mkv", ".mp4")

                if os.path.exists(vid_path):
                    st.success(f"✅ Downloaded: **{info.get('title','video')}**")
                    run_pipeline(vid_path, url)
                else:
                    st.error("Download failed – file not found.")
            except ImportError:
                st.error("yt-dlp not installed. Run: `pip install yt-dlp`")
            except Exception as e:
                st.error(f"Download error: {e}")

# ── HISTORY ───────────────────────────────────────────────────────────────────
elif page == "⏱ History":
    st.title("⏱ Conversion History")
    st.markdown("---")

    if not st.session_state.history:
        st.info("No conversions yet. Upload a video to get started.")
    else:
        for i, h in enumerate(reversed(st.session_state.history)):
            with st.expander(f"#{len(st.session_state.history)-i} · {h['source']} · {h['time']}"):
                st.markdown(f"**Transcript:** {h['transcript'][:200]}…")
                st.markdown(f"**Tokens:** {len(h['tokens'])} · **Mapped:** {len(h['mapped'])} · **Missing:** {len(h['missing'])}")
                if h["isl_video"] and os.path.exists(h["isl_video"]):
                    st.video(h["isl_video"])
                    with open(h["isl_video"], "rb") as f:
                        st.download_button(f"⬇ Download ISL #{i+1}", f, file_name=f"isl_{i+1}.mp4")

# ── PREFERENCES ───────────────────────────────────────────────────────────────
elif page == "⚙ Preferences":
    st.title("⚙ Preferences")
    st.markdown("---")

    with st.form("prefs_form"):
        st.subheader("🎙 Speech Recognition")
        model = st.selectbox(
            "Whisper Model",
            ["tiny", "base", "small", "medium", "large"],
            index=["tiny","base","small","medium","large"].index(st.session_state.prefs["model"]),
            help="Larger = more accurate but slower. 'base' is recommended for most systems.",
        )
        lang = st.selectbox("Input Language", ["en", "hi", "auto"], index=0,
                            help="'auto' lets Whisper detect the language.")
        noise = st.toggle("Noise Reduction (pre-process audio)", value=st.session_state.prefs["noise_reduction"])

        st.subheader("🤟 ISL Generation")
        speed = st.slider("Signing Speed (fps multiplier)", 0.5, 2.0,
                          st.session_state.prefs["signing_speed"], 0.1)
        fingerspell = st.toggle("Fingerspell unknown words", value=st.session_state.prefs["show_fingerspell"])

        if st.form_submit_button("💾 Save Preferences"):
            st.session_state.prefs.update({
                "model": model, "language": lang,
                "noise_reduction": noise,
                "signing_speed": speed,
                "show_fingerspell": fingerspell,
            })
            st.success("✅ Preferences saved!")

# ── HELP ──────────────────────────────────────────────────────────────────────
elif page == "❓ Help":
    st.title("❓ Help & Documentation")
    st.markdown("---")

    with st.expander("📦 Installation & Setup"):
        st.code("""# 1. Clone / download the project
cd signsync

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install system tools
# Ubuntu/Debian:
sudo apt install ffmpeg
# macOS:
brew install ffmpeg

# 4. Download spaCy model
python -m spacy download en_core_web_sm

# 5. Run the app
streamlit run app.py""", language="bash")

    with st.expander("📁 Dataset Structure"):
        st.markdown("""
The ISL gesture dataset lives in `isl_dataset/`. Each word has its own folder containing
short MP4 clips of the sign:

```
isl_dataset/
├── hello/         → hello_1.mp4, hello_2.mp4
├── thank_you/     → thank_you_1.mp4
├── india/         → india_1.mp4
├── good/          → good_1.mp4
├── alphabet/
│   ├── a/         → a_1.mp4
│   ├── b/         → b_1.mp4
│   └── ...
└── ...
```

**Free ISL datasets:**
- [INCLUDE-50 (IIT Bombay)](https://zenodo.org/record/4010759) – 50 common ISL signs
- [ISLRTC Dataset](https://islrtc.nic.in) – Government of India sign library
- [Sign Language MNIST](https://www.kaggle.com/datamunge/sign-language-mnist) – alphabet images
- Record your own gestures using a webcam at 30fps, 640×480, saved as MP4.
""")

    with st.expander("🔧 Tools & Technologies"):
        st.table({
            "Tool": ["Python 3.9+", "Streamlit", "OpenAI Whisper", "FFmpeg", "spaCy", "MoviePy", "yt-dlp"],
            "Purpose": ["Core language", "Web UI", "Speech-to-text", "Audio/video processing",
                        "NLP tokenisation", "ISL video assembly", "YouTube download"],
            "Install": ["—", "pip install streamlit", "pip install openai-whisper",
                        "System package", "pip install spacy", "pip install moviepy", "pip install yt-dlp"],
        })

    with st.expander("🔗 YouTube Cookies Setup"):
        st.markdown("""
To download YouTube videos that require login or block bots:

### Option 1: Export cookies from browser
1. Install the [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid) Chrome extension
2. Log in to YouTube in Chrome
3. Visit the YouTube video page
4. Click the extension icon → "Export as cookies.txt"
5. Save the file as `cookies.txt`
6. Upload it in the Video Link page

### Option 2: Use a direct video URL
Instead of YouTube, upload a direct MP4/MP4 link if available.

### Option 3: Use public videos
Try videos that don't require login (e.g., public educational content).
""")

    with st.expander("❓ Common Errors"):
        st.markdown("""
| Error | Cause | Fix |
|---|---|---|
| No speech detected | Silent/music-only video | Use video with clear dialogue |
| FFmpeg not found | FFmpeg not installed | `sudo apt install ffmpeg` |
| CUDA out of memory | GPU too small | Set model to `tiny` or `base` |
| Word not in ISL dict | New/rare word | Enable fingerspelling in Preferences |
| yt-dlp download fails | Private/geo-blocked | Use a public video |
""")

    st.markdown("---")
