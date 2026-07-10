"""Enterprise UI layer: theming, accessibility, and reusable components.

Accessibility: WCAG AA+ palettes, high-contrast mode, text scaling,
reduce-motion, visible focus outlines, aria labels on visuals, and
modular voice widgets (browser speech synthesis / recognition).
"""

import html
import json

import streamlit as st
import streamlit.components.v1 as components

import config
from strings import L, tr
from visuals import get_visual

# ---------------------------------------------------------------------------
# Theme tokens (all text/background pairs meet WCAG AA at minimum)
# ---------------------------------------------------------------------------
THEMES = {
    "light": {
        "bg": "#f4f6fa", "surface": "#ffffff", "surface2": "#f8fafd",
        "border": "#d5dce8", "text": "#16202e", "muted": "#4c5c74",
        "accent": "#1a46c2", "accent-soft": "#e8effd", "accent-text": "#1a46c2",
        "ok": "#0b6157", "ok-soft": "#e6f5f3",
        "warn": "#8a4207", "warn-soft": "#fdf1e3",
        "danger": "#a11616", "danger-soft": "#fdeaea",
        "shadow": "0 1px 3px rgba(16,24,40,.06), 0 1px 2px rgba(16,24,40,.04)",
    },
    "dark": {
        "bg": "#0e1420", "surface": "#161e2e", "surface2": "#1c2638",
        "border": "#324260", "text": "#e9edf5", "muted": "#a3b2c8",
        "accent": "#6d9af5", "accent-soft": "#1d2c4a", "accent-text": "#a5c2fa",
        "ok": "#45d6a4", "ok-soft": "#12302a",
        "warn": "#fcc43c", "warn-soft": "#33290f",
        "danger": "#f98888", "danger-soft": "#3a1a1a",
        "shadow": "0 1px 3px rgba(0,0,0,.4)",
    },
    # High-contrast variants (approach WCAG AAA)
    "light_hc": {
        "bg": "#ffffff", "surface": "#ffffff", "surface2": "#f2f2f2",
        "border": "#000000", "text": "#000000", "muted": "#1f1f1f",
        "accent": "#0000c8", "accent-soft": "#dfe6ff", "accent-text": "#0000c8",
        "ok": "#004d40", "ok-soft": "#d9f2ee",
        "warn": "#6b3300", "warn-soft": "#ffe9cf",
        "danger": "#8a0000", "danger-soft": "#ffdddd",
        "shadow": "none",
    },
    "dark_hc": {
        "bg": "#000000", "surface": "#000000", "surface2": "#111111",
        "border": "#ffffff", "text": "#ffffff", "muted": "#e6e6e6",
        "accent": "#ffd93b", "accent-soft": "#333000", "accent-text": "#ffd93b",
        "ok": "#6bffdb", "ok-soft": "#00332a",
        "warn": "#ffc46b", "warn-soft": "#332200",
        "danger": "#ff9c9c", "danger-soft": "#330000",
        "shadow": "none",
    },
}

TEXT_SCALES = {"normal": 1.0, "large": 1.15, "xlarge": 1.3}


def theme_key(base: str, high_contrast: bool) -> str:
    return f"{base}_hc" if high_contrast else base


def inject_css(theme: str = "light", text_scale: str = "normal", reduce_motion: bool = False):
    t = THEMES.get(theme, THEMES["light"])
    vars_css = "\n".join(f"--{k}: {v};" for k, v in t.items())
    zoom = TEXT_SCALES.get(text_scale, 1.0)
    motion_css = """
*, *::before, *::after { animation: none !important; transition: none !important; }
""" if reduce_motion else ""
    zoom_css = (f'[data-testid="stAppViewContainer"] {{ zoom: {zoom}; }}\n'
                f'[data-testid="stBottomBlockContainer"] {{ zoom: {zoom}; }}') if zoom != 1.0 else ""
    st.markdown(f"""
<style>
:root {{ {vars_css} }}
{zoom_css}
[data-testid="stAppViewContainer"] {{ background: var(--bg); }}
[data-testid="stHeader"] {{ background: var(--bg); }}
[data-testid="stSidebar"] {{ background: var(--surface); border-right: 1px solid var(--border); }}
[data-testid="stSidebar"] * {{ color: var(--text); }}
html, body, [data-testid="stAppViewContainer"] p, [data-testid="stAppViewContainer"] span,
[data-testid="stAppViewContainer"] div, [data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] input, [data-testid="stAppViewContainer"] textarea,
[data-testid="stAppViewContainer"] button, [data-testid="stAppViewContainer"] li,
[data-testid="stAppViewContainer"] h1, [data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3, [data-testid="stAppViewContainer"] h4,
[data-testid="stAppViewContainer"] h5 {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, sans-serif;
    color: var(--text);
}}
/* Restore Streamlit's icon font. A global font override breaks Material
   Symbols and makes icon names render as overlapping text. */
[data-testid="stIconMaterial"], [data-testid="stExpanderToggleIcon"],
span[class*="material-symbols"], .material-symbols-rounded, .material-icons {{
    font-family: "Material Symbols Rounded" !important;
}}
[data-testid="stBottomBlockContainer"] {{ background: var(--bg); }}

/* Keyboard navigation: always-visible focus */
button:focus-visible, a:focus-visible, input:focus-visible, textarea:focus-visible,
[role="button"]:focus-visible {{
    outline: 3px solid var(--accent) !important; outline-offset: 2px !important;
}}

/* ---- Chat ---- */
[data-testid="stChatMessage"] {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
    padding: 14px 18px; box-shadow: var(--shadow); margin-bottom: 4px;
}}
[data-testid="stChatInput"] textarea {{
    background: var(--surface) !important; color: var(--text) !important;
    border-radius: 12px !important;
}}
[data-testid="stChatInput"] {{
    background: var(--surface) !important; border: 1.5px solid var(--border) !important;
    border-radius: 12px !important;
}}
/* Chat input inner wrappers + bottom bar (otherwise they keep the base-theme dark bg) */
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] [data-baseweb="base-input"] {{
    background: var(--surface) !important; border-color: var(--border) !important;
}}
[data-testid="stChatInput"] textarea::placeholder {{
    color: var(--muted) !important; opacity: 1 !important;
}}
[data-testid="stChatInput"] button {{ background: transparent !important; }}
[data-testid="stChatInput"] button svg {{ fill: var(--muted) !important; }}
[data-testid="stBottom"], [data-testid="stBottom"] > div {{
    background: var(--bg) !important;
}}

/* ---- Form widgets: force legible colors regardless of Streamlit base theme ---- */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input {{
    background: var(--surface) !important; color: var(--text) !important;
    border: 1.5px solid var(--border) !important; border-radius: 10px !important;
}}
[data-testid="stTextInput"] input::placeholder, [data-testid="stTextArea"] textarea::placeholder {{
    color: var(--muted) !important; opacity: 1 !important;
}}
[data-baseweb="select"] > div {{
    background: var(--surface) !important; color: var(--text) !important;
    border-color: var(--border) !important; border-radius: 10px !important;
}}
[data-baseweb="select"] * {{ color: var(--text) !important; }}
[data-baseweb="select"] svg {{ fill: var(--muted) !important; }}
[data-baseweb="popover"] [role="listbox"], [data-baseweb="menu"] {{
    background: var(--surface) !important; border: 1px solid var(--border) !important;
}}
[data-baseweb="popover"] [role="option"], [data-baseweb="menu"] li {{
    background: var(--surface) !important; color: var(--text) !important;
}}
[data-baseweb="popover"] [role="option"][aria-selected="true"],
[data-baseweb="popover"] [role="option"]:hover {{
    background: var(--accent-soft) !important; color: var(--accent-text) !important;
}}

/* ---- Expanders: legible header + body on any base theme ---- */
[data-testid="stExpander"] details {{
    background: var(--surface) !important; border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}}
[data-testid="stExpander"] summary {{
    background: var(--surface) !important; color: var(--text) !important;
    border-radius: 12px !important;
}}
[data-testid="stExpander"] summary:hover {{ color: var(--accent-text) !important; }}
[data-testid="stExpander"] summary span, [data-testid="stExpander"] summary p {{
    color: var(--text) !important;
}}

/* ---- Buttons: large, clear targets ---- */
.stButton > button, .stDownloadButton > button {{
    border-radius: 10px; border: 1.5px solid var(--border); background: var(--surface);
    color: var(--text); font-weight: 550; box-shadow: var(--shadow);
    min-height: 44px; transition: all .15s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
    border-color: var(--accent); color: var(--accent-text);
}}
.stButton > button[kind="primary"] {{
    background: var(--accent); border-color: var(--accent); color: #ffffff;
}}
.stButton > button[kind="primary"]:hover {{ filter: brightness(1.08); color: #fff; }}

/* ---- App header ---- */
.app-header {{
    display: flex; align-items: center; gap: 14px; padding: 16px 20px;
    background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
    box-shadow: var(--shadow); margin-bottom: 16px;
}}
.app-header .logo {{
    width: 44px; height: 44px; border-radius: 12px; background: var(--accent); color: #fff;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 17px; flex-shrink: 0;
}}
.app-header h1 {{ font-size: 19px; margin: 0; font-weight: 650; }}
.app-header p {{ margin: 2px 0 0; font-size: 13px; color: var(--muted); }}

/* ---- Badges ---- */
.badge {{
    display: inline-flex; align-items: center; gap: 6px; padding: 3px 11px;
    border-radius: 999px; font-size: 12px; font-weight: 650;
}}
.badge .dot {{ width: 7px; height: 7px; border-radius: 50%; }}
.badge-accent {{ background: var(--accent-soft); color: var(--accent-text); }}
.badge-accent .dot {{ background: var(--accent); }}
.badge-ok {{ background: var(--ok-soft); color: var(--ok); }}
.badge-ok .dot {{ background: var(--ok); }}
.badge-warn {{ background: var(--warn-soft); color: var(--warn); }}
.badge-warn .dot {{ background: var(--warn); }}
.badge-danger {{ background: var(--danger-soft); color: var(--danger); }}
.badge-danger .dot {{ background: var(--danger); }}

/* ---- Panels ---- */
.panel {{
    background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
    padding: 14px 16px; box-shadow: var(--shadow); margin-bottom: 12px;
}}
.panel h4 {{
    margin: 0 0 10px; font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: .8px; color: var(--muted);
}}
.panel.notice {{ border-left: 4px solid var(--warn); }}
.metric-row {{ display: flex; justify-content: space-between; align-items: center;
    padding: 5px 0; font-size: 13px; gap: 8px; }}
.metric-row .label {{ color: var(--muted); }}
.metric-row .value {{ font-weight: 600; text-align: right; }}

/* ---- Progress ---- */
.progress-track {{ display: flex; gap: 4px; margin: 8px 0 6px; }}
.progress-seg {{ flex: 1; height: 8px; border-radius: 4px; background: var(--border);
    transition: background .3s ease; }}
.progress-seg.filled {{ background: var(--accent); }}
.progress-caption {{ font-size: 12px; color: var(--muted); }}

/* ---- Step card ---- */
.step-card {{
    background: var(--surface); border: 1.5px solid var(--border);
    border-left: 5px solid var(--accent); border-radius: 14px; padding: 16px 18px;
    box-shadow: var(--shadow); margin: 6px 0 8px; animation: rise .35s ease;
}}
.step-card .step-head {{ display: flex; align-items: center; justify-content: space-between;
    gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }}
.step-card .step-title {{ font-size: 15px; font-weight: 650; }}
.step-card .row {{ display: flex; gap: 10px; margin: 8px 0; font-size: 14px; line-height: 1.55; }}
.step-card .row .icon {{
    flex-shrink: 0; width: 26px; height: 26px; border-radius: 8px;
    background: var(--accent-soft); color: var(--accent-text);
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 700;
}}
.step-card .row .k {{ font-weight: 650; margin-right: 4px; }}

/* ---- Timeline ---- */
.timeline {{ position: relative; padding-left: 18px; max-height: 300px; overflow-y: auto; }}
.timeline::before {{ content: ""; position: absolute; left: 5px; top: 4px; bottom: 4px;
    width: 2px; background: var(--border); }}
.tl-item {{ position: relative; padding: 4px 0 10px; font-size: 12.5px; line-height: 1.45; }}
.tl-item::before {{ content: ""; position: absolute; left: -18px; top: 8px;
    width: 8px; height: 8px; border-radius: 50%; background: var(--accent);
    border: 2px solid var(--surface); }}
.tl-item.kind-step_result::before {{ background: var(--ok); }}
.tl-item.kind-escalation_reason::before {{ background: var(--danger); }}
.tl-item .kind {{ display:block; font-size: 10px; font-weight: 700; letter-spacing: .6px;
    text-transform: uppercase; color: var(--muted); }}

/* ---- Thinking (gentle, no flashing) ---- */
.thinking {{ display: inline-flex; align-items: center; gap: 10px; padding: 10px 16px;
    border-radius: 12px; background: var(--surface); border: 1px solid var(--border);
    color: var(--muted); font-size: 13.5px; }}
.thinking .dots span {{ display: inline-block; width: 6px; height: 6px; margin-right: 4px;
    border-radius: 50%; background: var(--accent); animation: pulse 1.6s infinite ease-in-out; }}
.thinking .dots span:nth-child(2) {{ animation-delay: .22s; }}
.thinking .dots span:nth-child(3) {{ animation-delay: .44s; }}
@keyframes pulse {{ 0%,80%,100% {{ opacity:.35; }} 40% {{ opacity:1; }} }}
@keyframes rise {{ from {{ opacity:0; transform: translateY(6px);}} to {{opacity:1; transform:none;}} }}

/* ---- Ticket ---- */
.ticket {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
    box-shadow: var(--shadow); overflow: hidden; margin: 8px 0 14px; animation: rise .35s ease; }}
.ticket .ticket-head {{ padding: 16px 20px; background: var(--surface2);
    border-bottom: 1px solid var(--border); display: flex; justify-content: space-between;
    align-items: flex-start; gap: 12px; flex-wrap: wrap; }}
.ticket .ticket-head h3 {{ margin: 0 0 4px; font-size: 17px; font-weight: 650; }}
.ticket .ticket-head .ref {{ font-size: 12px; color: var(--muted); }}
.ticket .ticket-body {{ padding: 6px 20px 16px; }}
.ticket .sec {{ padding: 11px 0; border-bottom: 1px solid var(--border); }}
.ticket .sec:last-child {{ border-bottom: none; }}
.ticket .sec h5 {{ margin: 0 0 6px; font-size: 10.5px; font-weight: 700;
    text-transform: uppercase; letter-spacing: .8px; color: var(--muted); }}
.ticket .sec p, .ticket .sec li {{ margin: 0; font-size: 13.5px; line-height: 1.55; }}
.ticket .sec ul, .ticket .sec ol {{ margin: 2px 0 0; padding-left: 20px; }}
.ticket .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; }}
.ticket .kv .k {{ font-size: 10.5px; font-weight: 700; text-transform: uppercase;
    letter-spacing: .8px; color: var(--muted); display:block; margin-bottom: 3px; }}
.ticket .kv .v {{ font-size: 13.5px; font-weight: 550; }}

.quick-label {{ font-size: 12px; color: var(--muted); margin: 2px 0 6px; }}
.visual-caption {{ font-size: 12.5px; color: var(--muted); margin-top: 6px; }}
hr {{ border-color: var(--border); }}

/* ---- Welcome hero (landing) ---- */
.hero {{
    background:
      radial-gradient(1200px 240px at 15% -40%, var(--accent-soft), transparent 60%),
      var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 26px 28px 22px;
    box-shadow: var(--shadow);
    margin-bottom: 16px;
    animation: rise .4s ease;
}}
.hero .eyebrow {{
    display: inline-flex; align-items: center; gap: 7px;
    font-size: 11.5px; font-weight: 700; letter-spacing: .7px; text-transform: uppercase;
    color: var(--accent-text); background: var(--accent-soft);
    padding: 4px 11px; border-radius: 999px; margin-bottom: 14px;
}}
.hero h2 {{
    font-size: 25px; line-height: 1.25; margin: 0 0 10px; font-weight: 720;
    letter-spacing: -.3px; max-width: 30ch;
}}
.hero p {{ font-size: 14.5px; line-height: 1.6; color: var(--muted); margin: 0; max-width: 62ch; }}
.hero .chips {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }}
.hero .chip {{
    display: inline-flex; align-items: center; gap: 7px;
    font-size: 12.5px; font-weight: 550; color: var(--text);
    background: var(--surface2); border: 1px solid var(--border);
    padding: 6px 12px; border-radius: 999px;
}}
.hero .chip .ic {{ font-size: 13px; }}

@media (max-width: 640px) {{
    .hero {{ padding: 20px 18px; }}
    .hero h2 {{ font-size: 21px; }}
    .app-header {{ padding: 14px 16px; }}
    .app-header h1 {{ font-size: 17px; }}
    [data-testid="stChatMessage"] {{ padding: 12px 14px; }}
    .step-card {{ padding: 14px 15px; }}
    .ticket .ticket-head, .ticket .ticket-body {{ padding-left: 15px; padding-right: 15px; }}
}}
{motion_css}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------
def esc(s) -> str:
    return html.escape(str(s or ""))


def header(lang: str = "en"):
    badge_html = ""
    if getattr(config, "APP_BADGE", ""):
        badge_html = f'<span class="badge badge-accent" style="margin-left:8px;vertical-align:middle;">{esc(config.APP_BADGE)}</span>'
    st.markdown(f"""
<div class="app-header" role="banner">
  <div class="logo" aria-hidden="true">{esc(config.ORG_SHORT)}</div>
  <div>
    <h1 style="display:inline-block;">{esc(config.APP_NAME)}</h1>{badge_html}
    <p>{esc(config.ORG_NAME)} · {esc(L('tagline', lang))}</p>
  </div>
</div>
""", unsafe_allow_html=True)


def welcome_hero(lang: str = "en"):
    chips = [
        ("🧭", L("chip_guided", lang)),
        ("💬", L("chip_noforms", lang)),
        ("🎫", L("chip_ticket", lang)),
        ("🌐", L("chip_bilingual", lang)),
    ]
    chip_html = "".join(
        f'<span class="chip"><span class="ic">{ic}</span>{esc(txt)}</span>' for ic, txt in chips
    )
    eyebrow = "Welcome" if lang == "en" else "Bienvenido"
    st.markdown(f"""
<div class="hero">
  <span class="eyebrow">👋 {esc(eyebrow)}</span>
  <h2>{esc(L('welcome_title', lang))}</h2>
  <p>{esc(L('welcome_sub', lang))}</p>
  <div class="chips">{chip_html}</div>
</div>
""", unsafe_allow_html=True)


def badge(text: str, kind: str = "accent") -> str:
    return f'<span class="badge badge-{kind}"><span class="dot"></span>{esc(text)}</span>'


def phase_badge(phase: str, lang: str = "en") -> str:
    kinds = {"resolved": "ok", "escalation_offer": "warn"}
    label = config.PHASES.get(phase, ("In progress", "En progreso"))
    return badge(label[0 if lang == "en" else 1], kinds.get(phase, "accent"))


def prototype_notice(lang: str = "en"):
    st.markdown(f"""
<div class="panel notice" role="note" aria-label="prototype notice">
  <h4>🧪 {esc(L('prototype_title', lang))}</h4>
  <div style="font-size:13px; line-height:1.6;">{esc(L('prototype_notice', lang))}</div>
</div>
""", unsafe_allow_html=True)


def privacy_notice(lang: str = "en"):
    st.markdown(f"""
<div class="panel notice" role="note" aria-label="privacy notice">
  <h4>{esc(L('privacy_title', lang))}</h4>
  <div style="font-size:13.5px; line-height:1.6;">⚠️ {esc(L('privacy_notice', lang))}</div>
</div>
""", unsafe_allow_html=True)


def sensitive_warning(lang: str = "en"):
    st.markdown(f"""
<div class="panel notice" role="alert">
  <div style="font-size:13.5px; line-height:1.6;">🔒 {esc(L('sensitive_warning', lang))}</div>
</div>
""", unsafe_allow_html=True)


def progress_bar(current: int, total: int, lang: str = "en"):
    total = max(total, current, 1)
    segs = "".join(
        f'<div class="progress-seg{" filled" if i < current else ""}"></div>'
        for i in range(total)
    )
    st.markdown(f"""
<div class="progress-track" role="progressbar" aria-valuenow="{current}" aria-valuemin="1"
     aria-valuemax="{total}" aria-label="{esc(L('step_of', lang, a=current, b=total))}">{segs}</div>
<div class="progress-caption">{esc(L('step_of', lang, a=current, b=total))}</div>
""", unsafe_allow_html=True)


def session_panel(turn, lang: str = "en"):
    conf = int(turn.confidence)
    conf_kind = "ok" if conf >= 70 else ("warn" if conf >= 40 else "danger")
    st.markdown(f"""
<div class="panel">
  <h4>{esc(L('session_status', lang))}</h4>
  <div style="margin-bottom:8px;">{phase_badge(turn.phase, lang)}</div>
  <div class="metric-row"><span class="label">{esc(L('current_activity', lang))}</span>
      <span class="value">{esc(turn.status_label)}</span></div>
  <div class="metric-row"><span class="label">{esc(L('time_remaining', lang))}</span>
      <span class="value">{int(turn.est_minutes_remaining)} min</span></div>
  <div class="metric-row"><span class="label">{esc(L('confidence', lang))}</span>
      <span class="value">{badge(f"{conf}%", conf_kind)}</span></div>
</div>
""", unsafe_allow_html=True)
    if turn.issue_summary:
        st.markdown(f"""
<div class="panel">
  <h4>{esc(L('issue_summary', lang))}</h4>
  <div style="font-size:13px; line-height:1.5;">{esc(turn.issue_summary)}</div>
</div>
""", unsafe_allow_html=True)


KIND_LABELS = {
    "info_collected": "Info", "finding": "Finding", "step_attempted": "Step",
    "step_result": "Result", "escalation_reason": "Escalation",
}


def timeline_panel(log: list[dict], lang: str = "en"):
    if not log:
        return
    items = "".join(
        f'<div class="tl-item kind-{esc(e["kind"])}">'
        f'<span class="kind">{esc(KIND_LABELS.get(e["kind"], e["kind"]))}</span>'
        f'{esc(e["detail"])}</div>'
        for e in log[-30:]
    )
    st.markdown(f"""
<div class="panel">
  <h4>{esc(L('timeline', lang))}</h4>
  <div class="timeline">{items}</div>
</div>
""", unsafe_allow_html=True)


def step_card(step: dict, lang: str = "en"):
    diff = step.get("difficulty", "Easy")
    diff_label = {"Easy": {"en": "Easy", "es": "Fácil"}, "Moderate": {"en": "Moderate", "es": "Moderado"},
                  "Advanced": {"en": "Advanced", "es": "Avanzado"}}.get(diff, {"en": diff, "es": diff})[lang]
    diff_kind = {"Easy": "ok", "Moderate": "warn", "Advanced": "danger"}.get(diff, "ok")
    st.markdown(f"""
<div class="step-card" role="group" aria-label="{esc(step.get("title"))}">
  <div class="step-head">
    <span class="step-title">{esc(step.get("title"))}</span>
    {badge(diff_label, diff_kind)}
  </div>
  <div class="row"><span class="icon" aria-hidden="true">1</span>
    <span class="body"><span class="k">{esc(L('what_to_do', lang))}:</span>{esc(step.get("what"))}</span></div>
  <div class="row"><span class="icon" aria-hidden="true">?</span>
    <span class="body"><span class="k">{esc(L('why_matters', lang))}:</span>{esc(step.get("why"))}</span></div>
  <div class="row"><span class="icon" aria-hidden="true">✓</span>
    <span class="body"><span class="k">{esc(L('expected_result', lang))}:</span>{esc(step.get("expected"))}</span></div>
</div>
""", unsafe_allow_html=True)
    # Optional visual guidance. Kept out of the card so chat stays clean
    visual_id = step.get("visual")
    if visual_id:
        v = get_visual(visual_id)
        if v:
            with st.expander(f"🖼️ {L('show_me_how', lang)}, {tr(v['caption'], lang)}"):
                st.markdown(v["svg"], unsafe_allow_html=True)
                st.markdown(f'<div class="visual-caption">{esc(tr(v["alt"], lang))}</div>',
                            unsafe_allow_html=True)
                st.caption(f"▶️ {L('play_video', lang)}: {L('video_placeholder', lang)}")


def thinking(placeholder, lang: str = "en"):
    placeholder.markdown(f"""
<div class="thinking" role="status" aria-live="polite">
  <span class="dots" aria-hidden="true"><span></span><span></span><span></span></span>
  {esc(L('thinking', lang))}…
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Voice (modular; browser-based, degrades gracefully)
# ---------------------------------------------------------------------------
def _speakable(text: str) -> str:
    """Strip markdown/emoji artifacts so speech is clean and complete."""
    import re
    t = re.sub(r"[*_`#>]|\[|\]\([^)]*\)", " ", str(text))
    t = re.sub(r"[🛠️🎫📋✏️↺🔊🎤⭐🖼️▶️♿🔒⚠️🎉]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def tts_button(text: str, lang: str = "en", key: str = ""):
    """Speaker button. Reads the FULL text aloud reliably.

    Browsers silently stop long utterances (~15s in Chromium), so the text is
    split into sentence chunks queued one after another, with a pause/resume
    keep-alive to defeat the auto-stop. A second click stops playback.
    """
    payload = json.dumps(_speakable(text))
    voice = "es-ES" if lang == "es" else "en-US"
    stop_label = "⏹" if lang == "en" else "⏹"
    components.html(f"""
<button id="tts" aria-label="{esc(L('listen', lang))}" title="{esc(L('listen', lang))}"
  style="border:1.5px solid #94a3b8;background:transparent;border-radius:8px;
         padding:4px 12px;cursor:pointer;font-size:13px;color:#64748b;">
  🔊 {esc(L('listen', lang))}</button>
<script>
  const FULL = {payload};
  const btn = document.getElementById('tts');
  const synth = window.speechSynthesis;
  let keepAlive = null, playing = false;

  function stop() {{
    playing = false;
    if (keepAlive) clearInterval(keepAlive);
    synth.cancel();
    btn.innerHTML = '🔊 {esc(L('listen', lang))}';
  }}

  btn.onclick = () => {{
    if (playing) {{ stop(); return; }}
    stop();
    playing = true;
    btn.innerHTML = '{stop_label} …';
    // Split into sentence-sized chunks; long chunks split on commas.
    let chunks = FULL.match(/[^.!?]+[.!?]+|\\S[^.!?]*$/g) || [FULL];
    chunks = chunks.flatMap(c => c.length > 200 ? c.split(/,(?=\\s)/) : [c])
                   .map(c => c.trim()).filter(Boolean);
    chunks.forEach((c, i) => {{
      const u = new SpeechSynthesisUtterance(c);
      u.lang = "{voice}"; u.rate = 0.95;
      if (i === chunks.length - 1) u.onend = stop;
      synth.speak(u);
    }});
    // Keep-alive: Chromium stops speaking after ~15s without this.
    keepAlive = setInterval(() => {{
      if (!synth.speaking) {{ stop(); return; }}
      synth.pause(); synth.resume();
    }}, 10000);
  }};
</script>
""", height=44)


def mic_widget(lang: str = "en"):
    """Speech-to-text (browser SpeechRecognition). Shows the transcript for the
    user to copy into the chat box. Modular placeholder until a native
    Streamlit injection path exists."""
    voice = "es-ES" if lang == "es" else "en-US"
    components.html(f"""
<div style="font-family:sans-serif;display:flex;gap:8px;align-items:center;">
  <button id="mic" aria-label="microphone"
    style="border:1.5px solid #94a3b8;background:transparent;border-radius:8px;
           padding:6px 14px;cursor:pointer;font-size:14px;color:#64748b;">🎤</button>
  <input id="out" readonly aria-label="voice transcript" placeholder="{esc(L('mic_hint', lang))}"
    style="flex:1;border:1.5px solid #94a3b8;border-radius:8px;padding:6px 10px;
           font-size:13px;color:#334155;background:transparent;"
    onclick="this.select()">
</div>
<script>
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const btn = document.getElementById('mic'), out = document.getElementById('out');
  if (!SR) {{
    out.placeholder = {json.dumps(L('mic_unsupported', lang))};
    btn.disabled = true;
  }} else {{
    const rec = new SR(); rec.lang = "{voice}"; rec.interimResults = false;
    let listening = false;
    btn.onclick = () => {{
      if (listening) {{ rec.stop(); return; }}
      listening = true; btn.textContent = '⏺'; rec.start();
    }};
    rec.onresult = (e) => {{ out.value = e.results[0][0].transcript; out.select();
                             document.execCommand && document.execCommand('copy'); }};
    rec.onend = () => {{ listening = false; btn.textContent = '🎤'; }};
    rec.onerror = () => {{ listening = false; btn.textContent = '🎤'; }};
  }}
</script>
""", height=56)


# ---------------------------------------------------------------------------
# Ticket preview
# ---------------------------------------------------------------------------
def summary_preview(t: dict, lang: str = "en"):
    """End-user support summary. Plain, calm, no internal routing/priority/risk."""
    tried = t.get("troubleshooting_performed", [])
    if tried:
        steps = "".join(
            f"<li><strong>{esc(s['step'])}</strong>, "
            f"<span style='color:var(--muted)'>{esc(s['result'])}</span></li>"
            for s in tried
        )
        tried_html = f"<ul>{steps}</ul>"
    else:
        none_txt = "No steps were completed before this summary." if lang == "en" \
            else "No se completaron pasos antes de este resumen."
        tried_html = f"<p style='color:var(--muted)'>{esc(none_txt)}</p>"

    st.markdown(f"""
<div class="ticket" role="article" aria-label="support summary">
  <div class="ticket-head">
    <div>
      <h3>{esc(t.get("title"))}</h3>
      <span class="ref">{esc(t.get("created_at"))}</span>
    </div>
  </div>
  <div class="ticket-body">
    <div class="sec grid">
      <div class="kv"><span class="k">{esc(L('sum_requester', lang))}</span>
        <span class="v">{esc(t.get("user_name"))} ({esc(t.get("user_role"))})</span></div>
      <div class="kv"><span class="k">Email</span><span class="v">{esc(t.get("user_email"))}</span></div>
      <div class="kv"><span class="k">{esc(L('field_campus', lang))}</span>
        <span class="v">{esc(t.get("user_location"))}</span></div>
    </div>
    <div class="sec"><h5>{esc(L('sum_issue', lang))}</h5><p>{esc(t.get("executive_summary"))}</p></div>
    <div class="sec"><h5>{esc(L('sum_tried', lang))}</h5>{tried_html}</div>
  </div>
</div>
""", unsafe_allow_html=True)


def staff_ops_view(t: dict, log: list, entry_id: str | None, lang: str = "en"):
    """Technician-only triage detail, shown inside an expander in IT Staff Operations."""
    kb_line = f"<div class='kv'><span class='k'>Matched KB entry</span><span class='v'>{esc(entry_id or 'none')}</span></div>"
    conf = int(t.get("confidence_score", 0))
    st.markdown(f"""
<div class="panel">
  <h4>Routing &amp; triage</h4>
  <div class="ticket grid" style="border:none;box-shadow:none;">
    <div class="kv"><span class="k">Assignment group</span><span class="v">{esc(t.get("assignment_group"))}</span></div>
    <div class="kv"><span class="k">Category</span><span class="v">{esc(t.get("category"))} › {esc(t.get("subcategory"))}</span></div>
    <div class="kv"><span class="k">Priority</span><span class="v">{esc(t.get("priority"))}</span></div>
    <div class="kv"><span class="k">Risk</span><span class="v">{esc(t.get("risk_level"))}</span></div>
    <div class="kv"><span class="k">Confidence</span><span class="v">{conf}%</span></div>
    <div class="kv"><span class="k">Est. effort</span><span class="v">{esc(t.get("estimated_technician_effort"))}</span></div>
    {kb_line}
  </div>
</div>
<div class="panel"><h4>Why this assignment group</h4>
  <div style="font-size:13px;line-height:1.55;">{esc(t.get("assignment_rationale"))}</div></div>
<div class="panel"><h4>Why this priority</h4>
  <div style="font-size:13px;line-height:1.55;">{esc(t.get("priority_rationale"))}</div></div>
<div class="panel"><h4>Suggested resolution path</h4>
  <div style="font-size:13px;line-height:1.55;">{esc(t.get("suggested_resolution_path"))}</div></div>
""", unsafe_allow_html=True)
    timeline_panel(log, lang)


def ticket_preview(t: dict, lang: str = "en"):
    def ul(items):
        if not items:
            return "<p>Not provided</p>"
        return "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>"

    steps = "".join(
        f"<li><strong>{esc(s['step'])}</strong><br>"
        f"<span style='color:var(--muted)'>Result: {esc(s['result'])}</span></li>"
        for s in t.get("troubleshooting_performed", [])
    )
    steps_html = f"<ol>{steps}</ol>" if steps else "<p>None</p>"
    conf = int(t.get("confidence_score", 0))
    conf_kind = "ok" if conf >= 70 else ("warn" if conf >= 40 else "danger")
    pr = t.get("priority", "Medium")
    pr_kind = {"Urgent": "danger", "High": "warn"}.get(pr, "accent")

    st.markdown(f"""
<div class="ticket" role="article" aria-label="support ticket draft">
  <div class="ticket-head">
    <div>
      <h3>{esc(t.get("title"))}</h3>
      <span class="ref">{esc(t.get("ticket_ref"))} · {esc(t.get("created_at"))} · AI-prepared draft</span>
    </div>
    <div style="display:flex; gap:8px; flex-wrap:wrap;">
      {badge(pr, pr_kind)}
      {badge(f"Risk: {t.get('risk_level', 'Low')}", "accent")}
      {badge(f"Confidence {conf}%", conf_kind)}
    </div>
  </div>
  <div class="ticket-body">
    <div class="sec grid">
      <div class="kv"><span class="k">Requester</span><span class="v">{esc(t.get("user_name"))} ({esc(t.get("user_role"))})</span></div>
      <div class="kv"><span class="k">Email</span><span class="v">{esc(t.get("user_email"))}</span></div>
      <div class="kv"><span class="k">Location</span><span class="v">{esc(t.get("user_location"))}</span></div>
    </div>
    <div class="sec"><h5>Summary</h5><p>{esc(t.get("executive_summary"))}</p></div>
    <div class="sec"><h5>Details</h5><p>{esc(t.get("detailed_description"))}</p></div>
    <div class="sec"><h5>Symptoms</h5>{ul(t.get("symptoms"))}</div>
    <div class="sec grid">
      <div class="kv"><span class="k">Environment</span><span class="v">{esc(t.get("environment"))}</span></div>
      <div class="kv"><span class="k">Device</span><span class="v">{esc(t.get("device_information"))}</span></div>
    </div>
    <div class="sec"><h5>Applications involved</h5>{ul(t.get("applications_involved"))}</div>
    <div class="sec"><h5>Error messages</h5>{ul(t.get("error_messages"))}</div>
    <div class="sec"><h5>Impact</h5><p>{esc(t.get("impact", t.get("business_impact")))}</p></div>
    <div class="sec"><h5>Troubleshooting completed</h5>{steps_html}</div>
    <div class="sec grid">
      <div class="kv"><span class="k">Assignment group</span><span class="v">{esc(t.get("assignment_group"))}</span></div>
      <div class="kv"><span class="k">Category</span><span class="v">{esc(t.get("category"))} › {esc(t.get("subcategory"))}</span></div>
      <div class="kv"><span class="k">Est. effort</span><span class="v">{esc(t.get("estimated_technician_effort"))}</span></div>
    </div>
    <div class="sec"><h5>Why this assignment group</h5><p>{esc(t.get("assignment_rationale"))}</p></div>
    <div class="sec"><h5>Why this priority</h5><p>{esc(t.get("priority_rationale"))}</p></div>
    <div class="sec"><h5>Suggested resolution path</h5><p>{esc(t.get("suggested_resolution_path"))}</p></div>
  </div>
</div>
""", unsafe_allow_html=True)
