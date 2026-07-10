"""Ticket-time identity intake (issue-first flow).

The conversation opens with the user's PROBLEM (handled by the engine). Identity
details are collected here only when a support-ready summary is actually needed. Users whose issues are resolved never fill anything out.

Location is a single FREE-TEXT question (no preset school buttons). Whatever the
user types is parsed into school_site / building_number / room_number /
location_notes, best-effort. Respectful language throughout.

Pure logic (no Streamlit) so it is unit-testable. app.py drives it via
next_step(), prompt(), quick_replies(), process(), progress(), finalize().
"""

import re

import config

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SKIP_WORDS = {"skip", "omitir", "none", "ninguno", "n/a", "na"}
UNSURE_WORDS = {"not sure", "unsure", "no sé", "no se", "idk", "dunno"}
OFFSITE_WORDS = {"off-site", "off site", "offsite", "remote", "home", "a distancia", "en casa", "remoto"}

STEPS = ["name", "email", "role", "location", "device"]

# Categories that inherently involve student/parent/account data. The
# sensitivity flag is inferred from these instead of asking a question.
SENSITIVE_CATEGORIES = {"parent_portal", "student_account", "testing", "security",
                        "password_login", "mfa", "shared_drive"}

PROMPTS = {
    "name": {
        "en": "Before I put together a support-ready summary, I need a few quick details so IT "
              "can reach you. First, may I have your name?",
        "es": "Antes de preparar un resumen listo para soporte, necesito unos datos rápidos para "
              "que TI pueda contactarle. Primero, ¿me podría decir su nombre?",
    },
    "email": {
        "en": "Thank you, {name}! What's the best email address to reach you?",
        "es": "¡Gracias, {name}! ¿Cuál es el mejor correo electrónico para contactarle?",
    },
    "role": {
        "en": "What best describes you?",
        "es": "¿Qué opción le describe mejor?",
    },
    "location": {
        "en": "What school site or location are you at today? Please include the building number "
              "and room number if you know it. (You can also type Skip, Not sure, or Off-site.)",
        "es": "¿En qué escuela o ubicación se encuentra hoy? Incluya el número de edificio y de "
              "salón si los sabe. (También puede escribir Omitir, No estoy seguro o A distancia.)",
    },
    "device": {
        "en": "Last one. What type of device is this about?",
        "es": "Última pregunta. ¿sobre qué tipo de equipo es el problema?",
    },
}

ERRORS = {
    "name": {
        "en": "I'm sorry, I didn't catch that. What should I call you?",
        "es": "Disculpe, no entendí. ¿cómo le puedo llamar?",
    },
    "email": {
        "en": "That email doesn't look quite right. Could you type it again? (e.g., name@example.org)",
        "es": "Ese correo no parece válido. ¿podría escribirlo de nuevo? (ej.: nombre@ejemplo.org)",
    },
}

SKIP_LABEL = {"en": "Skip", "es": "Omitir"}
NOTSURE_LABEL = {"en": "Not sure", "es": "No estoy seguro"}
OFFSITE_LABEL = {"en": "Off-site", "es": "A distancia"}


def _li(lang: str) -> int:
    return 0 if lang == "en" else 1


def next_step(data: dict) -> str | None:
    for step in STEPS:
        # 'location' is satisfied once we've stored the parsed location fields
        if step == "location":
            if "location_done" not in data:
                return "location"
            continue
        if step not in data:
            return step
    return None


def progress(data: dict) -> tuple[int, int]:
    total = len(STEPS)
    done = 0
    for step in STEPS:
        if step == "location":
            done += 1 if "location_done" in data else 0
        else:
            done += 1 if step in data else 0
    return min(done + 1, total), total


def prompt(step: str, lang: str, data: dict) -> str:
    p = PROMPTS[step][lang]
    if "{name}" in p:
        first = (data.get("name") or "").split()[0] if data.get("name") else ""
        p = p.format(name=first)
        p = p.replace("Thank you, !", "Thank you!").replace("¡Gracias, !", "¡Gracias!")
    return p


def quick_replies(step: str, lang: str) -> list[str]:
    i = _li(lang)
    if step == "role":
        return [v[i] for v in config.ROLES.values()]
    if step == "location":
        # Convenience only. NOT preset school names. Everything else is free text.
        return [SKIP_LABEL[lang], NOTSURE_LABEL[lang], OFFSITE_LABEL[lang]]
    if step == "device":
        return [v[i] for v in config.DEVICE_TYPES.values()]
    return []


def _lookup(table: dict, text: str, default: str) -> str:
    t = text.strip().lower()
    for key, labels in table.items():
        for lbl in labels:
            if t == lbl.lower():
                return key
    for key, labels in table.items():
        for lbl in labels:
            if lbl.lower() in t or t in lbl.lower():
                return key
    return default


def parse_location(text: str) -> dict:
    """Best-effort parse of a free-text location into structured fields.

    Examples:
      'Jefferson High School, Building 2, Room 204'
        -> school_site='Jefferson High School', building_number='2', room_number='204'
      'Main office, Room 12' -> location_notes='Main office', room_number='12'
      'Library' -> location_notes='Library'
      'Not sure' / 'Off-site' / 'Skip' -> stored in location_notes accordingly
    """
    raw = text.strip()
    low = raw.lower()
    out = {"school_site": "", "building_number": "", "room_number": "", "location_notes": ""}

    if low in SKIP_WORDS or low in (SKIP_LABEL["en"].lower(), SKIP_LABEL["es"].lower()):
        out["location_notes"] = "Not provided"
        return out
    if low in UNSURE_WORDS or low in (NOTSURE_LABEL["en"].lower(), NOTSURE_LABEL["es"].lower()):
        out["location_notes"] = "Not sure"
        return out
    if any(w in low for w in OFFSITE_WORDS):
        out["location_notes"] = "Off-site / remote"
        return out

    # Pull out building and room numbers wherever they appear.
    m_room = re.search(r"(?:room|rm|salón|salon)\s*#?\s*([0-9]{1,5}[a-z]?)", low)
    if m_room:
        out["room_number"] = m_room.group(1)
    m_bldg = re.search(r"(?:building|bldg|bld|edificio|building no\.?)\s*#?\s*([0-9a-z]{1,4})", low)
    if m_bldg:
        out["building_number"] = m_bldg.group(1)

    # The first comma-separated chunk that isn't a building/room is the site/place.
    parts = [p.strip() for p in re.split(r"[,;]", raw) if p.strip()]
    for p in parts:
        pl = p.lower()
        if re.match(r"(room|rm|salón|salon|building|bldg|bld|edificio)\b", pl):
            continue
        if re.fullmatch(r"[#0-9a-z\.\- ]{1,6}", pl):  # bare number fragment
            continue
        if re.search(r"\b(school|elementary|middle|high|academy|escuela|prepa|colegio)\b", pl):
            out["school_site"] = p
        else:
            out["location_notes"] = (out["location_notes"] + "; " + p).strip("; ") if out["location_notes"] else p
        break
    if not out["school_site"] and not out["location_notes"]:
        out["location_notes"] = raw
    return out


def process(step: str, text: str, lang: str) -> tuple[bool, dict, str]:
    t = text.strip()
    if step == "name":
        if len(t) < 2 or "@" in t:
            return False, {}, ERRORS["name"][lang]
        return True, {"name": t.title() if t.islower() else t}, ""
    if step == "email":
        if not EMAIL_RE.match(t):
            return False, {}, ERRORS["email"][lang]
        return True, {"email": t.lower()}, ""
    if step == "role":
        key = _lookup(config.ROLES, t, "other")
        return True, {"role": config.ROLES[key][0]}, ""
    if step == "location":
        loc = parse_location(t)
        # Canonical fields for the ticket, plus the structured pieces for session state.
        campus = loc["school_site"] or loc["location_notes"] or "Not provided"
        return True, {
            "location_done": True,
            "school_site": loc["school_site"],
            "building_number": loc["building_number"],
            "room_number": loc["room_number"],
            "location_notes": loc["location_notes"],
            # legacy keys used by the ticket builder
            "campus": campus,
            "building": loc["building_number"],
            "room": loc["room_number"] or (loc["location_notes"] if not loc["school_site"] else ""),
        }, ""
    if step == "device":
        key = _lookup(config.DEVICE_TYPES, t, "other")
        return True, {"device": config.DEVICE_TYPES[key][0]}, ""
    return True, {}, ""


def finalize(data: dict, category: str = "other") -> dict:
    """Complete intake dict; sensitivity inferred from category."""
    return {
        "name": data.get("name", ""), "email": data.get("email", ""),
        "role": data.get("role", config.ROLES["other"][0]),
        "campus": data.get("campus", "Not provided"),
        "building": data.get("building", ""), "room": data.get("room", ""),
        "school_site": data.get("school_site", ""),
        "building_number": data.get("building_number", ""),
        "room_number": data.get("room_number", ""),
        "location_notes": data.get("location_notes", ""),
        "device": data.get("device", config.DEVICE_TYPES["other"][0]),
        "category": category,
        "data_type": "Inferred from issue category",
        "sensitive": category in SENSITIVE_CATEGORIES,
    }
