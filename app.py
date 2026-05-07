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

input, textarea, select, [role="textbox"], div[role="combobox"], .stTextInput>div>div>input, .stTextInput>div>div>textarea {
    background: #0f1117 !important;
    color: #ffffff !important;
    border-color: rgba(255,255,255,0.12) !important;
}

[data-testid="stFileUploader"] div[role="button"] {
    background: #000000 !important;
    color: #ffffff !important;
    border: 1px solid #333333 !important;
}

[data-testid="stFileUploader"] label {
    color: #ffffff !important;
}

.brand-box {
    background: #000000;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius:12px; padding:16px 20px; margin-bottom:20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}
.brand-title { font-size:22px; font-weight:700; color:#ffffff; margin:0; }
.brand-sub   { font-size:11px; color:#8891a8; margin:0; letter-spacing:1px; }

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
    background: #ffffff; color: #000000 !important; border: 1px solid #000000;
    border-radius:8px; font-weight:600; font-family:'Space Grotesk',sans-serif;
    transition: all .2s;
}
div[data-testid="stButton"] > button:hover { background: #e0e0e0; border-color: #000000; }

[data-testid="stFileUploader"] div[role="button"] {
    background: #ffffff !important;
    color: #000000 !important;
    border: 1px solid #000000 !important;
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
        ["🏠 Dashboard", "📤 Upload Video", "🔗 Video Link", "⏱ History"],
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
    st.markdown("#### 🎬 Side-by-Side Comparison")

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
            st.warning("ISL video not generated. Check terminal for details.")


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

    use_cookies = st.checkbox(
        "Use Chrome browser cookies automatically",
        value=False,
        help="⚠️ Requires Chrome to be fully closed. Fails on newer yt-dlp versions on Windows. Use cookies.txt upload below instead if this fails."
    )

    with st.expander("🔐 Manual Authentication (Advanced)"):
        st.markdown("""
        **Recommended method:** Upload a `cookies.txt` file exported from your browser.
        1. Install the **[Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)** Chrome extension
        2. Log in to YouTube in Chrome
        3. Go to the YouTube video page, click the extension → **Export**
        4. Upload the saved file below
        """)
        cookie_file = st.file_uploader("Upload cookies.txt", type=["txt"])

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

                base_opts = {
                    "format": "best",
                    "outtmpl": out_tmpl,
                    "quiet": True,
                    "merge_output_format": "mp4",
                    "retries": 5,
                    "fragment_retries": 5,
                    "nocheckcertificate": True,
                    "socket_timeout": 30,
                    # Spoof a normal browser UA to avoid bot detection
                    "http_headers": {
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/124.0.0.0 Safari/537.36"
                        )
                    },
                }

                # ── Apply auth ────────────────────────────────────────────
                if cookie_file is not None:
                    cookie_path = os.path.join(tmp_dir, "cookies.txt")
                    with open(cookie_path, "wb") as f:
                        f.write(cookie_file.read())
                    base_opts["cookiefile"] = cookie_path
                    st.info("🍪 Using uploaded cookies.txt for authentication.")
                elif use_cookies:
                    # Try automatic cookie extraction – may fail on Windows
                    base_opts["cookiesfrombrowser"] = ("chrome",)
                    st.info("🍪 Attempting automatic Chrome cookie extraction…")

                info, vid_path = None, None

                # ── Attempt download ──────────────────────────────────────
                try:
                    with yt_dlp.YoutubeDL(base_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        vid_path = ydl.prepare_filename(info)
                        # Normalise extension
                        for ext in (".webm", ".mkv"):
                            if vid_path.endswith(ext):
                                vid_path = vid_path[:-len(ext)] + ".mp4"
                except Exception as inner_err:
                    inner_msg = str(inner_err)
                    cookie_related = any(k in inner_msg for k in [
                        "_parse_browser_specification", "cookiesfrombrowser",
                        "browser-cookie3", "Automatic browser cookie",
                        "Could not find a suitable browser profile",
                    ])
                    if cookie_related and use_cookies:
                        # Cookie extraction failed → retry without cookies
                        st.warning(
                            "⚠️ Automatic cookie extraction failed (Chrome must be fully closed on Windows). "
                            "Retrying without cookies…"
                        )
                        fallback_opts = {k: v for k, v in base_opts.items() if k != "cookiesfrombrowser"}
                        with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                            info = ydl.extract_info(url, download=True)
                            vid_path = ydl.prepare_filename(info)
                            for ext in (".webm", ".mkv"):
                                if vid_path.endswith(ext):
                                    vid_path = vid_path[:-len(ext)] + ".mp4"
                    else:
                        raise

                if vid_path and os.path.exists(vid_path):
                    st.success(f"✅ Downloaded: **{info.get('title', 'video')}**")
                    run_pipeline(vid_path, url)
                else:
                    st.error(
                        "❌ Download completed but output file not found. "
                        "This can happen with some video formats — try a different URL."
                    )

            except ImportError:
                st.error("yt-dlp not installed. Run: `pip install yt-dlp`")
            except Exception as e:
                err_msg = str(e)
                cookie_hint = any(k in err_msg for k in [
                    "_parse_browser_specification", "cookiesfrombrowser",
                    "browser-cookie3", "browser cookie",
                ])
                age_restricted = "age" in err_msg.lower() or "sign in" in err_msg.lower()
                bot_detected   = "bot" in err_msg.lower() or "429" in err_msg or "blocked" in err_msg.lower()

                if cookie_hint:
                    st.error(
                        "❌ **Cookie extraction failed.**\n\n"
                        "**Fix:** Close Chrome completely, then try again — OR use the "
                        "**Manual Authentication** section above to upload a `cookies.txt` file."
                    )
                elif age_restricted:
                    st.error(
                        "❌ **Age-restricted or sign-in required video.**\n\n"
                        "Export your YouTube cookies and upload via **Manual Authentication** above."
                    )
                elif bot_detected:
                    st.error(
                        "❌ **YouTube blocked the download (bot detection / rate limit).**\n\n"
                        "Try: upload `cookies.txt` from a logged-in YouTube session, or try a "
                        "different/public video."
                    )
                else:
                    st.error(f"❌ Download error: {e}")

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
                if h["isl_video"] and os.path.exists(h["isl_video"]):
                    st.video(h["isl_video"])
                    with open(h["isl_video"], "rb") as f:
                        st.download_button(f"⬇ Download ISL #{i+1}", f, file_name=f"isl_{i+1}.mp4")

