"""Ticket email dispatch (C2).

Sends the ticket to the service desk on Submit, with optional photo
attachments and an optional copy to the requester. Configuration comes from
environment variables or Streamlit secrets:

    SMTP_HOST          e.g. smtp.gmail.com or smtp.sendgrid.net
    SMTP_PORT          default 587 (STARTTLS)
    SMTP_USER          SMTP username (optional for open relays)
    SMTP_PASS          SMTP password / app password / API key
    SERVICE_DESK_EMAIL destination inbox for tickets
    FROM_EMAIL         sender address (defaults to SMTP_USER)
    CC_REQUESTER       "true" to copy the user on their own ticket

If unconfigured, the app degrades gracefully: tickets are still stored and
downloadable, and the UI says dispatch is not configured.
"""

import os
import smtplib
from email.message import EmailMessage


def _cfg(name: str, default=None):
    v = os.environ.get(name)
    if v:
        return v
    try:
        import streamlit as st
        return st.secrets[name]
    except Exception:
        return default


def is_configured() -> bool:
    return bool(_cfg("SMTP_HOST") and _cfg("SERVICE_DESK_EMAIL"))


def cc_requester_enabled() -> bool:
    return str(_cfg("CC_REQUESTER", "false")).lower() in ("1", "true", "yes")


def send_ticket(ticket_md: str, ticket: dict,
                attachments: list[tuple[str, bytes, str]] | None = None,
                requester_email: str | None = None) -> str:
    """Send the ticket. Returns the destination address. Raises on failure."""
    to_addr = _cfg("SERVICE_DESK_EMAIL")
    msg = EmailMessage()
    msg["Subject"] = f"[{ticket.get('priority', 'Medium')}] {ticket.get('title', 'Support ticket')} — {ticket.get('ticket_ref', '')}"
    msg["From"] = _cfg("FROM_EMAIL", _cfg("SMTP_USER", "it-assistant@district.local"))
    msg["To"] = to_addr
    if requester_email and cc_requester_enabled():
        msg["Cc"] = requester_email
    msg.set_content(ticket_md)

    for filename, content, mime in (attachments or []):
        maintype, _, subtype = mime.partition("/")
        msg.add_attachment(content, maintype=maintype or "application",
                           subtype=subtype or "octet-stream", filename=filename)

    host = _cfg("SMTP_HOST")
    port = int(_cfg("SMTP_PORT", "587"))
    user, password = _cfg("SMTP_USER"), _cfg("SMTP_PASS")
    with smtplib.SMTP(host, port, timeout=20) as server:
        server.ehlo()
        try:
            server.starttls()
            server.ehlo()
        except smtplib.SMTPNotSupportedError:
            pass  # relay without TLS (internal servers)
        if user and password:
            server.login(user, password)
        server.send_message(msg)
    return to_addr
