"""IT Support Assistant. AI front end to the district ticketing platform.

Run:  streamlit run app.py

Issue-first flow (M1): the conversation opens with the user's problem.
Identity details are collected only when a ticket is needed. Includes rate
limiting (C5), duplicate detection (M6), photo attachments (M7), and real
email dispatch when configured (C2). Storage survives redeploys when a
DATABASE_URL is configured (C1).
"""

import os
import time

import streamlit as st

import admin
import config
import intake_flow
import knowledge_base as kb
import mailer
import safety
import storage
import ui
from demo_engine import DemoEngine, demo_ticket, new_state
from engine import DiagnosticEngine, Turn
from strings import L
from ticket import generate_ticket, summary_to_text, ticket_to_markdown

st.set_page_config(page_title=config.APP_NAME, page_icon="🛠️", layout="wide",
                   initial_sidebar_state="expanded")


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
def init_state():
    ss = st.session_state
    ss.setdefault("lang", "en")
    ss.setdefault("theme", "dark")
    ss.setdefault("a11y", {"text_size": "normal", "high_contrast": False,
                           "reduce_motion": False, "read_aloud": False,
                           "voice_input": False, "simple": False})
    ss.setdefault("mode", "support")
    ss.setdefault("messages", [])
    ss.setdefault("api_messages", [])
    ss.setdefault("demo_state", None)
    ss.setdefault("log", [])
    ss.setdefault("last_turn", None)
    ss.setdefault("ticket", None)
    ss.setdefault("submitted", False)
    ss.setdefault("feedback_done", False)
    ss.setdefault("session_id", None)
    ss.setdefault("pending_input", None)
    ss.setdefault("force_escalate", False)
    # Ticket-time identity intake (M1)
    ss.setdefault("intake", None)
    ss.setdefault("identity_data", {})
    ss.setdefault("identity_mode", False)
    ss.setdefault("pending_reason", "")
    # Attachments / duplicates / dispatch
    ss.setdefault("attachments", [])
    ss.setdefault("dup_matches", [])
    ss.setdefault("dispatch_note", None)
    # Rate limiting
    ss.setdefault("last_input_ts", 0.0)
    ss.setdefault("category_recorded", False)


def start_over():
    for k in ["messages", "api_messages", "demo_state", "log", "last_turn", "ticket",
              "submitted", "feedback_done", "session_id", "pending_input",
              "force_escalate", "intake", "identity_data", "identity_mode",
              "pending_reason", "attachments", "dup_matches", "dispatch_note",
              "last_input_ts", "category_recorded"]:
        st.session_state.pop(k, None)
    init_state()


init_state()
LANG = st.session_state.lang
A11Y = st.session_state.a11y
ui.inject_css(ui.theme_key(st.session_state.theme, A11Y["high_contrast"]),
              A11Y["text_size"], A11Y["reduce_motion"])


def get_api_key() -> str | None:
    if st.session_state.get("api_key_input"):
        return st.session_state.api_key_input
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return None


api_key = get_api_key()
demo = DemoEngine()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def say(text: str):
    st.session_state.messages.append({"role": "assistant", "content": text, "step": None})


def user_message_count() -> int:
    return sum(1 for m in st.session_state.messages if m["role"] == "user")


def matched_entry() -> dict | None:
    ds = st.session_state.demo_state
    if ds and ds.get("entry_id"):
        return kb.BY_ID.get(ds["entry_id"])
    return None


def ensure_session():
    ss = st.session_state
    if ss.session_id is None:
        ss.session_id = storage.create_session("Unknown", "Unknown", "unmatched", LANG)


def apply_turn(turn: Turn):
    ss = st.session_state
    ss.messages.append({"role": "assistant", "content": turn.reply, "step": turn.step})
    ss.log.extend(turn.log_entries)
    ss.last_turn = turn
    entry = matched_entry()
    if ss.session_id:
        failed = [e["detail"] for e in turn.log_entries
                  if e["kind"] == "finding" and "needed help" in e["detail"]]
        updates = {"steps_attempted": sum(1 for e in ss.log if e["kind"] == "step_attempted")}
        if entry and not ss.category_recorded:
            updates["category"] = entry["id"]
            ss.category_recorded = True
        mem = ss.demo_state.get("memory") if ss.demo_state else None
        if mem and mem.get("device_type"):
            updates["device_type"] = mem["device_type"]
        if turn.phase == "resolved":
            updates["resolved"] = 1
            rstep = next((e["detail"].replace("Resolved by step: ", "")
                          for e in turn.log_entries
                          if e["kind"] == "finding" and e["detail"].startswith("Resolved by step:")), None)
            if rstep:
                updates["resolved_step"] = rstep
        if turn.phase == "escalation_offer":
            updates["escalated"] = 1
        if failed:
            updates["failed_step"] = failed[-1].replace("User needed help with step: ", "")
        elif turn.phase == "escalation_offer" and ss.demo_state and ss.demo_state.get("failed_steps"):
            updates["failed_step"] = ss.demo_state["failed_steps"][-1]
        storage.update_session(ss.session_id, **updates)


def run_engine(user_text: str):
    ss = st.session_state
    ensure_session()
    # Safety gate 1: refuse bypass / hacking / unauthorized-access requests cleanly.
    if safety.is_disallowed(user_text):
        ss.messages.append({"role": "user", "content": user_text, "step": None})
        say(L("boundary_reply", LANG))
        ss.log.append({"kind": "finding", "detail": "Refused a disallowed (bypass/unauthorized) request."})
        st.rerun()
    # Safety gate 2: don't store sensitive PII. Warn and let them rephrase.
    if safety.has_pii(user_text):
        say(L("pii_warning", LANG))
        st.rerun()
    ss.messages.append({"role": "user", "content": user_text, "step": None})
    ss.api_messages.append({"role": "user", "content": user_text})
    with st.chat_message("assistant", avatar="🛠️"):
        placeholder = st.empty()
        ui.thinking(placeholder, LANG)
        try:
            if api_key:
                context = ss.api_messages[-config.MAX_CONTEXT_MESSAGES:]
                turn = DiagnosticEngine(api_key).next_turn(
                    context, intake=ss.intake, lang=LANG, simple=A11Y["simple"])
            else:
                turn, ss.demo_state = demo.next_turn(ss.demo_state, user_text,
                                                     ss.intake or {}, LANG)
        except Exception as e:
            placeholder.empty()
            st.error(f"{L('error_generic', LANG)} ({type(e).__name__})")
            ss.messages.pop()
            ss.api_messages.pop()
            return
        placeholder.empty()
    ss.api_messages.append({"role": "assistant", "content": turn.to_history_text()})
    apply_turn(turn)
    st.rerun()


def handle_identity(user_text: str):
    """Ticket-time identity intake, one question at a time."""
    ss = st.session_state
    ss.messages.append({"role": "user", "content": user_text, "step": None})
    step = intake_flow.next_step(ss.identity_data)
    ok, updates, err = intake_flow.process(step, user_text, LANG)
    if not ok:
        say(err)
        st.rerun()
    ss.identity_data.update(updates)
    nxt = intake_flow.next_step(ss.identity_data)
    if nxt:
        say(intake_flow.prompt(nxt, LANG, ss.identity_data))
        st.rerun()
    # Identity complete -> finalize and build the ticket
    entry = matched_entry()
    category = entry["categories"][0] if entry else "other"
    ss.intake = intake_flow.finalize(ss.identity_data, category)
    ss.identity_mode = False
    ss.log.append({"kind": "info_collected",
                   "detail": f"Requester: {ss.intake['name']} ({ss.intake['role']}), "
                             f"{ss.intake['campus']}"
                             f"{' rm ' + ss.intake['room'] if ss.intake['room'] else ''}, "
                             f"device: {ss.intake['device']}"})
    storage.update_session(ss.session_id, campus=ss.intake["campus"], role=ss.intake["role"])
    build_ticket(ss.pending_reason or "User requested a technician.")


def begin_escalation(reason: str):
    """Capture attachments, then collect identity if we don't have it yet."""
    ss = st.session_state
    files = st.session_state.get("att_up") or []
    ss.attachments = []
    for f in files[:config.MAX_ATTACHMENTS]:
        data = f.getvalue()
        if len(data) <= config.MAX_ATTACHMENT_MB * 1024 * 1024:
            ss.attachments.append((f.name, data, f.type or "image/png"))
    ss.force_escalate = False
    ss.pending_reason = reason
    # Carry the device we already inferred into identity intake so it's not re-asked.
    mem = ss.demo_state.get("memory") if ss.demo_state else None
    if mem and mem.get("device_type"):
        ss.identity_data.setdefault("device", mem["device_type"])
    if ss.intake is None:
        ss.identity_mode = True
        say(intake_flow.prompt(intake_flow.next_step(ss.identity_data), LANG, ss.identity_data))
        st.rerun()
    build_ticket(reason)


def build_ticket(reason: str):
    ss = st.session_state
    ensure_session()
    transcript = [{"role": m["role"], "content": m["content"]} for m in ss.messages]
    with st.spinner(L("preparing_ticket", LANG)):
        try:
            if api_key:
                ss.ticket = generate_ticket(api_key, transcript, ss.log, reason, ss.intake, LANG)
            else:
                ss.ticket = demo_ticket(ss.intake, ss.log, ss.demo_state or new_state("other"),
                                        reason, LANG)
        except Exception as e:
            st.error(f"{L('error_generic', LANG)} ({type(e).__name__})")
            return
    t = ss.ticket
    if not any(e["kind"] == "escalation_reason" for e in ss.log):
        ss.log.append({"kind": "escalation_reason", "detail": reason})
    # M6: duplicate detection before saving
    ss.dup_matches = storage.similar_tickets(ss.intake.get("campus", ""), t.get("category", ""),
                                             hours=48, exclude_ref=t.get("ticket_ref"))
    if ss.dup_matches:
        refs = ", ".join(d["id"] for d in ss.dup_matches[:5])
        t["detailed_description"] += f" | Possible related open tickets (same campus/category, 48h): {refs}."
        ss.log.append({"kind": "finding",
                       "detail": f"Duplicate check: {len(ss.dup_matches)} similar open ticket(s): {refs}"})
    storage.save_ticket(t, ss.log, ss.intake, LANG)
    # M7: persist attachments
    for name, data, mime in ss.attachments:
        storage.save_attachment(t["ticket_ref"], name, mime, data)
    if ss.attachments:
        t["detailed_description"] += f" | {len(ss.attachments)} photo attachment(s) on file."
    storage.update_session(ss.session_id, ticket_generated=1, escalated=1)
    st.rerun()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"""
<div style="display:flex; align-items:center; gap:10px; padding:4px 0 12px;">
  <div style="width:34px;height:34px;border-radius:10px;background:var(--accent);
       color:#fff;display:flex;align-items:center;justify-content:center;
       font-weight:700;font-size:13px;">{config.ORG_SHORT}</div>
  <div style="font-weight:650;font-size:14.5px;">{config.APP_NAME}</div>
</div>
""", unsafe_allow_html=True)

    mode = st.session_state.mode  # set inside IT Staff Options; default 'support'

    lang_choice = st.radio(L("language", LANG), ["en", "es"],
                           index=0 if LANG == "en" else 1,
                           format_func=lambda x: "English" if x == "en" else "Español",
                           horizontal=True)
    if lang_choice != LANG:
        st.session_state.lang = lang_choice
        st.rerun()

    dark = st.toggle(L("dark_theme", LANG), value=(st.session_state.theme == "dark"))
    if ("dark" if dark else "light") != st.session_state.theme:
        st.session_state.theme = "dark" if dark else "light"
        st.rerun()

    with st.expander(L("a11y_title", LANG)):
        size = st.radio(L("a11y_text_size", LANG), ["normal", "large", "xlarge"],
                        index=["normal", "large", "xlarge"].index(A11Y["text_size"]),
                        format_func=lambda s: L(f"a11y_size_{s}", LANG), horizontal=True)
        hc = st.toggle(L("a11y_high_contrast", LANG), value=A11Y["high_contrast"])
        rm = st.toggle(L("a11y_reduce_motion", LANG), value=A11Y["reduce_motion"])
        ra = st.toggle(L("a11y_read_aloud", LANG), value=A11Y["read_aloud"])
        vi = st.toggle(L("a11y_voice_input", LANG), value=A11Y["voice_input"])
        sm = st.toggle(L("a11y_simple", LANG), value=A11Y["simple"])
        new_a11y = {"text_size": size, "high_contrast": hc, "reduce_motion": rm,
                    "read_aloud": ra, "voice_input": vi, "simple": sm}
        if new_a11y != A11Y:
            st.session_state.a11y = new_a11y
            st.rerun()

    if mode == "support" and st.session_state.last_turn and user_message_count() > 0:
        st.divider()
        ui.session_panel(st.session_state.last_turn, LANG)
        ui.timeline_panel(st.session_state.log, LANG)

    st.divider()
    if mode == "support" and st.session_state.ticket is None and user_message_count() > 0:
        if st.button(f"🎫 {L('request_technician', LANG)}", use_container_width=True):
            st.session_state.force_escalate = True
            st.rerun()
    if st.button(f"↺ {L('start_over', LANG)}", use_container_width=True):
        start_over()
        st.rerun()

    _urgent = "Urgent help" if LANG == "en" else "Ayuda urgente"
    st.markdown(f"""
<div class="panel" style="margin-top:8px;">
  <h4>📞 {_urgent}</h4>
  <div style="font-size:13px;line-height:1.5;">{L('urgent_help', LANG, phone=config.SERVICE_DESK_PHONE)}</div>
</div>
""", unsafe_allow_html=True)

    # --- Advanced / IT-staff-only controls, collapsed by default ---
    st.divider()
    with st.expander(f"🔧 {L('it_staff_options', LANG)}"):
        adm = st.toggle("Admin mode", value=(st.session_state.mode == "admin"))
        new_mode = "admin" if adm else "support"
        if new_mode != st.session_state.mode:
            st.session_state.mode = new_mode
            st.rerun()
        st.text_input("Anthropic API key", type="password", key="api_key_input",
                      help="Optional. Enables the adaptive AI engine. Leave blank to use "
                           "the built-in knowledge-base engine.")
        st.markdown(
            f"**Engine:** {'Claude AI + KB' if api_key else 'Built-in KB engine'}  \n"
            f"**Database:** {'Postgres (persistent)' if storage.using_postgres() else 'SQLite (local, resets on redeploy)'}  \n"
            f"**Email dispatch:** {'Configured' if mailer.is_configured() else 'Not configured'}"
        )


# ---------------------------------------------------------------------------
# Admin mode
# ---------------------------------------------------------------------------
if st.session_state.mode == "admin":
    ui.header(LANG)
    admin.render()
    st.stop()

# ---------------------------------------------------------------------------
# Support mode. Issue-first conversation
# ---------------------------------------------------------------------------
ui.header(LANG)

ss = st.session_state
if not ss.messages:
    ss.demo_state = new_state("other")
    first = demo.first_turn(ss.demo_state, {}, LANG)
    ss.messages.append({"role": "assistant", "content": first.reply, "step": None})
    ss.last_turn = first

turn: Turn = ss.last_turn
entry = matched_entry()

# Welcome hero + prototype disclaimer. Shown at the very start only.
if user_message_count() == 0 and ss.ticket is None and not ss.identity_mode:
    ui.welcome_hero(LANG)
    ui.prototype_notice(LANG)

col_chat, col_side = st.columns([2.2, 1], gap="medium")

with col_side:
    ui.privacy_notice(LANG)
    if entry and set(entry["categories"]) & intake_flow.SENSITIVE_CATEGORIES:
        ui.sensitive_warning(LANG)
    if ss.identity_mode:
        cur, total = intake_flow.progress(ss.identity_data)
        ui.progress_bar(cur, total, LANG)
    elif turn and ss.ticket is None and user_message_count() > 0:
        ui.progress_bar(turn.progress_current, turn.progress_total, LANG)
    st.markdown(f"""
<div class="panel">
  <h4>{L('ticket_panel', LANG)}</h4>
  <div style="font-size:12.5px;color:var(--muted);line-height:1.5;">
    {("🎫 " + ui.esc(ss.ticket.get("title"))) if ss.ticket else ui.esc(L('no_ticket_yet', LANG))}
  </div>
</div>
""", unsafe_allow_html=True)

with col_chat:
    for i, msg in enumerate(ss.messages):
        avatar = "🛠️" if msg["role"] == "assistant" else "🧑"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])
            if msg.get("step"):
                ui.step_card(msg["step"], LANG)
            if (msg["role"] == "assistant" and A11Y["read_aloud"]
                    and i == len(ss.messages) - 1):
                speak = msg["content"]
                if msg.get("step"):
                    s = msg["step"]
                    speak += (f". {s['title']}. {L('what_to_do', LANG)}: {s['what']}. "
                              f"{L('why_matters', LANG)}: {s['why']}. "
                              f"{L('expected_result', LANG)}: {s['expected']}.")
                ui.tts_button(speak, LANG, key=f"tts{i}")

    # ---- Support summary view (end-user) ----
    if ss.ticket is not None:
        t = ss.ticket
        st.markdown(f"### {L('ticket_ready', LANG)}")
        st.caption(L("ticket_review", LANG))
        if ss.dup_matches:
            st.info(L("dup_notice", LANG, n=len(ss.dup_matches),
                      campus=ss.intake.get("campus", "")))
        if ss.attachments:
            st.caption(f"📎 {len(ss.attachments)} × " + ", ".join(a[0] for a in ss.attachments))

        ui.summary_preview(t, LANG)

        summary_text = summary_to_text(t)
        c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1])
        with c1:
            copy_clicked = st.button(f"📋 {L('copy_summary', LANG)}", type="primary",
                                     use_container_width=True)
        with c2:
            st.download_button(L("download_txt", LANG), summary_text,
                               file_name=f"support-summary-{t['ticket_ref']}.txt",
                               use_container_width=True)
        with c3:
            edit_mode = st.toggle(f"✏️ {L('edit_ticket', LANG)}")
        with c4:
            if st.button(L("start_over", LANG), key="ticket_restart", use_container_width=True):
                start_over()
                st.rerun()

        # Copy-ready text. Always available, opened on demand
        with st.expander(f"📄 {L('sum_copyready', LANG)}", expanded=copy_clicked):
            st.caption(L("copy_hint", LANG))
            st.code(summary_text, language=None)

        if edit_mode:
            with st.form("edit_ticket"):
                new_title = st.text_input(L("sum_issue", LANG), t["title"])
                new_summary = st.text_area(L("sum_issue", LANG) + " ", t["executive_summary"])
                if st.form_submit_button(L("save_changes", LANG), type="primary"):
                    t.update({"title": new_title, "executive_summary": new_summary})
                    storage.save_ticket(t, ss.log, ss.intake, LANG)
                    st.rerun()

        # Technical triage is intentionally NOT shown here. It is saved with the
        # ticket and only visible to IT staff in Admin mode → Ticket History.

    # ---- Escalation offer (attachments + identity gate) ----
    elif turn and not ss.identity_mode and (turn.phase == "escalation_offer" or ss.force_escalate):
        reason = turn.escalation_reason or "User requested a technician."
        if ss.force_escalate:
            reason = "User requested escalation to a technician."
        st.file_uploader(L("attach_label", LANG), type=["png", "jpg", "jpeg", "webp"],
                         accept_multiple_files=True, key="att_up",
                         help=L("attach_hint", LANG, n=config.MAX_ATTACHMENTS,
                                mb=config.MAX_ATTACHMENT_MB))
        b1, b2 = st.columns([1.3, 1])
        with b1:
            if st.button(f"🎫 {L('generate_ticket', LANG)}", type="primary", use_container_width=True):
                begin_escalation(reason)
        with b2:
            if api_key and st.button(L("keep_troubleshooting", LANG), use_container_width=True):
                ss.force_escalate = False
                run_engine("Let's keep troubleshooting. What else can we try?")

    # ---- Resolved ----
    elif turn and turn.phase == "resolved":
        st.success(L("resolved_banner", LANG))

    # ---- Quick replies (identity intake or diagnostics) ----
    if ss.ticket is None:
        if ss.identity_mode:
            cur_step = intake_flow.next_step(ss.identity_data)
            quick = intake_flow.quick_replies(cur_step, LANG) if cur_step else []
        else:
            quick = turn.quick_replies if (turn and turn.phase != "resolved") else []
        if quick:
            st.markdown(f'<div class="quick-label">{L("quick_answers", LANG)}</div>',
                        unsafe_allow_html=True)
            per_row = 4
            for r in range(0, len(quick), per_row):
                row = quick[r:r + per_row]
                cols = st.columns(per_row)
                for i, qr in enumerate(row):
                    if cols[i].button(qr, key=f"qr_{len(ss.messages)}_{r}_{i}",
                                      use_container_width=True):
                        ss.pending_input = qr
        if A11Y["voice_input"] and (ss.identity_mode or (turn and turn.phase != "resolved")):
            ui.mic_widget(LANG)

    # ---- Post-resolution / post-summary feedback ----
    show_feedback = ((turn and turn.phase == "resolved") or ss.ticket is not None) \
                    and not ss.feedback_done
    if show_feedback:
        st.divider()
        st.markdown(f"#### ⭐ {L('feedback_title', LANG)}")
        with st.form("feedback_form"):
            resolved = st.radio(L("fb_resolved", LANG),
                                [L("yes", LANG), L("partially", LANG), L("no", LANG)],
                                horizontal=True)
            scale = [1, 2, 3]  # 3 = best
            labels = {1: L("rate_low", LANG), 2: L("rate_mid", LANG), 3: L("rate_high", LANG)}
            fmt = lambda n: labels[n]
            helpful = st.radio(L("fb_helpful", LANG), scale, index=2, format_func=fmt, horizontal=True)
            easy = st.radio(L("fb_easy", LANG), scale, index=2, format_func=fmt, horizontal=True)
            accurate = st.radio(L("fb_accurate", LANG), scale, index=2, format_func=fmt, horizontal=True)
            comments = st.text_area(L("fb_comments", LANG))
            if st.form_submit_button(L("fb_submit", LANG), type="primary"):
                storage.save_feedback(
                    ss.ticket["ticket_ref"] if ss.ticket else None,
                    ss.session_id, resolved, helpful, easy, accurate, comments[:2000])
                ss.feedback_done = True
                st.rerun()
    if ss.feedback_done:
        st.success(L("fb_thanks", LANG))
        if st.button(L("new_session", LANG), type="primary"):
            start_over()
            st.rerun()

# ---------------------------------------------------------------------------
# Chat input with rate limiting (C5)
# ---------------------------------------------------------------------------
input_active = ss.ticket is None and (ss.identity_mode or (turn and turn.phase != "resolved"))
if input_active:
    prompt = st.chat_input(L("chat_placeholder", LANG))
    user_text = prompt or ss.pending_input
    if user_text:
        ss.pending_input = None
        now = time.time()
        if len(user_text) > config.MAX_INPUT_CHARS:
            with col_chat:
                st.warning(L("input_too_long", LANG, n=config.MAX_INPUT_CHARS))
        elif now - ss.last_input_ts < config.COOLDOWN_SECONDS:
            pass  # ignore rapid-fire input
        elif user_message_count() >= config.MAX_MESSAGES:
            ss.force_escalate = True
            if not ss.messages or L("limit_reached", LANG) != ss.messages[-1]["content"]:
                say(L("limit_reached", LANG))
            st.rerun()
        else:
            ss.last_input_ts = now
            with col_chat:
                if ss.identity_mode:
                    handle_identity(user_text.strip())
                else:
                    run_engine(user_text.strip())
