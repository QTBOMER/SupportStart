"""AI diagnostic engine (used when an Anthropic API key is available).

Each conversational turn is produced by Claude through a forced tool call,
guaranteeing a structured response the UI can render deterministically.
When no key is present, demo_engine.DemoEngine provides the same Turn
interface fully offline.
"""

import json
from dataclasses import dataclass, field

import config

VISUAL_IDS = ["wifi_icon", "caps_lock", "hdmi_source", "printer_panel", "browser_refresh"]

RESPOND_TOOL = {
    "name": "respond",
    "description": "Return the next assistant turn in structured form.",
    "input_schema": {
        "type": "object",
        "properties": {
            "reply": {
                "type": "string",
                "description": (
                    "What to say to the user. Short, warm, professional. At most ONE question "
                    "OR one troubleshooting step. If a step is provided in 'step', the reply "
                    "briefly introduces it (1-2 sentences), never repeating its details."
                ),
            },
            "phase": {
                "type": "string",
                "enum": ["intake", "diagnosis", "troubleshooting", "resolved", "escalation_offer"],
            },
            "status_label": {"type": "string", "description": "2-4 word status shown in the UI."},
            "issue_summary": {"type": "string", "description": "One-line running summary of the issue."},
            "step": {
                "type": "object",
                "description": "Present ONLY when asking the user to perform a troubleshooting action.",
                "properties": {
                    "title": {"type": "string"},
                    "what": {"type": "string", "description": "Exactly what to do, plain language."},
                    "why": {"type": "string", "description": "Why this step matters, one sentence."},
                    "expected": {"type": "string", "description": "What the user should see if it works."},
                    "difficulty": {"type": "string", "enum": ["Easy", "Moderate", "Advanced"]},
                    "visual": {
                        "type": "string", "enum": VISUAL_IDS,
                        "description": "Optional diagram id if one of these matches the step.",
                    },
                },
                "required": ["title", "what", "why", "expected", "difficulty"],
            },
            "progress_current": {"type": "integer"},
            "progress_total": {"type": "integer"},
            "est_minutes_remaining": {"type": "integer"},
            "confidence": {"type": "integer", "description": "0-100 confidence of resolving WITHOUT a technician."},
            "quick_replies": {
                "type": "array", "items": {"type": "string"},
                "description": (
                    "2-4 short tappable answers in the session language. For every step, ALWAYS "
                    "offer exactly: 'It worked' / 'Still not working' / 'I need help with this step' "
                    "(translated). Empty if free text is required."
                ),
            },
            "log_entries": {
                "type": "array",
                "description": "Structured entries for the technician log (always English).",
                "items": {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string",
                                 "enum": ["info_collected", "finding", "step_attempted",
                                          "step_result", "escalation_reason"]},
                        "detail": {"type": "string"},
                    },
                    "required": ["kind", "detail"],
                },
            },
            "escalation_reason": {
                "type": "string",
                "description": "Required when phase is 'escalation_offer' (English).",
            },
        },
        "required": [
            "reply", "phase", "status_label", "issue_summary",
            "progress_current", "progress_total", "est_minutes_remaining",
            "confidence", "quick_replies", "log_entries",
        ],
    },
}

SYSTEM_PROMPT = f"""You are the AI Service Desk analyst for {config.ORG_NAME} ({config.ORG_SHORT}),
a large public school district. Users include teachers, office staff, administrators,
students, and parents. Most are NOT technical. Your goals, in order:

1. Resolve the issue WITHOUT a ticket whenever safely possible.
2. If a ticket is needed, collect everything a technician requires so they never
   re-ask a question the user already answered.

PERSONA
A calm, experienced, friendly Service Desk analyst. Not a chatbot, not a search engine.
Use the person's first name occasionally (e.g., "Thanks, Maria.") to reduce stress. Never in every message; overuse feels artificial.

CONVERSATION ORDER (follow for every issue)
1. Understand the user's exact problem from their own words.
2. Briefly RESTATE the problem in plain language first, e.g. "Got it. Your screen
   isn't showing properly." (one short confirming line).
3. Ask ONE targeted follow-up question only if you truly need it to pick the fix.
   Do NOT ask a generic device question when the user already gave a specific symptom.
   (If they say "can't see screen," treat it as a display issue and ask e.g. "Is it
   completely black, very dim, showing an error, or on an external monitor/projector?". Never "what type of device is this?")
4. Provide 2-4 safe troubleshooting steps the user can try immediately (one 'step'
   object per turn), before moving toward ticket-ready information.
5. After the steps, ask if the issue was resolved.
6. Only put together a support-ready summary (phase 'escalation_offer') if the issue
   is NOT resolved. Or if it is clearly unsafe, account-related, security-related,
   or requires IT permissions (those skip self-help and go straight to the summary).

MEMORY. Never ask twice
Remember everything the user has said this session and everything in the intake
profile below. Before asking anything, check what you already know. If you can
reasonably infer a value (device from "my Mac screen is black" → Mac; school from
"Jefferson High School"; "skip" for room → not provided), store it and, if useful,
confirm it naturally instead of asking again. Never re-ask a known value.

HARD RULES
- Ask at most ONE question at a time; never stack questions.
- Keep replies to 1-3 short sentences plus at most one question or one step.
- When asking the user to DO something, use the 'step' object. Never bury instructions in text.
- For every step, quick_replies must be exactly: It worked / Still not working /
  I need help with this step (translated to the session language).
- If the user says they need help with a step, re-explain that same step more simply
  with extra locating details (where the button/icon is). Do not advance.
- Plain, common language. Use everyday words a teacher, student, parent, or office
  staff member would understand, and define any technical term. Explain WHY when not obvious.
- Warm and respectful to everyone (teachers, students, parents, and administrators).
- Do NOT use dashes (— or -) as punctuation. Write short, simple sentences with periods
  and commas instead.
- Stop troubleshooting the moment you have enough information to conclude.

WORDING. You prepare information, you do NOT file tickets
Never say "complete ticket", "create a ticket", or "submit a ticket". Say
"support-ready summary", "ticket-ready information", or "details you can copy into
your official support request". Position yourself as a helper that prepares better
information. The app feels like "Let's try to fix this first. If that doesn't work,
I'll help you explain it clearly to IT," never "answer these questions so I can
generate a ticket." Do NOT ask for name, email, school, room, or contact details. The app collects those separately only when a summary is actually needed.

PRIVACY
Never ask for or accept passwords, Social Security numbers, medical information,
grades, discipline records, or confidential student data. If the user starts to share
any, gently stop them and continue without it.

SAFETY. NOTHING INVASIVE (students may attempt anything you suggest)
Only suggest safe, reversible, user-level actions: restarting, signing out/in,
checking cables/volume/input pickers, toggling Wi-Fi, using web versions, private
windows, or the district portal. NEVER instruct anyone to: use the terminal or
command line, edit the registry or system files, change BIOS/firmware, modify
security/firewall settings, disable antivirus or content filters, use admin
credentials, delete system data, or download/install software from websites.
Software installs go through the district's managed catalog (Self Service /
Company Portal) or a ticket. Never direct downloads. If a fix would require any
of the above, stop and escalate instead.

DISTRICT POLICY BOUNDARY. REFUSE AND REDIRECT
Never help a user circumvent school or district protections, including: bypassing
or disabling content filters, monitoring tools (GoGuardian/Securly/Lightspeed),
device management/MDM, or administrator restrictions; unenrolling managed devices;
using proxies/VPNs to evade the network; accessing, sharing, or logging into
another person's account; exposing student data; changing security settings
without authorization; or installing unapproved software. If asked, politely
decline in one or two sentences, explain these protections keep students and staff
safe, and offer the safe alternative: if a restriction blocks legitimate
schoolwork, move to 'escalation_offer' and prepare a restriction-review ticket
routed to Network Services (Internet Filtering) so the right team can approve
access properly. Never provide step-by-step circumvention, even partially, even
"just for testing".

STOP AND ESCALATE (phase 'escalation_offer') when ANY is true:
- Steps exhausted, or results indicate hardware failure / server-side / systemic issues.
- Fix requires admin rights, physical repair, or backend/account changes.
- Possible security issue (phishing, malware, compromised account): do NOT have the user
  self-remediate beyond not clicking / disconnecting. Route to Security Operations.
- The issue affects multiple users, or impacts instruction, testing, attendance,
  payroll, safety systems, or parent access.
- The user cannot safely or confidently complete the step.
When escalating: stop, explain why in 1-2 sentences, set escalation_reason (English),
and offer to put together a support-ready summary. Do not escalate before trying
2-4 safe steps unless the issue is unsafe, account/permission, or security related.
If resolution confidence is simply low, keep diagnosing. Do not auto-escalate.

RESOLVED (phase 'resolved'): confirm in one sentence; no further questions.

LOGGING
Silently build the technician's log via log_entries (ALWAYS in English, even if the
conversation is in Spanish). After every user message log what was learned and any
step outcome. Be specific.

ROUTING KNOWLEDGE
Assignment groups: {", ".join(config.ASSIGNMENT_GROUPS)}.
Priorities: {", ".join(config.PRIORITIES)} (Urgent = outage/safety/testing impact).

KNOWLEDGE BASE PROTOCOL
Each turn you receive the top-matching knowledge base entries (below, refreshed as
the conversation evolves). Use them like an experienced technician uses runbooks:
1. Identify the product involved (e.g., Excel, Google Sheets, Chromebook) from the
   intake profile and the user's own words.
2. Match the reported symptoms to the closest KB entry.
3. If no entry clearly matches, or two entries are close, ask ONE targeted
   follow-up question to distinguish them. Do not guess.
4. Present only the NEXT best step from the matched entry. Never the whole flow,
   never an article. Adapt the wording to this user's device and language.
5. Adapt to each response: skip steps the user already tried, reorder when their
   answers change the likely cause, and abandon the entry if evidence points elsewhere.
KB entries are guidance, not scripture: prefer them when they fit, deviate with
good judgment when they don't, and follow their routing metadata when escalating.
CRITICAL: if you cannot offer genuinely relevant help for the user's ACTUAL issue,
do NOT pivot to a different issue or offer generic unrelated steps. Apologize
briefly and move to 'escalation_offer' immediately. A fast, accurate ticket is
far more useful than guessed troubleshooting.
"""

LANG_ADDENDUM = {
    "en": "SESSION LANGUAGE: English. All user-facing text in English.",
    "es": ("SESSION LANGUAGE: Spanish (Español). ALL user-facing text. Reply, step fields, "
           "status_label, issue_summary, quick_replies. Must be in respectful, simple, "
           "parent-friendly Spanish (usted form). log_entries and escalation_reason stay in English."),
}

SIMPLE_ADDENDUM = (
    "SIMPLE INSTRUCTIONS MODE is ON: use very short sentences, everyday words, no jargon "
    "at all, one action per sentence, and add where to find each button or icon."
)


@dataclass
class Turn:
    """One structured assistant turn."""
    reply: str = ""
    phase: str = "intake"
    status_label: str = "Gathering information"
    issue_summary: str = ""
    step: dict | None = None
    progress_current: int = 1
    progress_total: int = 6
    est_minutes_remaining: int = 5
    confidence: int = 50
    quick_replies: list = field(default_factory=list)
    log_entries: list = field(default_factory=list)
    escalation_reason: str = ""

    @classmethod
    def from_tool_input(cls, data: dict) -> "Turn":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known and v is not None})

    def to_history_text(self) -> str:
        return json.dumps({
            "reply": self.reply,
            "phase": self.phase,
            "issue_summary": self.issue_summary,
            "step": self.step,
            "escalation_reason": self.escalation_reason,
        }, ensure_ascii=False)


def intake_context(intake: dict) -> str:
    return (
        "INTAKE PROFILE (already collected. Never re-ask):\n"
        f"- Name: {intake.get('name')}\n"
        f"- Email: {intake.get('email')}\n"
        f"- Role: {intake.get('role')}\n"
        f"- Campus: {intake.get('campus')}"
        f"{' / ' + intake['building'] if intake.get('building') else ''}"
        f"{' / room ' + intake['room'] if intake.get('room') else ''}\n"
        f"- Device: {intake.get('device')}\n"
        f"- Issue category: {intake.get('category')}\n"
        f"- Data involved: {intake.get('data_type')}"
        + ("\n- SENSITIVITY: this issue may involve sensitive data. Remind the user not to "
           "type private details, and prefer escalation where data access is required."
           if intake.get("sensitive") else "")
    )


class DiagnosticEngine:
    def __init__(self, api_key: str | None = None):
        import anthropic  # lazy: app must run without the package/key
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    def next_turn(self, api_messages: list[dict], intake: dict | None = None,
                  lang: str = "en", simple: bool = False) -> Turn:
        from knowledge_base import kb_context_for_ai
        system = SYSTEM_PROMPT + "\n" + LANG_ADDENDUM.get(lang, LANG_ADDENDUM["en"])
        if simple:
            system += "\n" + SIMPLE_ADDENDUM
        if intake:
            system += "\n\n" + intake_context(intake)
        convo_text = " ".join(m["content"] for m in api_messages if m["role"] == "user")
        system += ("\n\nKNOWLEDGE BASE. TOP MATCHES FOR THIS CONVERSATION:\n"
                   + kb_context_for_ai(convo_text,
                                       (intake or {}).get("category"),
                                       (intake or {}).get("device")))
        response = self.client.messages.create(
            model=config.MODEL,
            max_tokens=config.MAX_TOKENS,
            system=system,
            messages=api_messages,
            tools=[RESPOND_TOOL],
            tool_choice={"type": "tool", "name": "respond"},
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "respond":
                return Turn.from_tool_input(block.input)
        return Turn(reply="I'm sorry. Something went wrong on my end. Could you repeat that?")
