"""Persistence layer — dual backend.

Uses hosted Postgres automatically when a DATABASE_URL is configured
(environment variable or Streamlit secrets — e.g. a free Supabase project),
so data survives Streamlit Cloud redeploys. Falls back to local SQLite for
development / offline use.

Tables: tickets, sessions, feedback, suggestions, attachments, admin_audit.
All queries are parameterized. Queries are written with '?' placeholders and
translated to '%s' for Postgres.
"""

import json
import os
import sqlite3
from datetime import datetime, timedelta

import config


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------
def _database_url() -> str | None:
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    try:
        import streamlit as st
        return st.secrets["DATABASE_URL"]
    except Exception:
        return None


def _schema(pg: bool) -> list[str]:
    auto = "SERIAL PRIMARY KEY" if pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    blob = "BYTEA" if pg else "BLOB"
    return [
        f"""CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            resolved_at TEXT,
            status TEXT NOT NULL DEFAULT 'Open',
            user_name TEXT, email TEXT, role TEXT,
            campus TEXT, building TEXT, room TEXT,
            language TEXT,
            category TEXT, subcategory TEXT,
            title TEXT, summary TEXT,
            assignment_group TEXT, priority TEXT, risk TEXT,
            confidence INTEGER,
            impact TEXT,
            ticket_json TEXT NOT NULL,
            log_json TEXT NOT NULL
        )""",
        f"""CREATE TABLE IF NOT EXISTS sessions (
            id {auto},
            created_at TEXT NOT NULL,
            campus TEXT, role TEXT, category TEXT, language TEXT,
            resolved INTEGER DEFAULT 0,
            ticket_generated INTEGER DEFAULT 0,
            escalated INTEGER DEFAULT 0,
            failed_step TEXT,
            resolved_step TEXT,
            device_type TEXT,
            steps_attempted INTEGER DEFAULT 0
        )""",
        f"""CREATE TABLE IF NOT EXISTS feedback (
            id {auto},
            created_at TEXT NOT NULL,
            ticket_id TEXT,
            session_id INTEGER,
            resolved TEXT,
            helpful INTEGER, easy INTEGER, accurate INTEGER,
            comments TEXT
        )""",
        f"""CREATE TABLE IF NOT EXISTS suggestions (
            id {auto},
            created_at TEXT NOT NULL,
            kind TEXT NOT NULL,
            title TEXT NOT NULL,
            reason TEXT,
            examples TEXT,
            confidence INTEGER,
            risk TEXT,
            status TEXT NOT NULL DEFAULT 'Pending'
        )""",
        f"""CREATE TABLE IF NOT EXISTS attachments (
            id {auto},
            created_at TEXT NOT NULL,
            ticket_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            mime TEXT NOT NULL,
            content {blob} NOT NULL
        )""",
        f"""CREATE TABLE IF NOT EXISTS admin_audit (
            id {auto},
            created_at TEXT NOT NULL,
            success INTEGER NOT NULL,
            note TEXT
        )""",
    ]


_SCHEMA_DONE: set[str] = set()


def _connect():
    """Return (is_pg, connection). Creates schema once per process/backend."""
    url = _database_url()
    if url:
        import psycopg2
        conn = psycopg2.connect(url)
        kind = "pg"
    else:
        conn = sqlite3.connect(config.DB_PATH)
        conn.row_factory = sqlite3.Row
        kind = "sqlite"
    if kind not in _SCHEMA_DONE:
        cur = conn.cursor()
        for stmt in _schema(kind == "pg"):
            cur.execute(stmt)
        conn.commit()
        _SCHEMA_DONE.add(kind)
    return kind == "pg", conn


def _rows_to_dicts(is_pg: bool, cur) -> list[dict]:
    if is_pg:
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]
    return [dict(r) for r in cur.fetchall()]


def _run(sql: str, params: tuple = (), fetch: str | None = None,
         returning_id: bool = False):
    """Execute one statement. fetch: None | 'one' | 'all'."""
    is_pg, conn = _connect()
    try:
        cur = conn.cursor()
        q = sql.replace("?", "%s") if is_pg else sql
        if returning_id and is_pg:
            q += " RETURNING id"
        cur.execute(q, params)
        result = None
        if fetch == "all":
            result = _rows_to_dicts(is_pg, cur)
        elif fetch == "one":
            rows = _rows_to_dicts(is_pg, cur)
            result = rows[0] if rows else None
        elif returning_id:
            result = cur.fetchone()[0] if is_pg else cur.lastrowid
        conn.commit()
        return result
    finally:
        conn.close()


def using_postgres() -> bool:
    return _database_url() is not None


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------
def create_session(campus: str, role: str, category: str, language: str) -> int:
    return _run(
        "INSERT INTO sessions (created_at, campus, role, category, language) VALUES (?,?,?,?,?)",
        (now(), campus, role, category, language), returning_id=True,
    )


def update_session(session_id: int, **fields):
    if not fields or session_id is None:
        return
    cols = ", ".join(f"{k}=?" for k in fields)
    _run(f"UPDATE sessions SET {cols} WHERE id=?", (*fields.values(), session_id))


def list_resolutions(limit: int = 100) -> list[dict]:
    """Self-resolved sessions (no ticket) — what got fixed and the step that worked."""
    return _run(
        "SELECT created_at, category, device_type, resolved_step, steps_attempted "
        "FROM sessions WHERE resolved=1 ORDER BY created_at DESC LIMIT ?",
        (limit,), fetch="all")


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------
def save_ticket(ticket: dict, log: list, intake: dict, language: str):
    _run(
        """INSERT INTO tickets
           (id, created_at, status, user_name, email, role, campus, building, room,
            language, category, subcategory, title, summary, assignment_group,
            priority, risk, confidence, impact, ticket_json, log_json)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT (id) DO UPDATE SET
             title=excluded.title, summary=excluded.summary,
             assignment_group=excluded.assignment_group, priority=excluded.priority,
             risk=excluded.risk, ticket_json=excluded.ticket_json,
             log_json=excluded.log_json""",
        (
            ticket.get("ticket_ref"), ticket.get("created_at", now()), "Open",
            intake.get("name"), intake.get("email"), intake.get("role"),
            intake.get("campus"), intake.get("building"), intake.get("room"),
            language, ticket.get("category"), ticket.get("subcategory"),
            ticket.get("title"), ticket.get("executive_summary"),
            ticket.get("assignment_group"), ticket.get("priority"),
            ticket.get("risk_level"), ticket.get("confidence_score"),
            ticket.get("impact"),
            json.dumps(ticket, ensure_ascii=False),
            json.dumps(log, ensure_ascii=False),
        ),
    )


def update_ticket_status(ticket_id: str, status: str):
    _run("UPDATE tickets SET status=?, resolved_at=? WHERE id=?",
         (status, now() if status == "Resolved" else None, ticket_id))


def list_tickets(limit: int = 200) -> list[dict]:
    return _run("SELECT * FROM tickets ORDER BY created_at DESC LIMIT ?",
                (limit,), fetch="all")


def similar_tickets(campus: str, category: str, hours: int = 48,
                    exclude_ref: str | None = None) -> list[dict]:
    """Open tickets from the same campus + category within the window (M6)."""
    since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    rows = _run(
        """SELECT id, title, created_at FROM tickets
           WHERE campus=? AND category=? AND status IN ('Open','In Progress')
             AND created_at >= ? ORDER BY created_at DESC LIMIT 10""",
        (campus, category, since), fetch="all")
    return [r for r in rows if r["id"] != exclude_ref]


# ---------------------------------------------------------------------------
# Attachments (M7)
# ---------------------------------------------------------------------------
def save_attachment(ticket_id: str, filename: str, mime: str, content: bytes):
    _run("INSERT INTO attachments (created_at, ticket_id, filename, mime, content) VALUES (?,?,?,?,?)",
         (now(), ticket_id, filename, mime, content))


def list_attachments(ticket_id: str) -> list[dict]:
    rows = _run("SELECT filename, mime, content FROM attachments WHERE ticket_id=? ORDER BY id",
                (ticket_id,), fetch="all")
    for r in rows:  # psycopg2 returns memoryview for BYTEA
        if not isinstance(r["content"], (bytes, bytearray)):
            r["content"] = bytes(r["content"])
    return rows


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------
def save_feedback(ticket_id: str | None, session_id: int | None, resolved: str,
                  helpful: int, easy: int, accurate: int, comments: str):
    _run("""INSERT INTO feedback (created_at, ticket_id, session_id, resolved,
            helpful, easy, accurate, comments) VALUES (?,?,?,?,?,?,?,?)""",
         (now(), ticket_id, session_id, resolved, helpful, easy, accurate, comments))


# ---------------------------------------------------------------------------
# Admin audit (C4)
# ---------------------------------------------------------------------------
def log_admin_attempt(success: bool, note: str = ""):
    _run("INSERT INTO admin_audit (created_at, success, note) VALUES (?,?,?)",
         (now(), 1 if success else 0, note))


# ---------------------------------------------------------------------------
# Suggestions (admin review queue)
# ---------------------------------------------------------------------------
def add_suggestion(kind: str, title: str, reason: str, examples: str,
                   confidence: int, risk: str):
    dup = _run("SELECT 1 AS x FROM suggestions WHERE title=? AND status='Pending'",
               (title,), fetch="one")
    if not dup:
        _run("""INSERT INTO suggestions (created_at, kind, title, reason, examples,
                confidence, risk) VALUES (?,?,?,?,?,?,?)""",
             (now(), kind, title, reason, examples, confidence, risk))


def list_suggestions(status: str | None = None) -> list[dict]:
    if status:
        return _run("SELECT * FROM suggestions WHERE status=? ORDER BY created_at DESC",
                    (status,), fetch="all")
    return _run("SELECT * FROM suggestions ORDER BY created_at DESC", (), fetch="all")


def set_suggestion_status(sid: int, status: str):
    _run("UPDATE suggestions SET status=? WHERE id=?", (status, sid))


# ---------------------------------------------------------------------------
# Analytics for the Improvement Dashboard
# ---------------------------------------------------------------------------
def metrics() -> dict:
    one = lambda q, *a: (_run(q, a, fetch="one") or {"n": 0})["n"]
    total_sessions = one("SELECT COUNT(*) AS n FROM sessions")
    resolved_sessions = one("SELECT COUNT(*) AS n FROM sessions WHERE resolved=1")
    tickets_generated = one("SELECT COUNT(*) AS n FROM tickets")
    avg = _run("SELECT AVG(helpful) AS h, AVG(easy) AS e, AVG(accurate) AS a FROM feedback",
               (), fetch="one") or {}
    return {
        "total_sessions": total_sessions,
        "tickets_prevented": resolved_sessions,
        "tickets_generated": tickets_generated,
        "avg_helpful": round(float(avg.get("h") or 0), 2),
        "avg_easy": round(float(avg.get("e") or 0), 2),
        "avg_accurate": round(float(avg.get("a") or 0), 2),
        "top_categories": _run(
            "SELECT category, COUNT(*) AS n FROM sessions WHERE category IS NOT NULL "
            "GROUP BY category ORDER BY n DESC LIMIT 5", (), fetch="all"),
        "top_campus_issues": _run(
            "SELECT campus, category, COUNT(*) AS n FROM sessions "
            "WHERE campus IS NOT NULL GROUP BY campus, category ORDER BY n DESC LIMIT 5",
            (), fetch="all"),
        "top_failed_steps": _run(
            "SELECT failed_step, COUNT(*) AS n FROM sessions WHERE failed_step IS NOT NULL "
            "AND failed_step != '' GROUP BY failed_step ORDER BY n DESC LIMIT 5",
            (), fetch="all"),
        "escalation_by_category": _run(
            "SELECT category, SUM(escalated) AS esc, COUNT(*) AS n FROM sessions "
            "GROUP BY category ORDER BY esc DESC LIMIT 8", (), fetch="all"),
        "groups": _run(
            "SELECT assignment_group, COUNT(*) AS n FROM tickets "
            "GROUP BY assignment_group ORDER BY n DESC", (), fetch="all"),
        # ~18 min saved per prevented ticket + ~7 min per high-quality ticket
        "time_saved_minutes": resolved_sessions * 18 + tickets_generated * 7,
    }


def generate_suggestions():
    """Heuristic analysis of history -> pending suggestions for admin review."""
    m = metrics()
    for row in m["top_failed_steps"][:3]:
        if row["n"] >= 2:
            add_suggestion(
                "Troubleshooting step", f"Users struggle with: {row['failed_step']}",
                f"This step was reported as failed or needing help {row['n']} times. "
                "Consider adding visual guidance or simplifying the instructions.",
                f"{row['n']} sessions recorded this step as a failure point.",
                min(50 + row["n"] * 10, 90), "Low")
    for row in m["escalation_by_category"]:
        if row["n"] >= 3 and row["esc"] and row["esc"] / row["n"] > 0.7:
            add_suggestion(
                "Category escalation rate",
                f"High escalation rate in category: {row['category']}",
                f"{row['esc']} of {row['n']} sessions in this category escalated to a ticket. "
                "The guided flow may need additional steps or a knowledge base article.",
                f"{row['n']} sessions analyzed.", 70, "Medium")
    low = (_run("SELECT COUNT(*) AS n FROM feedback WHERE accurate IS NOT NULL AND accurate <= 1",
                (), fetch="one") or {"n": 0})["n"]
    if low >= 2:
        add_suggestion(
            "Ticket template", "Summaries rated inaccurate by users",
            f"{low} feedback responses rated summary accuracy the lowest score. "
            "Review the summary template and description generation.",
            f"{low} low accuracy ratings.", 60, "Medium")
    es = (_run("SELECT COUNT(*) AS n FROM sessions WHERE language='es'", (), fetch="one")
          or {"n": 0})["n"]
    if es >= 3:
        add_suggestion(
            "Spanish translation", "Growing Spanish-language usage — review translations",
            f"{es} sessions were completed in Spanish. Schedule a native-speaker review "
            "of troubleshooting flows and ticket summaries.",
            f"{es} Spanish sessions.", 55, "Low")
