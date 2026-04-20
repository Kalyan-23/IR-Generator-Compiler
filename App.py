"""
App.py — Intermediate Code Generator Toolkit
----------------------------------------------
Compiler Design project.
Run:  streamlit run App.py

What's in here:
  - Sidebar navigation with 3 sections
  - Visual SVG AST tree + text tree
  - Postfix (RPN) with step-by-step
  - TAC: Quadruples, Triples, Indirect Triples
  - Token Inspector tab inside AST view
"""

import base64
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from Lexer      import tokenize, LexerError
from Parser     import parse, ParseError, program_to_text
from Postfix    import to_postfix
from Codegen    import generate_tac, as_quadruples, as_triples, as_indirect_triples
from ast_visual import render_ast_svg, render_ast_text

# ── page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ICG Toolkit",
    page_icon=":material/account_tree:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600&family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Manrope:wght@400;500;600;700&display=swap');

:root {
    --bg:       #f4efe6;
    --paper:    #fffaf0;
    --card:     #fbf4e8;
    --card2:    #efe3d0;
    --ink:      #18212b;
    --border:   #d9c9af;
    --accent:   #0f6d68;
    --blue:     #205f8f;
    --orange:   #b85f28;
    --purple:   #6e5b8f;
    --yellow:   #9b6b16;
    --red:      #b23a36;
    --pink:     #a44b66;
    --text:     #22303a;
    --muted:    #6d746f;
    --mono:     'IBM Plex Mono', monospace;
    --sans:     'Manrope', sans-serif;
    --display:  'Fraunces', serif;
}

html, body, [class*="css"] {
    background: var(--bg) !important;
    color: var(--text);
    font-family: var(--sans);
}
.stApp {
    background:
      radial-gradient(circle at 12% 6%, rgba(15,109,104,0.11), transparent 27rem),
      radial-gradient(circle at 88% 4%, rgba(184,95,40,0.12), transparent 24rem),
      linear-gradient(135deg, #f8f0df 0%, #f3eadb 48%, #ede4d2 100%) !important;
}
#MainMenu, header { visibility: visible; }
footer { visibility: hidden; }
[data-testid="stHeader"] {
    background: transparent !important;
}
[data-testid="stSidebarCollapsedControl"] button,
[data-testid="stSidebarCollapseButton"] button {
    width: 42px !important;
    height: 42px !important;
    min-width: 42px !important;
    padding: 0 !important;
    background-color: transparent !important;
    background-image:
      linear-gradient(#000000, #000000),
      linear-gradient(#000000, #000000),
      linear-gradient(#000000, #000000) !important;
    background-size: 22px 2.5px, 22px 2.5px, 22px 2.5px !important;
    background-position: center 13px, center 20px, center 27px !important;
    background-repeat: no-repeat !important;
    box-shadow: none !important;
    border: none !important;
    border-radius: 10px !important;
    color: #000000 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    position: relative !important;
}
[data-testid="stSidebarCollapseButton"] button {
    background-image:
      linear-gradient(#ffffff, #ffffff),
      linear-gradient(#ffffff, #ffffff),
      linear-gradient(#ffffff, #ffffff) !important;
    color: #ffffff !important;
}
[data-testid="stSidebarCollapsedControl"] {
    transform: translate(-20px, -6px) !important;
}
[data-testid="stSidebarCollapsedControl"] button:hover,
[data-testid="stSidebarCollapseButton"] button:hover {
    background-color: rgba(255,250,240,0.14) !important;
}
[data-testid="stSidebarCollapsedControl"] button svg,
[data-testid="stSidebarCollapseButton"] button svg {
    opacity: 0 !important;
    color: #000000 !important;
    fill: #000000 !important;
    stroke: #000000 !important;
}
.block-container {
    padding: 3rem 1.6rem 3rem !important;
    max-width: 1240px !important;
}
@media (max-width: 768px) {
    .block-container { padding: 2.1rem 0.75rem 2rem !important; }
    [data-testid="stSidebarCollapsedControl"] {
        transform: translate(2px, 4px) !important;
    }
    [data-testid="stSidebarCollapsedControl"] button,
    [data-testid="stSidebarCollapseButton"] button {
        width: 38px !important;
        height: 38px !important;
        min-width: 38px !important;
        background-size: 20px 2.4px, 20px 2.4px, 20px 2.4px !important;
        background-position: center 11px, center 18px, center 25px !important;
    }
}

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #bba98f; border-radius: 3px; }

/* sidebar */
[data-testid="stSidebar"] {
    background:
      linear-gradient(180deg, #263238 0%, #1f2a30 100%) !important;
    border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] * { color: #f8efe0 !important; }
[data-testid="stSidebar"] .stRadio label {
    font-size: 0.94rem !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(248,239,224,0.18) !important; }
.side-brand {
    border: 1px solid rgba(248,239,224,0.16);
    border-radius: 18px;
    padding: 1rem;
    margin-bottom: 1.1rem;
    background: rgba(255,255,255,0.045);
    display: flex;
    align-items: center;
    gap: 0.8rem;
}
@media (max-width: 420px) {
    .side-brand {
        padding: 0.85rem;
        gap: 0.7rem;
    }
    .side-icon {
        width: 38px;
        height: 38px;
        flex-basis: 38px;
    }
    .side-title {
        font-size: 1.28rem;
        letter-spacing: 0;
    }
    .side-sub {
        font-size: 0.58rem;
        letter-spacing: 0.08em;
    }
}
.side-icon {
    width: 42px;
    height: 42px;
    border-radius: 14px;
    display: grid;
    place-items: center;
    flex: 0 0 42px;
    background: #fffaf0;
    border: 1px solid rgba(248,239,224,0.24);
    box-shadow: 0 12px 26px rgba(0,0,0,0.16);
}
.side-icon svg {
    width: 25px;
    height: 25px;
    color: #263238 !important;
}
.side-icon svg path {
    stroke: #263238 !important;
}
.side-copy {
    min-width: 0;
}
.side-title {
    font-family: var(--display);
    font-size: 1.55rem;
    line-height: 1;
    letter-spacing: -0.03em;
}
.side-sub {
    color: #cbbfae !important;
    font-family: var(--mono);
    font-size: 0.68rem;
    letter-spacing: 0.1em;
    margin-top: 0.45rem;
    text-transform: uppercase;
}

/* page title */
.hero {
    background: rgba(255,250,240,0.78);
    border: 1px solid rgba(217,201,175,0.86);
    border-radius: 28px;
    box-shadow: 0 22px 60px rgba(60,45,25,0.11);
    padding: clamp(1.1rem, 2.3vw, 1.65rem);
    margin: 0.75rem 0 1.1rem;
    position: relative;
    overflow: hidden;
}
.hero:after {
    content: "";
    position: absolute;
    width: 260px;
    height: 260px;
    right: -110px;
    top: -130px;
    background: rgba(15,109,104,0.12);
    border-radius: 50%;
}
.eyebrow {
    color: var(--orange);
    font-family: var(--mono);
    font-size: 0.72rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.page-title {
    font-family: var(--display);
    font-size: clamp(2.05rem, 5vw, 4rem);
    font-weight: 700;
    letter-spacing: -0.055em;
    color: var(--ink);
    line-height: 1.1;
}
.page-sub {
    color: var(--muted);
    font-size: clamp(0.9rem, 1.8vw, 1rem);
    max-width: 660px;
    margin-top: 0.45rem;
    line-height: 1.7;
}
.divider {
    height: 1px;
    background: linear-gradient(90deg, var(--accent), rgba(15,109,104,0.12), transparent 70%);
    margin: 1rem 0 1rem;
}

/* feature pill */
.feat-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    max-width: 100%;
    background: #eef6f2;
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 0.35rem 0.85rem;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--accent);
    line-height: 1.35;
    white-space: normal;
}
@media (max-width: 520px) {
    .hero {
        border-radius: 20px;
        padding: 1rem;
    }
    .hero:after {
        width: 180px;
        height: 180px;
        right: -105px;
        top: -95px;
    }
    .page-title {
        font-size: 2.25rem;
        letter-spacing: 0;
    }
    .page-sub {
        line-height: 1.55;
    }
    .feat-pill {
        border-radius: 14px;
        padding: 0.45rem 0.7rem;
        font-size: 0.76rem;
    }
}

/* section label */
.sec-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.13em;
    text-transform: uppercase;
    color: #7a6751;
    margin-bottom: 0.55rem;
}

/* textarea */
.stTextArea textarea {
    background: rgba(255,250,240,0.92) !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    color: var(--text) !important;
    font-family: var(--mono) !important;
    font-size: clamp(0.77rem, 1.7vw, 0.9rem) !important;
    line-height: 1.7 !important;
    caret-color: var(--accent);
}
.stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(15,109,104,0.12) !important;
}

/* button */
.stButton > button {
    background: #0f6d68 !important;
    color: #fffaf0 !important;
    font-family: var(--sans) !important;
    font-weight: 700 !important;
    font-size: clamp(0.8rem, 1.9vw, 0.93rem) !important;
    border: none !important;
    border: 1px solid #0b5652 !important;
    border-radius: 14px !important;
    padding: 0.72rem 1.4rem !important;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    width: 100%;
    box-shadow: 0 12px 26px rgba(15,109,104,0.22);
    transition: background 0.18s, transform 0.14s, box-shadow 0.18s;
}
.stButton > button:hover {
    background: #0b5f5b !important;
    transform: translateY(-2px);
    box-shadow: 0 16px 30px rgba(15,109,104,0.25);
}

/* SVG tree wrapper */
.svg-scroll {
    overflow-x: auto;
    overflow-y: auto;
    max-height: 520px;
    background: #fffaf0;
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 0.75rem;
}

/* legend */
.legend {
    display: flex;
    flex-wrap: wrap;
    gap: 0.6rem;
    margin: 0.7rem 0;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    font-family: var(--mono);
    font-size: 0.74rem;
    color: var(--muted);
}
.legend-dot {
    width: 11px; height: 11px;
    border-radius: 50%;
    flex-shrink: 0;
    border: 2px solid;
}

/* text tree block */
.ast-text {
    background: rgba(255,250,240,0.92);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1rem 1.2rem;
    font-family: var(--mono);
    font-size: clamp(0.72rem, 1.7vw, 0.83rem);
    line-height: 2;
    white-space: pre;
    overflow-x: auto;
    color: var(--text);
}

/* token table */
.tbl-wrap { overflow-x: auto; }
.data-tbl {
    width: 100%;
    border-collapse: collapse;
    font-family: var(--mono);
    font-size: clamp(0.7rem, 1.6vw, 0.81rem);
    min-width: 300px;
}
.data-tbl th {
    background: #efe3d0;
    color: var(--muted);
    padding: 0.42rem 0.85rem;
    text-align: left;
    font-size: 0.64rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
}
.data-tbl td {
    padding: 0.32rem 0.85rem;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
}
.data-tbl tr:last-child td { border-bottom: none; }
.data-tbl tr:hover td { background: rgba(255,255,255,0.025); }
.data-tbl .idx  { color: var(--muted); }
.data-tbl .cop  { color: var(--yellow); font-weight: 600; }
.data-tbl .carg { color: var(--blue); }
.data-tbl .cres { color: var(--accent); font-weight: 600; }
.data-tbl .cptr { color: var(--purple); }

/* metrics */
.metric-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin-bottom: 1.1rem;
}
.metric {
    flex: 1 1 65px;
    min-width: 60px;
    background: rgba(255,250,240,0.88);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 0.65rem 0.8rem;
    text-align: center;
}
.metric-val {
    font-size: clamp(1.15rem, 3.2vw, 1.55rem);
    font-weight: 700;
    color: var(--accent);
    line-height: 1;
}
.metric-lbl {
    font-size: 0.6rem;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 0.09em;
    margin-top: 0.18rem;
}

/* step cards */
.step-card {
    background: rgba(255,250,240,0.9);
    border: 1px solid var(--border);
    border-left: 3px solid var(--orange);
    border-radius: 14px;
    padding: 0.68rem 0.95rem;
    margin-bottom: 0.42rem;
    display: flex;
    gap: 0.7rem;
    align-items: flex-start;
}
.step-card.cse { border-left-color: var(--purple); opacity: 0.78; }
.step-num {
    background: var(--orange);
    color: #fffaf0;
    font-weight: 700;
    font-size: 0.68rem;
    border-radius: 8px;
    padding: 0.08rem 0.42rem;
    min-width: 1.6rem;
    text-align: center;
    flex-shrink: 0;
    margin-top: 0.13rem;
}
.step-sep {
    color: var(--muted);
    font-family: var(--mono);
    font-size: 0.71rem;
    border-top: 1px dashed var(--border);
    padding-top: 0.38rem;
    margin: 0.28rem 0;
}
.step-instr { font-family: var(--mono); font-size: clamp(0.74rem, 1.7vw, 0.84rem); }
.step-note  { font-family: var(--mono); font-size: 0.71rem; color: var(--muted); margin-top: 0.1rem; }

/* badges */
.badge {
    display: inline-block;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.09em;
    text-transform: uppercase;
    border-radius: 4px;
    padding: 0.1rem 0.45rem;
    margin-left: 0.38rem;
    vertical-align: middle;
}
.badge-ok  { background: rgba(56,232,176,0.12); color: var(--accent); }
.badge-cse { background: rgba(167,139,250,0.15); color: var(--purple); }
.badge-tok { background: rgba(91,164,245,0.12);  color: var(--blue); }

/* postfix pills */
.token-row { display: flex; flex-wrap: wrap; gap: 0.38rem; margin: 0.55rem 0; }
.tok-pill {
    font-family: var(--mono);
    font-size: clamp(0.72rem, 1.7vw, 0.83rem);
    border-radius: 999px;
    padding: 0.22rem 0.58rem;
    border: 1px solid transparent;
}
.tok-pill.operand  { background: rgba(91,164,245,0.1);  border-color: rgba(91,164,245,0.28);  color: var(--blue);   }
.tok-pill.operator { background: rgba(251,191,36,0.1);  border-color: rgba(251,191,36,0.28);  color: var(--yellow); }
.tok-pill.assign   { background: rgba(56,232,176,0.1);  border-color: rgba(56,232,176,0.28);  color: var(--accent); }
.tok-pill.unary    { background: rgba(244,114,182,0.1); border-color: rgba(244,114,182,0.28); color: var(--pink);   }

/* error box */
.err-box {
    background: rgba(248,113,113,0.07);
    border: 1px solid var(--red);
    border-radius: 16px;
    padding: 0.85rem 1.1rem;
    color: #fca5a5;
    font-family: var(--mono);
    font-size: clamp(0.74rem, 1.7vw, 0.85rem);
    word-break: break-word;
}

/* empty state */
.empty {
    background: rgba(255,250,240,0.62);
    border: 1px dashed #c8b89e;
    border-radius: 22px;
    color: var(--muted);
    font-size: 0.95rem;
    padding: 2.2rem 1.4rem;
    line-height: 1.9;
}

/* info box */
.info-box {
    background: rgba(32,95,143,0.08);
    border: 1px solid rgba(32,95,143,0.24);
    border-radius: 14px;
    padding: 0.7rem 1rem;
    color: #1f557b;
    font-family: var(--mono);
    font-size: 0.78rem;
    margin-bottom: 0.8rem;
    line-height: 1.6;
}

/* tabs */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(239,227,208,0.72) !important;
    border-radius: 16px;
    padding: 0.22rem;
    border: 1px solid var(--border);
    flex-wrap: wrap;
    gap: 2px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    border-radius: 12px !important;
    font-family: var(--sans) !important;
    font-size: clamp(0.71rem, 1.7vw, 0.82rem) !important;
    font-weight: 600 !important;
    padding: 0.3rem 0.78rem !important;
    white-space: nowrap;
}
.stTabs [aria-selected="true"] {
    background: var(--accent) !important;
    color: #fffaf0 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 0.9rem !important; }

/* checkbox + radio */
.stCheckbox label, .stRadio label {
    color: var(--text) !important;
    font-size: 0.87rem !important;
}
.stCheckbox label p,
.stCheckbox label span,
.stCheckbox [data-testid="stMarkdownContainer"] p {
    color: #263238 !important;
    font-weight: 700 !important;
}
.st-key-show_text_tree label p,
.st-key-show_tokens_tab label p,
.st-key-show_steps_pf label p,
.st-key-show_steps_tac label p,
.st-key-show_cse_steps label p,
.st-key-show_text_tree [data-testid="stMarkdownContainer"] p,
.st-key-show_tokens_tab [data-testid="stMarkdownContainer"] p,
.st-key-show_steps_pf [data-testid="stMarkdownContainer"] p,
.st-key-show_steps_tac [data-testid="stMarkdownContainer"] p,
.st-key-show_cse_steps [data-testid="stMarkdownContainer"] p {
    color: var(--accent) !important;
    font-weight: 700 !important;
}
.plain-text-label {
    color: var(--blue);
    font-weight: 800;
}
.st-key-q_plain label p,
.st-key-t_plain label p {
    color: var(--blue) !important;
    font-weight: 700 !important;
}
.option-row {
    display: flex;
    align-items: center;
    min-height: 1.75rem;
    font-size: 0.87rem;
    font-weight: 700;
    margin-top: 0;
}
.option-row.step-label,
.option-row.cse-label { color: var(--accent); }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def show_error(kind: str, msg: str):
    icons = {"Lexer": "🔴", "Parse": "🟠"}
    st.markdown(
        f'<div class="err-box">{icons.get(kind,"⚠️")} '
        f'<strong>{kind} Error</strong><br>{esc(str(msg))}</div>',
        unsafe_allow_html=True
    )

def metric_html(*pairs) -> str:
    """Build a metrics row from (value, label) pairs."""
    cards = ""
    for val, lbl in pairs:
        cards += (f'<div class="metric">'
                  f'<div class="metric-val">{val}</div>'
                  f'<div class="metric-lbl">{lbl}</div></div>')
    return f'<div class="metric-row">{cards}</div>'

def colored_checkbox(label: str, color_class: str, value: bool, key: str) -> bool:
    check_col, label_col = st.columns([0.08, 0.92], gap="small")
    with check_col:
        checked = st.checkbox(label, value=value, key=key, label_visibility="collapsed")
    with label_col:
        st.markdown(f'<div class="option-row {color_class}">{esc(label)}</div>', unsafe_allow_html=True)
    return checked


def render_svg_component(svg: str, height: int = 540):
    """Render SVG as an image to avoid Streamlit frontend HTML rendering issues."""
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    st.image(f"data:image/svg+xml;base64,{encoded}", use_container_width=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div class="side-brand">
      <div class="side-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M7 6.5 3 12l4 5.5" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M17 6.5 21 12l-4 5.5" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M14 5 10 19" stroke="currentColor" stroke-width="2.3" stroke-linecap="round"/>
        </svg>
      </div>
      <div class="side-copy">
        <div class="side-title">ICG Studio</div>
        <div class="side-sub">Compiler Design Workbench</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    feature = st.radio(
        "nav",
        ["Syntax Tree",
         "Postfix Notation",
         "Three Address Code"],
        label_visibility="collapsed",
    )

    tac_mode = None
    if feature == "Three Address Code":
        st.markdown("---")
        st.markdown('<div style="font-size:0.78rem;font-weight:700;color:#cbbfae;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.4rem">TAC Format</div>', unsafe_allow_html=True)
        tac_mode = st.radio(
            "tac",
            ["Quadruple", "Triple", "Indirect Triple"],
            label_visibility="collapsed",
    )

    # color legend (shows on AST page)
    if feature == "Syntax Tree":
        st.markdown("---")
        st.markdown('<div style="font-size:0.78rem;font-weight:700;color:#cbbfae;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:0.5rem">Tree Legend</div>', unsafe_allow_html=True)
        legend_items = [
            ("#5ba4f5", "Assign  (=)"),
            ("#a78bfa", "BinOp  (op)"),
            ("#f472b6", "Unary  (-)"),
            ("#38e8b0", "Number"),
            ("#fbbf24", "Variable"),
        ]
        for color, label in legend_items:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem">'
                f'<div style="width:12px;height:12px;border-radius:50%;background:{color};flex-shrink:0"></div>'
                f'<span style="font-size:0.79rem;color:#e2eaf6">{label}</span></div>',
                unsafe_allow_html=True
            )


# ── Default inputs per feature ─────────────────────────────────────────────────

DEFAULTS = {
    "Syntax Tree":
        "a = b * -c + b * -c;\nx = (y - z) / w;\nresult = a + b * c;\n",
    "Postfix Notation":
        "a = b + c * d;\na*(b+c)/d\nneg = -b + c;\n",
    "Three Address Code":
        "a = b + c * d;\nx = (y - z) / w;\nresult = a * (b + c) / d;\ncse = b * -c + b * -c;\n",
}


# ── Page header ────────────────────────────────────────────────────────────────

feat_info = {
    "Syntax Tree":        ("AST", "Syntax Tree",        "Visual structure of parsed expressions"),
    "Postfix Notation":   ("RPN", "Postfix Notation",   "Stack-friendly Reverse Polish form"),
    "Three Address Code": ("TAC", "Three Address Code", f"{tac_mode or 'Quadruple'} view with triples and indirect triples"),
}
icon, fname, fdesc = feat_info[feature]

st.markdown(f"""
<div class="hero">
  <div class="eyebrow">Compiler Design Workbench</div>
  <div class="page-title">Intermediate Code Generator</div>
  <div class="page-sub">Type a small expression program, choose the representation you want, and inspect how the compiler pipeline reshapes it.</div>
  <div class="divider"></div>
  <div class="feat-pill">{icon} · {fname} &nbsp;|&nbsp; {fdesc}</div>
</div>
""", unsafe_allow_html=True)


# ── Two-column layout: input | output ──────────────────────────────────────────

col_in, col_out = st.columns([1, 1], gap="large")

with col_in:
    st.markdown('<div class="sec-label">Source Program</div>', unsafe_allow_html=True)
    source = st.text_area(
        "src",
        value=DEFAULTS[feature],
        height=195,
        label_visibility="collapsed",
        placeholder="e.g.  a = b + c * d;",
        key=f"src_{feature}",
    )

    # per-feature options
    if feature == "Syntax Tree":
        show_text_tree = st.checkbox("Also show text tree", value=True, key="show_text_tree")
        show_tokens_tab = st.checkbox("Show token stream", value=True, key="show_tokens_tab")

    elif feature == "Postfix Notation":
        show_steps_pf = st.checkbox("Show step-by-step", value=True, key="show_steps_pf")

    elif feature == "Three Address Code":
        show_steps_tac = st.checkbox("Show step-by-step", value=True, key="show_steps_tac")
        show_cse_steps = st.checkbox("Highlight CSE reuses", value=True, key="show_cse_steps")

    run = st.button(f"Build {fname}", use_container_width=True)


# ── Output panel ───────────────────────────────────────────────────────────────

with col_out:
    if not run:
        st.markdown(f"""
        <div class="empty">
          Choose an output view, edit the source program,<br>
          then click <strong style="color:var(--accent)">Build {fname}</strong>.
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # parse input
    try:
        stmts, tokens = parse(source.strip())
    except LexerError as e:
        show_error("Lexer", e); st.stop()
    except ParseError as e:
        show_error("Parse", e); st.stop()
    except Exception as e:
        show_error("Unexpected", e); st.stop()

    # base metrics (shown by all features)
    n_tok = len(tokens) - 1
    n_stm = len(stmts)
    st.markdown(metric_html((n_stm, "Statements"), (n_tok, "Tokens")), unsafe_allow_html=True)


    # ══════════════════════════════════════════════════════════════════════════
    # 1 ─ Syntax Tree
    # ══════════════════════════════════════════════════════════════════════════
    if feature == "Syntax Tree":

        tab_labels = ["Visual Tree"]
        if show_text_tree:   tab_labels.append("Text Tree")
        if show_tokens_tab:  tab_labels.append("Tokens")
        tabs = st.tabs(tab_labels)
        ti = 0

        # ── Visual SVG tree ────────────────────────────────────────────────
        with tabs[ti]:
            ti += 1
            st.markdown(
                '<div class="sec-label">Abstract Syntax Tree'
                '<span class="badge badge-ok">SVG</span></div>',
                unsafe_allow_html=True
            )

            svg = render_ast_svg(stmts)
            render_svg_component(svg)

            # quick legend row
            st.markdown("""
            <div class="legend">
              <div class="legend-item"><div class="legend-dot" style="background:#1e3a5f;border-color:#5ba4f5"></div>Assign</div>
              <div class="legend-item"><div class="legend-dot" style="background:#2d1b4e;border-color:#a78bfa"></div>BinOp</div>
              <div class="legend-item"><div class="legend-dot" style="background:#3b1f3b;border-color:#f472b6"></div>Unary&nbsp;-</div>
              <div class="legend-item"><div class="legend-dot" style="background:#1a3a2a;border-color:#38e8b0"></div>Number</div>
              <div class="legend-item"><div class="legend-dot" style="background:#2a2a1a;border-color:#fbbf24"></div>Variable</div>
            </div>
            """, unsafe_allow_html=True)

        # ── Text tree ──────────────────────────────────────────────────────
        if show_text_tree:
            with tabs[ti]:
                ti += 1
                text_tree = render_ast_text(stmts)
                st.markdown(f'<div class="ast-text">{esc(text_tree)}</div>', unsafe_allow_html=True)
                st.text_area("Copy", text_tree, height=120, key="ast_copy")

        # ── Token table ────────────────────────────────────────────────────
        if show_tokens_tab:
            with tabs[ti]:
                TCOL = {
                    "ID":"#e2eaf6",  "NUMBER":"#38e8b0",
                    "PLUS":"#fbbf24","MINUS":"#fbbf24",
                    "MUL":"#fbbf24", "DIV":"#fbbf24",
                    "ASSIGN":"#5ba4f5","SEMI":"#5a6a82",
                    "LPAREN":"#ff8c42","RPAREN":"#ff8c42",
                    "EOF":"#252d40",
                }
                rows = ""
                for t in tokens:
                    c = TCOL.get(t.type, "#e2eaf6")
                    rows += (f'<tr>'
                             f'<td style="color:{c};font-weight:600">{esc(t.type)}</td>'
                             f'<td class="carg">{esc(repr(t.value))}</td>'
                             f'<td class="idx">{t.line}</td>'
                             f'<td class="idx">{t.col}</td></tr>')
                st.markdown(
                    f'<div class="tbl-wrap"><table class="data-tbl">'
                    f'<thead><tr><th>Type</th><th>Value</th><th>Line</th><th>Col</th></tr></thead>'
                    f'<tbody>{rows}</tbody></table></div>',
                    unsafe_allow_html=True
                )


    # ══════════════════════════════════════════════════════════════════════════
    # 2 ─ Postfix Notation
    # ══════════════════════════════════════════════════════════════════════════
    elif feature == "Postfix Notation":

        postfix_str, pf_toks, pf_steps = to_postfix(stmts)

        tab_labels = ["Postfix Output"]
        if show_steps_pf: tab_labels.append("Step-by-Step")
        tabs = st.tabs(tab_labels)

        with tabs[0]:
            st.markdown(
                '<div class="sec-label">Postfix (RPN)'
                    '<span class="badge badge-ok">Ready</span></div>',
                unsafe_allow_html=True
            )

            # colour-coded token pills
            pills = ""
            for tok in pf_toks:
                if tok == "uminus":
                    cls = "unary"
                elif tok in ("+", "-", "*", "/"):
                    cls = "operator"
                elif tok == "=":
                    cls = "assign"
                else:
                    cls = "operand"
                pills += f'<span class="tok-pill {cls}">{esc(tok)}</span>'
            st.markdown(f'<div class="token-row">{pills}</div>', unsafe_allow_html=True)

            st.markdown('<div class="sec-label plain-text-label" style="margin-top:1rem">Plain text</div>', unsafe_allow_html=True)
            st.code(postfix_str, language="text")

            # short explanation
            st.markdown("""
            <div class="info-box">
              <strong>How to read postfix:</strong> operands come first, operator follows.<br>
              Stack-based evaluation: push operands, apply operator to top two items.<br>
              <code>uminus</code> = unary negation (pop one, push its negative).
            </div>
            """, unsafe_allow_html=True)

        if show_steps_pf and len(tabs) > 1:
            with tabs[1]:
                num = 0
                for s in pf_steps:
                    if s["type"] == "sep":
                        st.markdown(f'<div class="step-sep">{esc(s["note"])}</div>', unsafe_allow_html=True)
                        continue
                    num += 1
                    if s["token"] == "uminus":  cls = "unary"
                    elif s["type"] == "operator": cls = "operator"
                    elif s["token"] == "=":       cls = "assign"
                    else:                         cls = "operand"
                    pill = f'<span class="tok-pill {cls}">{esc(s["token"])}</span>'
                    st.markdown(f"""
                    <div class="step-card">
                      <div class="step-num">{num}</div>
                      <div>
                        <div class="step-instr">{pill}</div>
                        <div class="step-note">{esc(s["note"])}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)


    # ══════════════════════════════════════════════════════════════════════════
    # 3 ─ Three Address Code
    # ══════════════════════════════════════════════════════════════════════════
    elif feature == "Three Address Code":

        gen  = generate_tac(stmts)
        recs = gen.records

        cse_hits = sum(1 for s in gen.steps if s.get("cse"))
        n_temps  = sum(1 for r in recs if r.result.startswith("t"))

        st.markdown(
            metric_html((len(recs), "Instructions"), (n_temps, "Temporaries"), (cse_hits, "CSE Hits")),
            unsafe_allow_html=True
        )

        tab_labels = [tac_mode, "All Formats"]
        if show_steps_tac: tab_labels.append("Step-by-Step")
        tabs = st.tabs(tab_labels)

        # ── selected format ────────────────────────────────────────────────
        with tabs[0]:

            if tac_mode == "Quadruple":
                quads = as_quadruples(recs)
                st.markdown(
                    '<div class="sec-label">Quadruples'
                    '<span class="badge badge-ok">op · arg1 · arg2 · result</span></div>',
                    unsafe_allow_html=True
                )
                rows = ""
                for i, (op, a1, a2, res) in enumerate(quads):
                    rows += (f'<tr><td class="idx">{i}</td>'
                             f'<td class="cop">{esc(op)}</td>'
                             f'<td class="carg">{esc(a1)}</td>'
                             f'<td class="carg">{esc(a2)}</td>'
                             f'<td class="cres">{esc(res)}</td></tr>')
                st.markdown(
                    f'<div class="tbl-wrap"><table class="data-tbl">'
                    f'<thead><tr><th>#</th><th>op</th><th>arg1</th><th>arg2</th><th>result</th></tr></thead>'
                    f'<tbody>{rows}</tbody></table></div>',
                    unsafe_allow_html=True
                )
                lines = [f"({op}, {a1}, {a2}, {res})" for op, a1, a2, res in quads]
                st.markdown('<div class="sec-label plain-text-label">Plain text</div>', unsafe_allow_html=True)
                st.text_area("Plain text", "\n".join(lines), height=110, key="q_plain", label_visibility="collapsed")

            elif tac_mode == "Triple":
                triples = as_triples(recs)
                st.markdown(
                    '<div class="sec-label">Triples'
                    '<span class="badge badge-ok">index · op · arg1 · arg2</span></div>',
                    unsafe_allow_html=True
                )
                rows = ""
                for idx, op, a1, a2 in triples:
                    rows += (f'<tr><td class="idx">({idx})</td>'
                             f'<td class="cop">{esc(op)}</td>'
                             f'<td class="carg">{esc(a1)}</td>'
                             f'<td class="carg">{esc(a2)}</td></tr>')
                st.markdown(
                    f'<div class="tbl-wrap"><table class="data-tbl">'
                    f'<thead><tr><th>Index</th><th>op</th><th>arg1</th><th>arg2</th></tr></thead>'
                    f'<tbody>{rows}</tbody></table></div>',
                    unsafe_allow_html=True
                )
                lines = [f"({idx}): ({op}, {a1}, {a2})" for idx, op, a1, a2 in triples]
                st.markdown('<div class="sec-label plain-text-label">Plain text</div>', unsafe_allow_html=True)
                st.text_area("Plain text", "\n".join(lines), height=110, key="t_plain", label_visibility="collapsed")

            elif tac_mode == "Indirect Triple":
                triples, ptr_tbl = as_indirect_triples(recs)
                st.markdown(
                    '<div class="sec-label">Indirect Triples'
                    '<span class="badge badge-ok">pointer table + triples</span></div>',
                    unsafe_allow_html=True
                )
                c1, c2 = st.columns([3, 2])
                with c1:
                    st.markdown('<div class="sec-label">Triples Table</div>', unsafe_allow_html=True)
                    rows = ""
                    for idx, op, a1, a2 in triples:
                        rows += (f'<tr><td class="idx">({idx})</td>'
                                 f'<td class="cop">{esc(op)}</td>'
                                 f'<td class="carg">{esc(a1)}</td>'
                                 f'<td class="carg">{esc(a2)}</td></tr>')
                    st.markdown(
                        f'<div class="tbl-wrap"><table class="data-tbl">'
                        f'<thead><tr><th>Index</th><th>op</th><th>arg1</th><th>arg2</th></tr></thead>'
                        f'<tbody>{rows}</tbody></table></div>',
                        unsafe_allow_html=True
                    )
                with c2:
                    st.markdown('<div class="sec-label">Pointer Table</div>', unsafe_allow_html=True)
                    rows = ""
                    for p_idx, t_idx in ptr_tbl:
                        rows += (f'<tr><td class="idx">ptr[{p_idx}]</td>'
                                 f'<td class="cptr">→ ({t_idx})</td></tr>')
                    st.markdown(
                        f'<div class="tbl-wrap"><table class="data-tbl">'
                        f'<thead><tr><th>Pointer</th><th>Points to</th></tr></thead>'
                        f'<tbody>{rows}</tbody></table></div>',
                        unsafe_allow_html=True
                    )

        # ── All Formats side-by-side comparison ───────────────────────────
        with tabs[1]:
            st.markdown(
                '<div class="info-box">'
                '<strong>Format comparison:</strong> All three forms represent the same computation.<br>'
                'Quadruples are most explicit. Triples save space but use index refs. '
                'Indirect Triples let optimizers reorder code by editing just the pointer table.'
                '</div>',
                unsafe_allow_html=True
            )

            ca, cb, cc = st.columns(3)
            quads   = as_quadruples(recs)
            triples = as_triples(recs)
            _, ptrs = as_indirect_triples(recs)

            with ca:
                st.markdown('<div class="sec-label">Quadruples</div>', unsafe_allow_html=True)
                lines = [f"({op},{a1},{a2},{r})" for op, a1, a2, r in quads]
                st.code("\n".join(lines), language="text")

            with cb:
                st.markdown('<div class="sec-label">Triples</div>', unsafe_allow_html=True)
                lines = [f"({i}):({op},{a1},{a2})" for i, op, a1, a2 in triples]
                st.code("\n".join(lines), language="text")

            with cc:
                st.markdown('<div class="sec-label">Pointer Table</div>', unsafe_allow_html=True)
                lines = [f"ptr[{p}]→({t})" for p, t in ptrs]
                st.code("\n".join(lines), language="text")

        # ── Step-by-step ──────────────────────────────────────────────────
        if show_steps_tac and len(tabs) > 2:
            with tabs[2]:
                num = 0
                for s in gen.steps:
                    if s["op"] == "SEP":
                        st.markdown(f'<div class="step-sep">{esc(s["note"])}</div>', unsafe_allow_html=True)
                        continue
                    is_cse = s.get("cse", False)
                    if is_cse and not show_cse_steps:
                        continue
                    num += 1
                    op, a1, a2, res = s["op"], s["arg1"], s["arg2"], s["result"]
                    if op == "=":         instr = f"{res} = {a1}"
                    elif op == "uminus":  instr = f"{res} = -{a1}"
                    elif op == "CSE":     instr = f"; reuse {res}  ({a1})"
                    else:                 instr = f"{res} = {a1} {op} {a2}"

                    badge = ' <span class="badge badge-cse">CSE</span>' if is_cse else ""
                    lbl   = "≡" if is_cse else str(num)
                    cls   = "step-card cse" if is_cse else "step-card"

                    st.markdown(f"""
                    <div class="{cls}">
                      <div class="step-num">{lbl}</div>
                      <div>
                        <div class="step-instr">{esc(instr)}{badge}</div>
                        <div class="step-note">{esc(s['note'])}</div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)


# ── footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="margin-top:3rem; border-top:1px solid #252d40; padding-top:0.85rem;
     color:#5a6a82; font-size:0.72rem; text-align:center; font-family:'IBM Plex Mono',monospace;">
  Intermediate Code Generator Studio &nbsp;·&nbsp; Compiler Design &nbsp;·&nbsp; Python + Streamlit
</div>
""", unsafe_allow_html=True)
