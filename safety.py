"""Centralized safety checks: disallowed (bypass/hack/unauthorized) requests
and sensitive-data (PII) detection.

Both engines and the app use these so behavior is consistent. The user-facing
wording lives in strings.py (boundary_reply, pii_warning)."""

import re

# ---------------------------------------------------------------------------
# Disallowed requests — bypassing security, monitoring, filters, device
# management, or accessing accounts/networks without authorization.
# Refuse cleanly; never provide partial instructions.
# ---------------------------------------------------------------------------
_MON = r"(goguardian|securly|lightspeed|bark|gaggle|content filter|web filter|filtering|" \
       r"monitoring|mdm|device management|firewall|antivirus|proxy|content blocker)"

DISALLOWED = re.compile(
    r"("
    r"\bhack(ing|ed)?\b"
    r"|\bbypass(ing)?\b|\bunblock\b|\bun-?block\b|\bget(ting)? around\b|\bwork(ing)? around\b"
    r"|\bcircumvent\b|\bevade\b|\bavoid(ing)?\b"
    r"|\bjailbreak\b|\bunenroll\b|\bun-?enroll\b|\bfactory reset to remove\b"
    r"|\b(disable|turn off|remove|uninstall|get rid of|shut off|stop)\b[^.?!]{0,30}" + _MON +
    r"|\b(around|past|through)\b[^.?!]{0,20}" + _MON +
    r"|\bproxy (site|server|website)\b|\bvpn\b[^.?!]{0,20}(school|district|filter|block|monitor)"
    r"|\b(another|someone|somebody|other|a) (student'?s?|teacher'?s?|user'?s?|staff|person'?s?|else'?s?)\b"
    r"[^.?!]{0,25}\b(account|password|login|log in|email|credentials?)\b"
    r"|\b(access|get into|log ?in to|reset|open|use)\b[^.?!]{0,40}\b(account|password|email)\b"
    r"[^.?!]{0,25}\b(without permission|not mine|isn'?t mine|another|someone else)\b"
    r"|\b(without|no) (permission|authorization|consent)\b"
    r"|\bhack (the )?(school|district|campus)?\s*(wi-?fi|wifi|network|internet)\b"
    r"|\b(disable|turn off|avoid|get past|beat|defeat|trick)\b[^.?!]{0,25}\b(security|monitoring|restriction|admin)\b"
    r")",
    re.IGNORECASE,
)

# Spanish coverage (common phrasings)
DISALLOWED_ES = re.compile(
    r"(hacke|piratear|desbloquear|evadir|saltar(se)?|burlar|quitar (el )?(filtro|goguardian|monitoreo|antivirus)|"
    r"desactivar (el )?(filtro|monitoreo|antivirus|seguridad)|"
    r"cuenta de otr[oa]|contraseña de otr[oa]|sin permiso|sin autorización|"
    r"acceder a (la )?cuenta de|red del distrito)",
    re.IGNORECASE,
)


def is_disallowed(text: str) -> bool:
    return bool(DISALLOWED.search(text or "") or DISALLOWED_ES.search(text or ""))


# ---------------------------------------------------------------------------
# Sensitive personal data (PII). Warn and pause; do not store the raw text.
# High-signal only, to avoid false alarms on ordinary troubleshooting text.
# ---------------------------------------------------------------------------
_PII_PATTERNS = [
    re.compile(r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b"),                 # SSN 123-45-6789
    re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),                 # phone 213-555-0100
    re.compile(r"\(\d{3}\)\s?\d{3}[-.\s]?\d{4}"),                     # (213) 555-0100
    re.compile(r"\b(student|employee|staff)\s*(id|number|#)\s*[:#]?\s*\d{3,}\b", re.I),
    re.compile(r"\b(my )?(password|passcode|pin)\s*(is|:|=)\s*\S+", re.I),
    re.compile(r"\b(ssn|social security)\b", re.I),
    re.compile(r"\b(iep|504 plan)\b", re.I),
    re.compile(r"\b(date of birth|d\.?o\.?b\.?|birthdate|born on)\b", re.I),
    re.compile(r"\b(grade[s]?\s+(of|for|are|is)|gpa is|failing grade|report card)\b", re.I),
    re.compile(r"\b(discipline record|suspension|expulsion|behavior incident)\b", re.I),
    re.compile(r"\b(medical|diagnosis|medication|health record|prescription)\b", re.I),
    re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),                 # a date like 03/14/2011 (DOB-ish)
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),   # email address
]


def has_pii(text: str) -> bool:
    t = text or ""
    return any(p.search(t) for p in _PII_PATTERNS)
