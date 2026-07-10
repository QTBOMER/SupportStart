"""Built-in bilingual diagnostic engine. No API key required.

Consumes the structured knowledge base (knowledge_base.py) rather than
hardcoded flows:

1. Identifies the product from intake hints + the user's description.
2. Matches symptoms to the closest KB entry (scored retrieval).
3. Asks a targeted disambiguation question when confidence is low.
4. Presents only the next best step, one at a time.
5. Adapts to responses: It worked -> resolved; I need help -> re-explain
   the same step; Still not working -> advance; multi-user/impact answers
   raise priority; security matches fast-escalate.

The app keeps the state dict in session_state; next_turn returns (Turn, state).
"""

import re
from datetime import datetime

import config
import knowledge_base as kb
import safety
from engine import Turn
from strings import L, tr

WORKED = re.compile(r"\b(it worked|worked|funcion[oó]|fixed|resolved|solved|resuelto|arreglado|working now|connected now|ya funciona)\b", re.I)

# District policy boundary: requests to bypass protections are refused politely
# and converted into a proper review request (never self-remediation).
BYPASS = re.compile(
    r"\b(bypass|unblock|un-block|get around|circumvent|jailbreak|"
    r"disable (the )?(filter|monitoring|goguardian|securly|lightspeed|management|mdm|antivirus|firewall)|"
    r"remove (the )?(mdm|management|restriction)|unenroll|un-enroll|"
    r"proxy (site|server)|vpn to|"
    r"(someone|somebody) else'?s (account|password)|another (user|student|person)'?s (account|password)|"
    r"desbloquear|evadir|saltar(se)? el filtro|quitar (el )?filtro|"
    r"cuenta de otra persona|contraseña de otra persona)\b", re.I)
HELP = re.compile(r"\b(need help|help with this step|necesito ayuda|no s[eé] c[oó]mo|don'?t know how|stuck|how do i)\b", re.I)
MULTI = re.compile(r"\b(others too|otros tambi[eé]n|multiple|everyone|todos|whole class|toda la clase)\b", re.I)
NEGATIVE = re.compile(r"\b(still|sigue|not|no)\b", re.I)

GENERIC_HELP = kb.B(
    "No problem. Let's slow down. Read the card again one line at a time, and only do the "
    "'What to do' part. If you can't find a button or menu it mentions, tell me what you see "
    "on your screen instead, or choose 'Still not working' and we'll move on. You won't break anything.",
    "No hay problema. Vamos más despacio. Lea la tarjeta de nuevo línea por línea y haga solo "
    "la parte de 'Qué hacer'. Si no encuentra un botón o menú, dígame qué ve en su pantalla, o "
    "elija 'Sigue sin funcionar' y continuamos. No dañará nada.",
)

DESCRIBE_Q = kb.B("In one or two sentences, what's happening?",
                  "En una o dos oraciones, ¿qué está pasando?")
DISAMBIG_Q = kb.B("To make sure I use the right fix, which of these best matches your situation?",
                  "Para usar la solución correcta, ¿cuál de estas opciones describe mejor su situación?")
DEVICE_Q = kb.B("Got it. What type of device or system is this about?",
                "Entendido. ¿Sobre qué tipo de equipo o sistema es esto?")
SCOPE_Q = kb.B("One quick check: is this affecting just you, or are others affected too?",
               "Una verificación rápida: ¿esto le afecta solo a usted o también a otras personas?")
SCOPE_QUICK = [kb.B("Just me", "Solo yo"), kb.B("Others too", "Otros también"), kb.B("Not sure", "No estoy seguro")]

PRIORITY_ORDER = ["Low", "Medium", "High", "Urgent"]

# Device inference: keyword -> device_type label (matches config.DEVICE_TYPES values)
DEVICE_KEYWORDS = {
    "chromebook": "Chromebook",
    "macbook": "Mac", "imac": "Mac", " mac ": "Mac", "mac ": "Mac", "macos": "Mac",
    "windows": "Windows laptop/desktop", "pc ": "Windows laptop/desktop", "laptop": "Windows laptop/desktop",
    "desktop": "Windows laptop/desktop",
    "ipad": "iPad / tablet", "tablet": "iPad / tablet",
    "smartboard": "Smartboard / display", "smart board": "Smartboard / display",
    "interactive display": "Smartboard / display", "promethean": "Smartboard / display",
    "projector": "Smartboard / display",
    "printer": "Printer / copier", "copier": "Printer / copier",
    "phone": "Phone",
}
# KB entries whose issue is device-dependent. Only these prompt for device type.
DEVICE_RELEVANT_CATEGORIES = {"Hardware", "Network", "Facilities & AV"}


def bump(priority: str, levels: int = 1) -> str:
    i = min(PRIORITY_ORDER.index(priority) + levels, len(PRIORITY_ORDER) - 1)
    return PRIORITY_ORDER[i]


def _blank_memory() -> dict:
    """The session's remembered answers. The assistant checks this before asking."""
    return {
        "issue_summary": None,
        "device_type": None,
        "user_type": None,
        "user_name": None,
        "user_email": None,
        "school_site": None,
        "building_room": None,
        "software_or_system": None,
        "error_message": None,
        "troubleshooting_steps_given": [],
        "troubleshooting_steps_attempted": [],
        "resolved_status": None,      # None | True | False
        "escalation_needed": False,
    }


def new_state(category: str) -> dict:
    return {"category": category if category in config.CATEGORY_LABELS else "other",
            "entry_id": None, "candidates": [], "stage": "describe", "idx": 0,
            "answers": {}, "multiuser": False, "impact": "",
            "failed_steps": [], "done": False,
            "memory": _blank_memory(), "asked_device": False,
            "pending_prefix": ""}


def infer_device(text: str, intake: dict | None = None) -> str | None:
    """Infer a device_type from the user's words or the intake profile."""
    if intake and intake.get("device") and intake["device"] != config.DEVICE_TYPES["other"][0]:
        return intake["device"]
    t = f" {text.lower()} "
    for kw, dev in DEVICE_KEYWORDS.items():
        if kw in t:
            return dev
    return None


def _device_relevant(entry: dict | None) -> bool:
    if not entry:
        return False
    return entry["routing"]["category"] in DEVICE_RELEVANT_CATEGORIES


def _entry(state: dict) -> dict | None:
    return kb.BY_ID.get(state["entry_id"]) if state["entry_id"] else None


def _total(state: dict) -> int:
    e = _entry(state)
    if not e:
        return 6
    dev = 1 if state.get("asked_device") else 0
    base = 1 + dev + len(e["questions"]) + len(e["steps"]) + 1  # describe (+device) + nodes + wrap-up
    return base + (0 if e.get("security_fast") else 1)          # + scope (no impact question)


def _pos(state: dict) -> int:
    e = _entry(state)
    stage, idx = state["stage"], state["idx"]
    dev = 1 if state.get("asked_device") else 0
    if stage in ("describe", "disambiguate", "device") or not e:
        return 1 + (0 if stage != "device" else dev)
    if stage == "questions":
        return 2 + dev + idx
    if stage == "steps":
        return 2 + dev + len(e["questions"]) + idx
    if stage == "scope":
        return 2 + dev + len(e["questions"]) + len(e["steps"])
    return _total(state)


class DemoEngine:
    """Stateful, KB-driven, bilingual guided-flow engine. No network, no key."""

    # ------------------------------------------------------------- entry
    def first_turn(self, state: dict, intake: dict, lang: str) -> Turn:
        """Issue-first opener: invite the problem description immediately."""
        name = (intake.get("name") or "").split()[0] if intake.get("name") else ""
        greet = {
            "en": (f"Hi{', ' + name if name else ''}! I'm your AI support assistant. "
                   "Tell me what's wrong in a sentence or two, and we'll try to fix it "
                   "together. If we can't, I'll write a clear summary you can send to IT."),
            "es": (f"¡Hola{', ' + name if name else ''}! Soy su asistente de soporte con "
                   "inteligencia artificial. Cuénteme qué pasa en una o dos oraciones y lo "
                   "intentamos arreglar juntos. Si no podemos, escribiré un resumen claro que "
                   "puede enviar a TI."),
        }[lang]
        return Turn(
            reply=greet,
            phase="intake",
            status_label={"en": "Listening", "es": "Escuchando"}[lang],
            issue_summary="",
            progress_current=1, progress_total=_total(state),
            est_minutes_remaining=8, confidence=60, quick_replies=[],
            log_entries=[],
        )

    # ------------------------------------------------------------- turns
    def next_turn(self, state: dict, user_text: str, intake: dict, lang: str) -> tuple[Turn, dict]:
        # District policy boundary. Checked before anything else, at any stage.
        if safety.is_disallowed(user_text):
            return self._boundary_turn(state, user_text, lang), state
        stage = state["stage"]
        log = []

        mem = state["memory"]

        if stage == "describe":
            log.append({"kind": "info_collected", "detail": f"Issue description: {user_text}"})
            mem["issue_summary"] = user_text
            # Infer and remember the device from the user's own words (no re-asking).
            dev = infer_device(user_text, intake)
            if dev:
                mem["device_type"] = dev
                log.append({"kind": "finding", "detail": f"Inferred device type: {dev}"})
            entry, candidates, conf = kb.select_entry(
                user_text, state["category"], mem.get("device_type") or (intake or {}).get("device"))
            if entry is None:
                state["candidates"] = [c["id"] for c in candidates]
                state["stage"] = "disambiguate"
                log.append({"kind": "finding",
                            "detail": "Low-confidence KB match. Asking user to disambiguate among: "
                                      + ", ".join(state["candidates"])})
                quick = [tr(kb.BY_ID[cid]["issue"], lang) for cid in state["candidates"]]
                return self._q_turn(tr(DISAMBIG_Q, lang), quick,
                                    {"en": "Narrowing it down", "es": "Acotando el problema"}[lang],
                                    state, lang, log, confidence=40), state
            self._select(state, entry, log)
            mem["software_or_system"] = entry["product"]
            return self._after_match(state, intake, lang, log), state

        if stage == "device":
            dev = self._match_device(user_text)
            mem["device_type"] = dev
            log.append({"kind": "info_collected", "detail": f"Device type: {dev}"})
            return self._serve_current(state, intake, lang, log), state

        if stage == "disambiguate":
            log.append({"kind": "info_collected", "detail": f"User clarified issue as: {user_text}"})
            entry = self._match_candidate(state, user_text)
            if entry is None:
                # No confident match. Do NOT pivot to an unrelated flow.
                # Go straight to offering a summary with everything collected so far.
                fallback = kb.BY_ID["general_it"]
                if state["category"] not in (None, "other"):
                    fallback = next((e for e in kb.ENTRIES if state["category"] in e["categories"]),
                                    kb.BY_ID["general_it"])
                state["entry_id"] = fallback["id"]
                state["done"] = True
                log.append({"kind": "finding",
                            "detail": "Clarification did not match a known troubleshooting flow, "
                                      "escalating directly instead of guessing."})
                reason = ("The reported issue could not be confidently matched to a self-service "
                          "fix; routed directly to a technician with the collected details.")
                reply = {
                    "en": "I don't want to guess and walk you through steps that don't fit your "
                          "situation. Instead, let me put together ticket-ready information, "
                          "details you can copy into your official support request so IT can help "
                          "you directly with everything you've told me so far.",
                    "es": "No quiero adivinar y guiarle por pasos que no correspondan a su "
                          "situación. Mejor permítame preparar la información lista para su "
                          "solicitud de soporte. Detalles que puede copiar para que TI le ayude "
                          "directamente con todo lo que me ha dado.",
                }[lang]
                log.append({"kind": "escalation_reason", "detail": reason})
                state["memory"]["escalation_needed"] = True
                turn = Turn(reply=reply, phase="escalation_offer",
                            status_label={"en": "Support summary available", "es": "Resumen disponible"}[lang],
                            issue_summary=tr(fallback["issue"], lang),
                            progress_current=_total(state), progress_total=_total(state),
                            est_minutes_remaining=2, confidence=10, quick_replies=[],
                            log_entries=log, escalation_reason=reason)
                return turn, state
            self._select(state, entry, log)
            mem["software_or_system"] = entry["product"]
            return self._after_match(state, intake, lang, log), state

        entry = _entry(state) or kb.BY_ID["general_it"]

        if stage == "questions":
            node = entry["questions"][state["idx"]]
            log.append({"kind": "info_collected", "detail": f"{node['label']}: {user_text}"})
            if "error" in node["label"].lower() and user_text.strip().lower() not in (
                    "none", "ninguno", "no", "n/a", ""):
                mem["error_message"] = user_text
            state["idx"] += 1
            return self._serve_current(state, intake, lang, log), state

        if stage == "steps":
            step = entry["steps"][state["idx"]]
            title = tr(step["title"], "en")
            if HELP.search(user_text):
                log.append({"kind": "finding", "detail": f"User needed help with step: {title}"})
                state["failed_steps"].append(title)
                help_text = tr(step.get("help", GENERIC_HELP), lang)
                return self._step_turn(step, state, lang, log, prefix=help_text), state
            log.append({"kind": "step_attempted", "detail": title})
            log.append({"kind": "step_result", "detail": user_text})
            mem["troubleshooting_steps_attempted"].append({"step": title, "result": user_text})
            if WORKED.search(user_text) and not NEGATIVE.search(user_text):
                log.append({"kind": "finding", "detail": "Issue confirmed resolved by user."})
                mem["resolved_status"] = True
                state["done"] = True
                return self._resolved_turn(entry, intake, lang, log, resolving_step=title), state
            state["failed_steps"].append(title)
            state["idx"] += 1
            return self._serve_current(state, intake, lang, log), state

        if stage == "scope":
            state["answers"]["scope"] = user_text
            log.append({"kind": "info_collected", "detail": f"Scope of impact: {user_text}"})
            if MULTI.search(user_text):
                state["multiuser"] = True
                log.append({"kind": "finding",
                            "detail": "Multiple users affected. Escalation threshold met."})
            mem["resolved_status"] = False
            mem["escalation_needed"] = True
            state["done"] = True
            return self._escalation_turn(entry, state, lang, log), state

        # done / overflow. Repeat escalation offer politely
        return self._escalation_turn(entry, state, lang, log), state

    # ----------------------------------------------------------- helpers
    def _select(self, state: dict, entry: dict, log: list):
        state["entry_id"] = entry["id"]
        state["stage"] = "questions" if entry["questions"] else "steps"
        state["idx"] = 0
        log.append({"kind": "finding",
                    "detail": f"Matched knowledge base entry '{entry['id']}' (product: {entry['product']})."})

    def _restate(self, entry: dict, lang: str) -> str:
        """One-line plain-language confirmation of the problem, shown once."""
        phrase = tr(entry["restate"], lang) if entry.get("restate") else tr(entry["issue"], lang).lower()
        return {"en": f"Got it, {phrase}.", "es": f"Entendido, {phrase}."}[lang]

    def _after_match(self, state: dict, intake: dict, lang: str, log: list) -> Turn:
        """After matching: restate the problem, then ask device ONLY when the entry
        has no targeted question of its own and the device is genuinely unknown."""
        entry = _entry(state)
        mem = state["memory"]
        # Plain-language restatement is queued to lead the next message (every issue).
        state["pending_prefix"] = self._restate(entry, lang)
        needs_device = (mem.get("device_type") is None and not state.get("asked_device")
                        and _device_relevant(entry) and not entry["questions"])
        if needs_device:
            state["asked_device"] = True
            state["stage"] = "device"
            quick = [v[0 if lang == "en" else 1] for v in config.DEVICE_TYPES.values()]
            return self._q_turn(tr(DEVICE_Q, lang), quick,
                                {"en": "Identifying device", "es": "Identificando equipo"}[lang],
                                state, lang, log)
        return self._serve_current(state, intake, lang, log)

    def _match_device(self, user_text: str) -> str:
        t = user_text.strip().lower()
        for key, labels in config.DEVICE_TYPES.items():
            for lbl in labels:
                if t == lbl.lower() or lbl.lower() in t:
                    return config.DEVICE_TYPES[key][0]
        dev = infer_device(user_text)
        return dev or config.DEVICE_TYPES["other"][0]

    def _answer_in_description(self, node: dict, desc: str) -> str | None:
        """If the user's original description clearly answers this diagnostic
        question, return that answer. Conservative: only auto-answer when the
        full option phrase appears, or a single distinctive one-word option
        matches. This deliberately still asks nuanced questions (e.g. black vs
        dim vs external monitor) rather than guessing from one shared word."""
        if not desc:
            return None
        d = f" {desc.lower()} "
        for opt in node.get("quick", []):
            en = tr(opt, "en").lower().strip()
            if f" {en} " in d:                      # exact option phrase present
                return tr(opt, "en")
            words = [w for w in re.findall(r"[a-z']+", en) if len(w) > 3]
            if len(words) == 1 and f" {words[0]} " in d:   # single distinctive keyword
                return tr(opt, "en")
        return None

    def _match_candidate(self, state: dict, user_text: str) -> dict:
        text = user_text.lower()
        best, best_score = None, -1.0
        for cid in state["candidates"]:
            e = kb.BY_ID[cid]
            score = 0.0
            for probe in (tr(e["issue"], "en").lower(), tr(e["issue"], "es").lower(), e["product"].lower()):
                if probe == text or probe in text:
                    score += 5.0
            score += sum(2.0 for kw in e["symptoms"] if kb.kw_in(text, kw))
            if score > best_score:  # ties keep earlier (higher-ranked) candidate
                best, best_score = e, score
        return best if best_score > 0 else None  # None -> caller escalates, never guesses

    def _serve_current(self, state: dict, intake: dict, lang: str, log: list) -> Turn:
        entry = _entry(state) or kb.BY_ID["general_it"]
        mem = state["memory"]
        if state["stage"] == "questions":
            # Skip any diagnostic question the user already answered in their description.
            while state["idx"] < len(entry["questions"]):
                node = entry["questions"][state["idx"]]
                known = self._answer_in_description(node, mem.get("issue_summary") or "")
                if known:
                    log.append({"kind": "info_collected",
                                "detail": f"{node['label']}: {known} (from initial description)"})
                    state["idx"] += 1
                    continue
                return self._q_turn(tr(node["q"], lang), [tr(q, lang) for q in node.get("quick", [])],
                                    tr(node["status"], lang), state, lang, log)
            state["stage"], state["idx"] = "steps", 0
        if state["stage"] == "steps":
            if state["idx"] < len(entry["steps"]):
                return self._step_turn(entry["steps"][state["idx"]], state, lang, log)
            if entry.get("security_fast"):
                mem["escalation_needed"] = True
                state["done"] = True
                return self._escalation_turn(entry, state, lang, log)
            state["stage"] = "scope"
        if state["stage"] == "scope":
            return self._q_turn(tr(SCOPE_Q, lang), [tr(q, lang) for q in SCOPE_QUICK],
                                {"en": "Checking who's affected", "es": "Verificando a quién afecta"}[lang],
                                state, lang, log)
        mem["escalation_needed"] = True
        state["done"] = True
        return self._escalation_turn(entry, state, lang, log)

    def _base(self, state: dict, lang: str) -> dict:
        entry = _entry(state)
        return {
            "issue_summary": tr(entry["issue"], lang) if entry else "",
            "progress_current": _pos(state), "progress_total": _total(state),
            "est_minutes_remaining": max((_total(state) - _pos(state)) * 2, 1),
        }

    def _q_turn(self, question: str, quick: list, status: str, state, lang, log,
                confidence: int | None = None) -> Turn:
        b = self._base(state, lang)
        prefix = state.get("pending_prefix") or ""
        if prefix:
            question = f"{prefix}\n\n{question}"
            state["pending_prefix"] = ""
        return Turn(reply=question, phase="diagnosis" if state["stage"] != "describe" else "intake",
                    status_label=status, quick_replies=quick, log_entries=log,
                    confidence=confidence if confidence is not None else max(70 - _pos(state) * 5, 30), **b)

    STEP_INTROS = {
        "en": ["Let's try this first.", "Okay, let's try this.", "Here's the next thing to try.",
               "Let's give this a go.", "Next, let's try this."],
        "es": ["Probemos esto primero.", "Bien, intentemos esto.", "Aquí está lo siguiente que probar.",
               "Vamos a intentar esto.", "Ahora, probemos esto."],
    }

    def _step_turn(self, step: dict, state, lang, log, prefix: str = "") -> Turn:
        b = self._base(state, lang)
        s = {"title": tr(step["title"], lang), "what": tr(step["what"], lang),
             "why": tr(step["why"], lang), "expected": tr(step["expected"], lang),
             "difficulty": step["difficulty"], "visual": step.get("visual")}
        given = state["memory"]["troubleshooting_steps_given"]
        if not prefix:
            intro = self.STEP_INTROS[lang][len(given) % len(self.STEP_INTROS[lang])]
            # Naturally confirm the inferred device on the first step, if we have it.
            dev = state["memory"].get("device_type")
            if not given and dev and dev != config.DEVICE_TYPES["other"][0]:
                intro = ({"en": f"Since this is a {dev}, ", "es": f"Como es un {dev}, "}[lang]
                         + intro[0].lower() + intro[1:])
            prefix = intro
        # A queued restatement leads the message on the first step (if no question preceded it).
        queued = state.get("pending_prefix") or ""
        if queued:
            prefix = f"{queued} {prefix}"
            state["pending_prefix"] = ""
        title_en = tr(step["title"], "en")
        if title_en not in given:
            given.append(title_en)
        return Turn(
            reply=prefix,
            phase="troubleshooting",
            status_label={"en": "Trying safe fixes", "es": "Probando soluciones seguras"}[lang],
            step=s,
            quick_replies=[L("it_worked", lang), L("still_not_working", lang), L("need_help_step", lang)],
            confidence=max(65 - _pos(state) * 5, 25), log_entries=log, **b)

    def _resolved_turn(self, entry, intake, lang, log, resolving_step: str = "") -> Turn:
        name = (intake.get("name") or "").split()[0] if intake.get("name") else ""
        reply = {
            "en": f"Excellent{', ' + name if name else ''}. Glad that fixed it! No ticket needed. "
                  "If it comes back, start a new session any time.",
            "es": f"Excelente{', ' + name if name else ''}. ¡me alegra que se haya arreglado! "
                  "No se necesita ticket. Si vuelve a ocurrir, inicie una nueva sesión cuando quiera.",
        }[lang]
        if resolving_step:
            log = log + [{"kind": "finding", "detail": f"Resolved by step: {resolving_step}"}]
        return Turn(reply=reply, phase="resolved",
                    status_label={"en": "Resolved", "es": "Resuelto"}[lang],
                    issue_summary=tr(entry["issue"], lang),
                    progress_current=1, progress_total=1,
                    est_minutes_remaining=0, confidence=95, quick_replies=[], log_entries=log)

    def _boundary_turn(self, state: dict, user_text: str, lang: str) -> Turn:
        """Polite refusal + safe alternative for bypass/restriction requests."""
        state["entry_id"] = "restricted_request"
        state["done"] = True
        reason = ("User requested help circumventing a district protection (filter, monitoring, "
                  "device management, or account access). Refused per policy; converted to a "
                  "restriction-review request for the responsible team.")
        log = [
            {"kind": "finding",
             "detail": f"Policy boundary triggered by request: {user_text[:200]}"},
            {"kind": "escalation_reason", "detail": reason},
        ]
        return Turn(
            reply=L("boundary_reply", lang),
            phase="escalation_offer",
            status_label={"en": "Policy review", "es": "Revisión de política"}[lang],
            issue_summary=tr(kb.BY_ID["restricted_request"]["issue"], lang),
            progress_current=_total(state), progress_total=_total(state),
            est_minutes_remaining=2, confidence=10, quick_replies=[],
            log_entries=log, escalation_reason=reason)

    def _escalation_turn(self, entry, state, lang, log) -> Turn:
        reason_en = tr(entry["esc_reason"], "en")
        reply = {
            "en": f"{tr(entry['esc_reason'], lang)} I can put together a support-ready summary "
                  "with everything we've covered. Details you can copy into your official "
                  "support request so IT has a clear starting point.",
            "es": f"{tr(entry['esc_reason'], lang)} Puedo preparar un resumen listo para soporte "
                  "con todo lo que revisamos. Detalles que puede copiar en su solicitud oficial "
                  "para que TI tenga un punto de partida claro.",
        }[lang]
        if entry.get("esc_extra"):
            reply += "\n\n" + tr(entry["esc_extra"], lang)
        log = log + [{"kind": "escalation_reason", "detail": reason_en}]
        state["memory"]["escalation_needed"] = True
        return Turn(reply=reply, phase="escalation_offer",
                    status_label={"en": "Support summary available", "es": "Resumen disponible"}[lang],
                    issue_summary=tr(entry["issue"], lang),
                    progress_current=_total(state), progress_total=_total(state),
                    est_minutes_remaining=2, confidence=15, quick_replies=[],
                    log_entries=log, escalation_reason=reason_en)


# ---------------------------------------------------------------------------
# Offline ticket generation (from KB routing + session log + intake)
# ---------------------------------------------------------------------------
def demo_ticket(intake: dict, log: list[dict], state: dict, reason: str, lang: str) -> dict:
    entry = kb.BY_ID.get(state.get("entry_id") or "general_it", kb.BY_ID["general_it"])
    r = entry["routing"]

    info = [e["detail"] for e in log if e["kind"] == "info_collected"]
    steps, results = [], []
    for e in log:
        if e["kind"] == "step_attempted":
            steps.append(e["detail"])
            results.append("Not recorded")
        elif e["kind"] == "step_result" and results:
            results[-1] = e["detail"]
    performed = [{"step": s, "result": x} for s, x in zip(steps, results)] or \
                [{"step": "Guided intake only", "result": "No troubleshooting steps before escalation"}]

    # Priority: base from KB, raised by inferred operational impact + scope.
    priority = r["priority"]
    issue_text = (state.get("memory", {}).get("issue_summary") or "").lower()
    if any(k in issue_text for k in ("testing", "test ", "exam", "safety", "security", "outage")):
        priority = "Urgent"
    elif any(k in issue_text for k in ("class", "teach", "instruction", "lesson", "attendance",
                                       "clase", "enseñ", "asistencia")):
        priority = bump(priority)
    if state.get("multiuser"):
        priority = bump(priority)

    scope = state.get("answers", {}).get("scope", "Not provided")
    impact_txt = (f"Scope: {scope}. "
                  f"{'Multiple users affected.' if state.get('multiuser') else 'Single user affected.'}")
    location = ", ".join(x for x in [intake.get("campus"), intake.get("building"), intake.get("room")] if x) \
               or "Not provided"
    errors = [d.split(":", 1)[1].strip() for d in info
              if "error" in d.split(":", 1)[0].lower()
              and d.split(":", 1)[1].strip().lower() not in ("none", "ninguno", "no", "n/a", "")]

    description = (
        f"Reported by {intake.get('name', 'user')} ({intake.get('role', 'unknown role')}) at {location}. "
        f"Device: {intake.get('device', 'Not provided')}. Product: {entry['product']}. "
        + ("Information collected: " + "; ".join(info) + ". " if info else "")
        + f"Escalated because: {reason}"
    )

    return {
        "title": f"{tr(entry['issue'], 'en')}, {intake.get('campus', '')}".rstrip(","),
        "executive_summary": (
            f"{tr(entry['issue'], 'en')} affecting {'multiple users' if state.get('multiuser') else 'one user'} "
            f"at {intake.get('campus', 'unknown site')}. Guided self-service troubleshooting completed "
            f"without resolution; technician action required."
        ),
        "detailed_description": description,
        "symptoms": info or [tr(entry["issue"], "en")],
        "environment": f"District-managed environment. KB entry: {entry['id']}. "
                       f"Session language: {'Spanish' if lang == 'es' else 'English'}. "
                       f"Data sensitivity: {intake.get('data_type', 'unknown')}.",
        "device_information": intake.get("device", "Not provided"),
        "user_location": location,
        "user_name": intake.get("name", "Not provided"),
        "user_email": intake.get("email", "Not provided"),
        "user_role": intake.get("role", "Not provided"),
        "applications_involved": [entry["product"]],
        "error_messages": errors or ["None reported"],
        "business_impact": impact_txt,
        "impact": impact_txt,
        "troubleshooting_performed": performed,
        "assignment_group": r["group"],
        "assignment_rationale": tr(r["rationale"], "en"),
        "category": r["category"],
        "subcategory": r["sub"],
        "priority": priority,
        "priority_rationale": (f"Base priority {r['priority']} raised to {priority} due to scope/operational impact."
                               if priority != r["priority"]
                               else config.PRIORITIES.get(priority, ("Standard priority.",))[0]),
        "risk_level": r["risk"],
        "suggested_resolution_path": tr(r["path"], "en"),
        "confidence_score": 78,
        "estimated_technician_effort": r["effort"],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ticket_ref": "DRAFT-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
    }
