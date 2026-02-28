import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from backend.parser import parse_resume
from backend.screener import screen_resume

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Screener",
    page_icon="🤖",
    layout="wide"
)

# ─────────────────────────────────────────────────────────────────────────────
# THEME STATE
# ─────────────────────────────────────────────────────────────────────────────
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

D = st.session_state.dark_mode

# ─────────────────────────────────────────────────────────────────────────────
# COLOUR TOKENS  — all black/white/grey, fully readable in both modes
# ─────────────────────────────────────────────────────────────────────────────
if D:
    APP_BG       = "#0d0d0d"
    SIDEBAR_BG   = "#111111"
    TEXT         = "#f2f2f2"       # headings / primary
    TEXT2        = "#c8c8c8"       # body
    TEXT3        = "#888888"       # muted / labels
    BORDER       = "#2a2a2a"
    CARD_BG      = "#1a1a1a"
    INPUT_BG     = "#161616"
    PLACEHOLDER  = "#555555"
    BTN_BG       = "#f2f2f2"
    BTN_TEXT     = "#0d0d0d"
    BTN_HOVER    = "#cccccc"
    # score colours — still monochrome, different weights
    SCORE_HIGH   = "#ffffff"
    SCORE_MID    = "#aaaaaa"
    SCORE_LOW    = "#555555"
    # tag — matched / missing
    TAG_M_BG     = "#252525"; TAG_M_BD = "#555555"; TAG_M_TX = "#e0e0e0"
    TAG_X_BG     = "#1a1a1a"; TAG_X_BD = "#333333"; TAG_X_TX = "#666666"
    # table
    TH_BG        = "#1e1e1e"
    TD_BG_A      = "#181818"
    TD_BG_B      = "#1c1c1c"
    # chart
    PAPER_BG     = "rgba(0,0,0,0)"
    PLOT_BG      = "rgba(0,0,0,0)"
    PLOT_TPL     = "plotly_dark"
    GRID_C       = "#2a2a2a"
    CHART_TEXT   = "#888888"
    BAR_SCALE    = [[0.0,"#333333"],[0.5,"#888888"],[1.0,"#f2f2f2"]]
    RADAR_FILL   = "rgba(242,242,242,0.07)"
    RADAR_LINE   = "rgba(242,242,242,0.65)"
    # toggle
    TOGGLE_LBL   = "☀️  Light Mode"
    CODE_COLOR   = "rgba(242,242,242,0.025)"
    GRID_BG      = "rgba(242,242,242,0.015)"
else:
    APP_BG       = "#f7f7f5"
    SIDEBAR_BG   = "#eeede9"
    TEXT         = "#111111"
    TEXT2        = "#333333"
    TEXT3        = "#777777"
    BORDER       = "#d0cec8"
    CARD_BG      = "#eeede9"
    INPUT_BG     = "#f2f0ec"
    PLACEHOLDER  = "#aaaaaa"
    BTN_BG       = "#111111"
    BTN_TEXT     = "#f7f7f5"
    BTN_HOVER    = "#333333"
    SCORE_HIGH   = "#111111"
    SCORE_MID    = "#555555"
    SCORE_LOW    = "#aaaaaa"
    TAG_M_BG     = "#e4e2dc"; TAG_M_BD = "#aaa9a4"; TAG_M_TX = "#1a1a1a"
    TAG_X_BG     = "#f0eeea"; TAG_X_BD = "#cccac4"; TAG_X_TX = "#888888"
    TH_BG        = "#e8e6e0"
    TD_BG_A      = "#f2f0ec"
    TD_BG_B      = "#eceae4"
    PAPER_BG     = "rgba(0,0,0,0)"
    PLOT_BG      = "rgba(0,0,0,0)"
    PLOT_TPL     = "plotly_white"
    GRID_C       = "#d8d6d0"
    CHART_TEXT   = "#777777"
    BAR_SCALE    = [[0.0,"#cccccc"],[0.5,"#777777"],[1.0,"#111111"]]
    RADAR_FILL   = "rgba(17,17,17,0.06)"
    RADAR_LINE   = "rgba(17,17,17,0.55)"
    TOGGLE_LBL   = "🌙  Dark Mode"
    CODE_COLOR   = "rgba(17,17,17,0.03)"
    GRID_BG      = "rgba(17,17,17,0.012)"

# ─────────────────────────────────────────────────────────────────────────────
# PURE-HTML TABLE  — zero pyarrow, zero st.dataframe / st.table
# ─────────────────────────────────────────────────────────────────────────────
def html_table(rows):
    if not rows:
        return ""
    headers = list(rows[0].keys())
    th = "".join(
        f"<th style='padding:10px 14px;text-align:left;font-size:0.82rem;"
        f"font-weight:600;letter-spacing:1px;text-transform:uppercase;"
        f"color:{TEXT3};border-bottom:1px solid {BORDER};'>{h}</th>"
        for h in headers
    )
    tbody = ""
    for i, row in enumerate(rows):
        bg = TD_BG_A if i % 2 == 0 else TD_BG_B
        tds = "".join(
            f"<td style='padding:10px 14px;color:{TEXT2};font-size:0.95rem;"
            f"border-bottom:1px solid {BORDER};'>{row[h]}</td>"
            for h in headers
        )
        tbody += f"<tr style='background:{bg};'>{tds}</tr>"
    return (
        f"<div style='overflow-x:auto;border:1px solid {BORDER};"
        f"border-radius:12px;overflow:hidden;'>"
        f"<table style='width:100%;border-collapse:collapse;background:{CARD_BG};'>"
        f"<thead style='background:{TH_BG};'><tr>{th}</tr></thead>"
        f"<tbody>{tbody}</tbody></table></div>"
    )

# ─────────────────────────────────────────────────────────────────────────────
# WATERMARK (blurred technical bg)
# ─────────────────────────────────────────────────────────────────────────────
WATERMARK = (
    "import resume_engine\\A"
    "from ai import Groq\\A"
    "\\A"
    "def screen(resume, jd):\\A"
    "    client = Groq()\\A"
    "    result = client\\A"
    "    .analyze(resume)\\A"
    "    .match(jd)\\A"
    "    return result\\A"
    "\\A"
    "01 10 11 00 01 10\\A"
    "11 00 01 10 11 00\\A"
    "00 11 10 01 00 11"
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS  — keeps the original default system font (no custom imports)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>

/* ── APP BASE ── */
.stApp {{
    background-color: {APP_BG} !important;
    background-image:
        repeating-linear-gradient(0deg, transparent, transparent 48px,
            {GRID_BG} 48px, {GRID_BG} 49px),
        repeating-linear-gradient(90deg, transparent, transparent 48px,
            {GRID_BG} 48px, {GRID_BG} 49px);
    background-size: 49px 49px;
    color: {TEXT} !important;
    transition: background-color 0.3s, color 0.3s;
}}

/* ── BLURRED CODE WATERMARK ── */
.stApp::before {{
    content: '{WATERMARK}';
    white-space: pre;
    position: fixed; top: 0; left: 0;
    width: 100%; height: 100%;
    font-family: 'Courier New', monospace;
    font-size: 0.9rem;
    color: {CODE_COLOR};
    line-height: 2.4; letter-spacing: 3px;
    padding: 60px; pointer-events: none;
    z-index: 0; filter: blur(2px); overflow: hidden;
}}

/* ── SIDEBAR ── */
section[data-testid="stSidebar"] {{
    background: {SIDEBAR_BG} !important;
    border-right: 1px solid {BORDER} !important;
}}

/* ── HEADINGS ── */
h1 {{
    color: {TEXT} !important;
    text-align: center;
    font-size: 2.6rem !important;
}}
h2, h3 {{ color: {TEXT} !important; }}

/* ── MARKDOWN TEXT ── */
p, li, div {{ color: {TEXT2}; }}

/* ── TEXTAREA ── */
.stTextArea textarea {{
    background: {INPUT_BG} !important;
    color: {TEXT} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    transition: border-color 0.2s !important;
}}
.stTextArea textarea:focus {{
    border-color: {TEXT3} !important;
    box-shadow: none !important;
}}
.stTextArea textarea::placeholder {{
    color: {PLACEHOLDER} !important;
}}

/* ── FILE UPLOADER ── */
div[data-testid="stFileUploader"] {{
    background: {INPUT_BG} !important;
    border: 1px dashed {BORDER} !important;
    border-radius: 12px !important;
    transition: border-color 0.2s !important;
}}
div[data-testid="stFileUploader"]:hover {{
    border-color: {TEXT3} !important;
}}

/* ── PRIMARY BUTTON (Analyze) ── */
div[data-testid="stButton"] button[kind="primary"],
div[data-testid="stButton"] button {{
    background: {BTN_BG} !important;
    color: {BTN_TEXT} !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: 1px !important;
    transition: background 0.2s, transform 0.15s !important;
}}
div[data-testid="stButton"] button:hover {{
    background: {BTN_HOVER} !important;
    transform: translateY(-1px) !important;
}}

/* ── METRICS ── */
div[data-testid="stMetric"] {{
    background: {CARD_BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    padding: 14px 16px !important;
}}
div[data-testid="stMetricValue"] {{
    color: {TEXT} !important;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
}}
div[data-testid="stMetricLabel"] {{
    color: {TEXT3} !important;
    font-size: 0.75rem !important;
    letter-spacing: 1px !important;
}}

/* ── EXPANDER ── */
div[data-testid="stExpander"] {{
    background: {CARD_BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    margin-bottom: 12px !important;
}}
div[data-testid="stExpander"]:hover {{
    border-color: {TEXT3} !important;
}}

/* ── PROGRESS BAR ── */
div[data-testid="stProgressBar"] > div > div {{
    background: {TEXT} !important;
    border-radius: 4px !important;
}}
div[data-testid="stProgressBar"] > div {{
    background: {BORDER} !important;
    border-radius: 4px !important;
}}

/* ── ALERTS ── */
div[data-testid="stAlert"] {{
    background: {CARD_BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    color: {TEXT} !important;
}}

/* ── SCORE DISPLAY ── */
.score-high {{ color: {SCORE_HIGH}; font-size: 2.8rem; font-weight: bold; }}
.score-mid  {{ color: {SCORE_MID};  font-size: 2.8rem; font-weight: bold; }}
.score-low  {{ color: {SCORE_LOW};  font-size: 2.8rem; font-weight: bold; }}

/* ── SKILL TAGS ── */
.tag {{
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    margin: 4px;
    font-size: 0.82rem;
    font-weight: 600;
}}
.tag-match   {{ background:{TAG_M_BG}; color:{TAG_M_TX}; border:1px solid {TAG_M_BD}; }}
.tag-missing {{ background:{TAG_X_BG}; color:{TAG_X_TX}; border:1px solid {TAG_X_BD}; }}

/* ── HORIZONTAL RULE ── */
hr {{ border-color: {BORDER} !important; }}

/* ── SCROLLBAR ── */
::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: {BORDER}; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: {TEXT3}; }}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(f"# 🤖 AI Resume Screener")
st.markdown(
    f"<p style='text-align:center; color:{TEXT3}; font-size:1.1rem'>"
    f"Powered by Gen Ai &nbsp;·&nbsp; Smart Hiring Assistant</p>",
    unsafe_allow_html=True
)
st.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR — theme toggle + status
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f"<div style='font-size:0.78rem;letter-spacing:3px;color:{TEXT3};"
        f"text-transform:uppercase;padding:14px 0 8px;'>Appearance</div>",
        unsafe_allow_html=True
    )
    if st.button(TOGGLE_LBL, key="theme_btn"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()

    st.markdown(f"<hr style='border-color:{BORDER};margin:14px 0;'>", unsafe_allow_html=True)

    st.markdown(
        f"<div style='font-size:0.78rem;letter-spacing:3px;color:{TEXT3};"
        f"text-transform:uppercase;margin-bottom:10px;'>System Status</div>",
        unsafe_allow_html=True
    )

    import os
    groq_key = os.getenv("GROQ_API_KEY", "")
    dot_on  = f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:{TEXT};margin-right:8px;'></span>"
    dot_off = f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:{BORDER};margin-right:8px;'></span>"

    if groq_key:
        st.markdown(f"<div style='color:{TEXT2};font-size:0.9rem;margin:6px 0;'>{dot_on}Gen Ai API &nbsp;·&nbsp; Online</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='color:{TEXT3};font-size:0.9rem;margin:6px 0;'>{dot_off}Gen Ai API &nbsp;·&nbsp; Offline</div>", unsafe_allow_html=True)
        st.markdown(f"<a href='https://console.groq.com' target='_blank' style='color:{TEXT3};font-size:0.88rem;'>→ Get free API key</a>", unsafe_allow_html=True)

    st.markdown(f"<hr style='border-color:{BORDER};margin:14px 0;'>", unsafe_allow_html=True)

    st.markdown(
        f"<div style='font-size:0.78rem;letter-spacing:3px;color:{TEXT3};"
        f"text-transform:uppercase;margin-bottom:12px;'>How to Use</div>"
        f"<div style='font-size:0.95rem;color:{TEXT2};line-height:2.2;'>"
        f"1. Paste job description<br>"
        f"2. Upload resume files<br>"
        f"3. Click Analyze button<br>"
        f"4. Review AI results</div>",
        unsafe_allow_html=True
    )

    st.markdown(f"<hr style='border-color:{BORDER};margin:14px 0;'>", unsafe_allow_html=True)

    st.markdown(
        f"<div style='font-size:0.78rem;letter-spacing:3px;color:{TEXT3};"
        f"text-transform:uppercase;margin-bottom:10px;'>Formats</div>"
        f"<div style='display:flex;gap:8px;'>"
        f"<span style='border:1px solid {BORDER};padding:2px 10px;border-radius:4px;font-size:0.8rem;color:{TEXT2};'>PDF</span>"
        f"<span style='border:1px solid {BORDER};padding:2px 10px;border-radius:4px;font-size:0.8rem;color:{TEXT2};'>DOCX</span>"
        f"<span style='border:1px solid {BORDER};padding:2px 10px;border-radius:4px;font-size:0.8rem;color:{TEXT2};'>TXT</span>"
        f"</div>",
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────────────────────────────────────
# TWO-COLUMN INPUT  — same layout as original
# ─────────────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown(f"### 📋 Job Description")
    job_desc = st.text_area(
        label="",
        placeholder="Paste the job description here...\n\nExample: We are looking for a Python Developer with 2+ years experience in Django, REST APIs, PostgreSQL...",
        height=300
    )

with col2:
    st.markdown(f"### 📄 Upload Resumes")
    uploaded_files = st.file_uploader(
        label="",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        help="Upload one or multiple resumes in PDF, DOCX, or TXT format"
    )
    if uploaded_files:
        st.success(f"✅ {len(uploaded_files)} resume(s) uploaded!")
        for f in uploaded_files:
            st.markdown(f"📎 `{f.name}`")

st.markdown("---")


# ─────────────────────────────────────────────────────────────────────────────
# ANALYZE BUTTON  — same position as original
# ─────────────────────────────────────────────────────────────────────────────
col_btn = st.columns([1, 2, 1])[1]
with col_btn:
    analyze_btn = st.button("🔍 Analyze Resumes", use_container_width=True, type="primary")


# ─────────────────────────────────────────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────────────────────────────────────────
if analyze_btn:
    if not job_desc.strip():
        st.error("⚠️ Please enter a job description!")
    elif not uploaded_files:
        st.error("⚠️ Please upload at least one resume!")
    else:
        results = []
        progress = st.progress(0, text="Analyzing resumes...")

        for i, file in enumerate(uploaded_files):
            with st.spinner(f"Screening **{file.name}**..."):
                resume_text = parse_resume(file)
                if not resume_text:
                    st.warning(f"Could not parse {file.name}")
                    continue
                result = screen_resume(resume_text, job_desc)
                result["filename"] = file.name
                results.append(result)
            progress.progress((i + 1) / len(uploaded_files), text=f"Done: {file.name}")

        progress.empty()

        if not results:
            st.error("No results generated. Check your files and API key.")
            st.stop()

        # Sort highest first
        results.sort(key=lambda x: x.get("match_score", 0), reverse=True)

        st.markdown(f"## 📊 Screening Results")

        # ── Summary table — pure HTML, no pyarrow ────────────────────────────
        summary_data = [{
            "Resume":         r["filename"],
            "Match Score":    f"{r['match_score']} / 100",
            "Experience":     r["experience_relevance"],
            "Education":      r["education_fit"],
            "Recommendation": r["recommendation"]
        } for r in results]

        st.markdown(html_table(summary_data), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Bar chart — uses go.Bar, no px.bar + DataFrame ───────────────────
        if len(results) > 1:
            names  = [r["filename"] for r in results]
            scores = [r["match_score"] for r in results]

            fig = go.Figure()
            for name, score in zip(names, scores):
                fig.add_trace(go.Bar(
                    x=[name], y=[score],
                    text=[f"{score}/100"],
                    textposition="outside",
                    textfont=dict(color=CHART_TEXT, size=12),
                    marker=dict(
                        color=score,
                        colorscale=BAR_SCALE,
                        cmin=0, cmax=100,
                        line=dict(width=0)
                    ),
                    showlegend=False
                ))
            fig.update_layout(
                title=dict(text="📈 Match Score Comparison", font=dict(color=TEXT, size=16)),
                paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
                template=PLOT_TPL,
                font=dict(color=CHART_TEXT, size=12),
                xaxis=dict(gridcolor=GRID_C, title=""),
                yaxis=dict(gridcolor=GRID_C, range=[0, 118], title=""),
                barmode="group",
                margin=dict(t=40, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)

        # ── Individual detail cards ───────────────────────────────────────────
        st.markdown(f"## 🧾 Detailed Analysis")

        for r in results:
            score = r["match_score"]
            score_class = "score-high" if score >= 70 else ("score-mid" if score >= 45 else "score-low")
            rec_emoji = "🟢" if r["recommendation"] == "Shortlist" else ("🟡" if r["recommendation"] == "Consider" else "🔴")

            with st.expander(
                f"{rec_emoji} {r['filename']}  —  Score: {score}/100",
                expanded=(score >= 70)
            ):
                c1, c2, c3 = st.columns(3)
                c1.metric("Match Score",          f"{score}/100")
                c2.metric("Experience Relevance", r["experience_relevance"])
                c3.metric("Recommendation",       r["recommendation"])

                # ── Radar chart ──────────────────────────────────────────────
                categories = ["Skills Match", "Experience", "Education", "Overall"]
                exp_map = {"High": 90, "Medium": 60, "Low": 30}
                edu_map = {"Good": 90, "Average": 60, "Poor": 30}
                vals = [
                    score,
                    exp_map.get(r.get("experience_relevance"), 50),
                    edu_map.get(r.get("education_fit"), 50),
                    score
                ]

                fig2 = go.Figure(go.Scatterpolar(
                    r=vals + [vals[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                    fillcolor=RADAR_FILL,
                    line=dict(color=RADAR_LINE, width=1.5)
                ))
                fig2.update_layout(
                    polar=dict(
                        bgcolor="rgba(0,0,0,0)",
                        radialaxis=dict(
                            visible=True, range=[0, 100],
                            gridcolor=GRID_C, linecolor=GRID_C,
                            tickfont=dict(color=CHART_TEXT, size=9)
                        ),
                        angularaxis=dict(
                            gridcolor=GRID_C, linecolor=GRID_C,
                            tickfont=dict(color=TEXT2, size=11)
                        )
                    ),
                    paper_bgcolor=PAPER_BG,
                    template=PLOT_TPL,
                    height=300,
                    showlegend=False,
                    margin=dict(t=20, b=20, l=50, r=50)
                )
                st.plotly_chart(fig2, use_container_width=True)

                # ── Skills ────────────────────────────────────────────────────
                col_s1, col_s2 = st.columns(2)

                with col_s1:
                    st.markdown(f"<b style='color:{TEXT}'>✅ Matched Skills</b>", unsafe_allow_html=True)
                    matched = r.get("skills_matched", [])
                    tags = " ".join(
                        f'<span class="tag tag-match">{s}</span>' for s in matched
                    )
                    st.markdown(tags if tags else f"<span style='color:{TEXT3}'>None found</span>", unsafe_allow_html=True)

                with col_s2:
                    st.markdown(f"<b style='color:{TEXT}'>❌ Missing Skills</b>", unsafe_allow_html=True)
                    missing = r.get("skills_missing", [])
                    tags = " ".join(
                        f'<span class="tag tag-missing">{s}</span>' for s in missing
                    )
                    st.markdown(tags if tags else f"<span style='color:{TEXT3}'>None missing</span>", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Strengths / Weaknesses ────────────────────────────────────
                col_w1, col_w2 = st.columns(2)
                with col_w1:
                    st.markdown(f"<b style='color:{TEXT}'>💪 Strengths</b>", unsafe_allow_html=True)
                    for s in r.get("strengths", []):
                        st.markdown(
                            f"<div style='padding:6px 12px;margin:4px 0;border-left:2px solid {TEXT3};"
                            f"color:{TEXT2};font-size:0.95rem;'>{s}</div>",
                            unsafe_allow_html=True
                        )
                with col_w2:
                    st.markdown(f"<b style='color:{TEXT}'>⚠️ Improvement Areas</b>", unsafe_allow_html=True)
                    for w in r.get("weaknesses", []):
                        st.markdown(
                            f"<div style='padding:6px 12px;margin:4px 0;border-left:2px solid {BORDER};"
                            f"color:{TEXT2};font-size:0.95rem;'>{w}</div>",
                            unsafe_allow_html=True
                        )

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Summary ───────────────────────────────────────────────────
                st.markdown(
                    f"<div style='background:{CARD_BG};border:1px solid {BORDER};"
                    f"border-radius:10px;padding:14px 18px;color:{TEXT2};"
                    f"font-size:0.98rem;line-height:1.75;'>"
                    f"<b style='color:{TEXT}'>📝 AI Summary</b><br><br>"
                    f"{r.get('summary', 'No summary available.')}</div>",
                    unsafe_allow_html=True
                )
                st.markdown("")


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<div style='text-align:center;color:{TEXT3};font-size:0.82rem;letter-spacing:2px;padding:8px 0;'>"
    f"AI Resume Screener &nbsp;·&nbsp; Gen Ai &nbsp;·&nbsp; Streamlit</div>",
    unsafe_allow_html=True
)