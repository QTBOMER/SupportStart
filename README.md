# SupportStart (Demo)

> **Portfolio prototype — not an official system for any school or district, and it
> does not submit real tickets.** Please don't enter real district or student data.
> The IT Staff view is intentionally viewable for demonstration; demo access code `admin123`.

I built a prototype AI support assistant for school technology issues. The goal is to
reduce bad tickets by guiding users through safe troubleshooting first, then generating
a technician-ready summary only when needed. The backend demo shows how IT staff could
review summaries, routing suggestions, failed steps, and improvement metrics.

It's bilingual (English/Español) and accessible, with a structured knowledge base of
30+ common school IT issues (Chromebooks, Windows/Mac, Wi-Fi, printers, displays,
Google Workspace, Microsoft Office, Schoology, accounts, and more).

**Works out of the box — no API key required.** A built-in engine drives guided flows
from the knowledge base. With an Anthropic API key, an adaptive Claude engine takes
over, grounded in the same knowledge base.

## Safety

The assistant refuses requests to bypass security, disable monitoring, hack Wi-Fi,
access accounts without permission, or work around school/district policy, and it warns
users not to enter passwords, student IDs, SSNs, grades, medical, or other private data.

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

### Production configuration (Streamlit Cloud → App settings → Secrets)

```toml
# Persistent database (C1) — create a free Supabase project, copy the
# connection string from Project Settings > Database ("URI" format).
# Without this, the app uses local SQLite (wiped on redeploy).
DATABASE_URL = "postgresql://postgres:...@db.xxxx.supabase.co:5432/postgres"

# Real ticket dispatch via email (C2). Without SMTP config, tickets are
# stored + downloadable and the UI says dispatch isn't configured.
SMTP_HOST = "smtp.gmail.com"        # or smtp.sendgrid.net etc.
SMTP_PORT = "587"
SMTP_USER = "helpdesk-bot@district.org"
SMTP_PASS = "app-password-or-api-key"
SERVICE_DESK_EMAIL = "helpdesk@district.org"
CC_REQUESTER = "false"              # "true" to copy users on their tickets

# Admin access (C4). Prefer the SHA-256 form; generate with:
#   python -c "import hashlib;print(hashlib.sha256(b'YourCode').hexdigest())"
IT_ASSISTANT_ADMIN_CODE_SHA256 = "…hex…"

# Optional adaptive AI engine
ANTHROPIC_API_KEY = "sk-ant-…"
```

Abuse limits (C5) are on by default: 60 messages/session, 1,000-char inputs,
1.5 s cooldown (override via `IT_ASSISTANT_MAX_MESSAGES` etc.). Admin sign-in
locks after 5 failed attempts and every attempt is audit-logged.

## Key features

- **Personalized intake** — name, email, role, campus, room, device, category, and a
  required data-sensitivity question, with a privacy notice before anything is collected.
- **Knowledge-base-driven diagnostics** — `knowledge_base.py` organizes troubleshooting
  by product → issue → symptoms. Both engines identify the product, match symptoms to
  the closest entry, ask a targeted follow-up when confidence is low, present only the
  next best step, and adapt to answers. Adding knowledge = appending an entry.
- **Guided steps** — every step card shows what to do / why it matters / expected result,
  with buttons: It worked · Still not working · I need help with this step, plus an
  optional "Show me how" visual (accessible SVG + alt text + video placeholder).
- **Safety** — privacy notices, sensitive-data warnings, security issues fast-escalate
  to Security Operations with no user self-remediation.
- **Escalation & smart routing** — stops when steps are exhausted, admin rights are
  needed, security risk, multiple users, or testing/instruction impact; recommends
  assignment group, category, priority (Low→Urgent), risk, and explains why.
- **Ticket preview** — edit, copy, download, submit, start over; stored in SQLite.
- **Accessibility** — WCAG-friendly palettes, high contrast, text scaling, reduce
  motion, keyboard focus outlines, screen-reader labels, simple-language mode,
  read-aloud (browser TTS), and voice input (browser speech recognition, modular).
- **Spanish support** — full UI + flows in respectful, parent-friendly Spanish;
  switchable mid-conversation. Tickets are always generated in English for technicians.
- **Feedback & improvement loop** — post-resolution star ratings stored in SQLite;
  Improvement Dashboard (tickets prevented, common issues, failed steps, routing
  accuracy signals, time saved) and an Admin Review Queue where AI-suggested
  improvements require explicit approval — nothing changes in production automatically.

## Structure

| File | Purpose |
|---|---|
| `app.py` | Orchestration: intake, chat, feedback, ticket actions, layout |
| `knowledge_base.py` | Structured KB (product/issue/symptom) + scored retrieval |
| `demo_engine.py` | Offline KB-driven engine + offline ticket builder |
| `engine.py` | Claude engine (KB-grounded, structured turns via forced tool use) |
| `ticket.py` | AI ticket generation + plain-text export |
| `storage.py` | SQLite: tickets, sessions, feedback, suggestions + analytics |
| `admin.py` | Improvement Dashboard, Ticket History, Review Queue |
| `ui.py` | Theming, accessibility, components, voice widgets |
| `visuals.py` | Accessible SVG step diagrams |
| `strings.py` | English/Spanish UI strings |
| `config.py` | Branding, taxonomy, campuses, roles, priorities |

## Customization

- Branding/campuses/taxonomy: `config.py`
- Add troubleshooting knowledge: append an entry in `knowledge_base.py`
- Add step visuals: `visuals.py`
- Real ITSM submission: replace the simulated submit in `app.py` with your platform's
  API (e.g., ServiceNow Table API) — the ticket dict maps directly.
## License

Copyright © 2026 Quinton Bomer.

Current versions of this project are licensed under the GNU Affero
General Public License v3.0.

Versions published before July 9, 2026 may remain available under the
license terms that applied when they were released.
