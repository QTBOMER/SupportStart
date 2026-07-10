"""Bilingual UI strings (English / Español).

Usage:  from strings import L; L("submit_ticket", lang)
Content dicts elsewhere use {"en": ..., "es": ...}; tr() picks the language.
"""

STRINGS = {
    # --- App chrome ---
    "tagline": {
        "en": "A portfolio project exploring guided troubleshooting and support-ready summaries.",
        "es": "Un proyecto de portafolio sobre solución guiada y resúmenes listos para soporte.",
    },
    "prototype_title": {"en": "Prototype notice", "es": "Aviso de prototipo"},
    "prototype_notice": {
        "en": "This is a personal prototype built for learning and portfolio demonstration. "
              "It is not an official system for any school or district, and it does not submit "
              "real tickets. Please don't enter passwords, student records, or other sensitive "
              "information.",
        "es": "Este es un prototipo personal creado para aprendizaje y demostración de portafolio. "
              "No es un sistema oficial de ninguna escuela o distrito, y no envía tickets reales. "
              "Por favor, no escriba contraseñas, expedientes de estudiantes ni información "
              "confidencial.",
    },
    "mode_support": {"en": "User Demo", "es": "Demo de usuario"},
    "mode_admin": {"en": "Demo IT Staff View", "es": "Vista de personal de TI (demo)"},
    "language": {"en": "Language", "es": "Idioma"},
    "dark_theme": {"en": "Dark theme", "es": "Tema oscuro"},
    "urgent_help": {
        "en": "This is a demo. For a real, urgent problem, contact {phone}.",
        "es": "Esto es una demostración. Para un problema real y urgente, contacte a {phone}.",
    },

    # --- Accessibility menu ---
    "a11y_title": {"en": "Accessibility", "es": "Accesibilidad"},
    "a11y_text_size": {"en": "Text size", "es": "Tamaño del texto"},
    "a11y_size_normal": {"en": "Normal", "es": "Normal"},
    "a11y_size_large": {"en": "Large", "es": "Grande"},
    "a11y_size_xlarge": {"en": "Extra large", "es": "Muy grande"},
    "a11y_high_contrast": {"en": "High contrast", "es": "Alto contraste"},
    "a11y_reduce_motion": {"en": "Reduce motion", "es": "Reducir animaciones"},
    "a11y_read_aloud": {"en": "Read responses aloud", "es": "Leer respuestas en voz alta"},
    "a11y_voice_input": {"en": "Voice input", "es": "Entrada por voz"},
    "a11y_simple": {"en": "Simple instructions mode", "es": "Modo de instrucciones simples"},
    "listen": {"en": "Listen", "es": "Escuchar"},
    "mic_hint": {
        "en": "Tap the microphone, speak, then copy the text into the message box.",
        "es": "Toque el micrófono, hable y luego copie el texto en el cuadro de mensaje.",
    },
    "mic_unsupported": {
        "en": "Voice input isn't supported in this browser yet.",
        "es": "La entrada por voz aún no es compatible con este navegador.",
    },

    # --- Welcome / landing ---
    "welcome_title": {
        "en": "Tell me what's wrong, and we'll try to fix it together.",
        "es": "Cuénteme qué pasa y lo intentamos arreglar juntos.",
    },
    "welcome_sub": {
        "en": "I'll walk you through a few easy steps first. Most problems are fixed in a few "
              "minutes. If we can't fix it, I'll write a clear summary you can copy into your "
              "support request, so you don't have to explain it twice.",
        "es": "Primero le muestro unos pasos fáciles. La mayoría de los problemas se arreglan en "
              "unos minutos. Si no podemos, escribiré un resumen claro que puede copiar en su "
              "solicitud de soporte, para que no tenga que explicarlo dos veces.",
    },
    "chip_guided": {"en": "Guided, one step at a time", "es": "Guiado, un paso a la vez"},
    "chip_noforms": {"en": "No forms to fill out", "es": "Sin formularios que llenar"},
    "chip_ticket": {"en": "Summary only if needed", "es": "Resumen solo si es necesario"},
    "chip_bilingual": {"en": "English & Español", "es": "Inglés y Español"},

    # --- Sidebar ---
    "it_staff_options": {"en": "Portfolio / IT Staff Demo", "es": "Portafolio / Demo de personal de TI"},

    # --- Safety boundaries ---
    "boundary_reply": {
        "en": "I can't help with bypassing security, disabling monitoring, hacking Wi-Fi, "
              "accessing accounts without permission, or working around school/district policy.\n\n"
              "If a restriction is blocking legitimate schoolwork, contact official IT support or "
              "ask an authorized staff member to submit a review request.",
        "es": "No puedo ayudar a evadir la seguridad, desactivar el monitoreo, hackear el Wi-Fi, "
              "acceder a cuentas sin permiso, ni saltarse las políticas de la escuela o del distrito.\n\n"
              "Si una restricción bloquea trabajo escolar legítimo, contacte al soporte de TI "
              "oficial o pida a un miembro autorizado del personal que envíe una solicitud de revisión.",
    },
    "pii_warning": {
        "en": "Please don't enter student IDs, passwords, Social Security numbers, dates of "
              "birth, grades, medical or discipline details, or other private information here. "
              "I can still help. Just describe the issue in general terms.",
        "es": "Por favor, no escriba números de identificación de estudiantes, contraseñas, "
              "números de Seguro Social, fechas de nacimiento, calificaciones, información médica "
              "o disciplinaria ni otros datos privados aquí. Igual puedo ayudarle. Solo describa "
              "el problema en términos generales.",
    },

    # --- Privacy / intake ---
    "privacy_title": {"en": "Before we begin", "es": "Antes de comenzar"},
    "privacy_notice": {
        "en": "Please don't enter any sensitive or confidential information.",
        "es": "Por favor, no escriba información confidencial ni delicada.",
    },
    "intake_title": {"en": "Tell us who you are", "es": "Díganos quién es usted"},
    "intake_intro": {
        "en": "This takes less than a minute and helps us route your issue correctly.",
        "es": "Esto toma menos de un minuto y nos ayuda a dirigir su problema correctamente.",
    },
    "field_name": {"en": "Your name", "es": "Su nombre"},
    "field_email": {"en": "Email address", "es": "Correo electrónico"},
    "field_role": {"en": "I am a…", "es": "Soy…"},
    "field_campus": {"en": "Location", "es": "Ubicación"},
    "field_building": {"en": "Building (optional)", "es": "Edificio (opcional)"},
    "field_room": {"en": "Room number or location (optional)", "es": "Número de salón o ubicación (opcional)"},
    "field_device": {"en": "Device type", "es": "Tipo de equipo"},
    "field_category": {"en": "What kind of issue is this?", "es": "¿Qué tipo de problema es?"},
    "field_data_type": {"en": "What type of data is involved?", "es": "¿Qué tipo de datos están involucrados?"},
    "start_session": {"en": "Start troubleshooting", "es": "Comenzar la solución"},
    "intake_required": {
        "en": "Please fill in your name, email, and the required selections.",
        "es": "Por favor complete su nombre, correo electrónico y las selecciones requeridas.",
    },
    "sensitive_warning": {
        "en": "This issue may involve sensitive information. Please describe the problem in "
              "general terms only. Never type passwords, grades, or personal records here. "
              "If private data is directly involved, we'll route this to the right team.",
        "es": "Este problema puede involucrar información confidencial. Describa el problema "
              "solo en términos generales; nunca escriba contraseñas, calificaciones ni "
              "expedientes personales aquí. Si hay datos privados involucrados, lo dirigiremos "
              "al equipo correcto.",
    },

    # --- Chat / session ---
    "chat_placeholder": {
        "en": "Describe your issue or answer the question above…",
        "es": "Describa su problema o responda la pregunta de arriba…",
    },
    "quick_answers": {"en": "Quick answers", "es": "Respuestas rápidas"},
    "session_status": {"en": "Session status", "es": "Estado de la sesión"},
    "current_activity": {"en": "Current activity", "es": "Actividad actual"},
    "time_remaining": {"en": "Est. time remaining", "es": "Tiempo restante estimado"},
    "confidence": {"en": "Resolution confidence", "es": "Confianza de resolución"},
    "issue_summary": {"en": "Issue summary", "es": "Resumen del problema"},
    "timeline": {"en": "Troubleshooting timeline", "es": "Cronología de la solución"},
    "step_of": {"en": "Step {a} of {b}", "es": "Paso {a} de {b}"},
    "what_to_do": {"en": "What to do", "es": "Qué hacer"},
    "why_matters": {"en": "Why this matters", "es": "Por qué es importante"},
    "expected_result": {"en": "Expected result", "es": "Resultado esperado"},
    "show_me_how": {"en": "Show me how", "es": "Muéstrame cómo"},
    "play_video": {"en": "Play video", "es": "Ver video"},
    "video_placeholder": {
        "en": "A short walkthrough video will appear here when available.",
        "es": "Aquí aparecerá un video corto cuando esté disponible.",
    },
    "it_worked": {"en": "It worked", "es": "Funcionó"},
    "still_not_working": {"en": "Still not working", "es": "Sigue sin funcionar"},
    "need_help_step": {"en": "I need help with this step", "es": "Necesito ayuda con este paso"},
    "request_technician": {"en": "Request a technician", "es": "Solicitar un técnico"},
    "start_over": {"en": "Start over", "es": "Comenzar de nuevo"},
    "keep_troubleshooting": {"en": "Keep troubleshooting", "es": "Seguir intentando"},
    "generate_ticket": {"en": "Create support-ready summary", "es": "Crear resumen listo para soporte"},
    "resolved_banner": {
        "en": "Issue resolved. No support request needed. 🎉",
        "es": "Problema resuelto. No se necesita solicitud de soporte. 🎉",
    },
    "new_session": {"en": "Start a new session", "es": "Iniciar una nueva sesión"},
    "thinking": {"en": "Analyzing your response", "es": "Analizando su respuesta"},
    "error_generic": {
        "en": "Something went wrong. Please try again.",
        "es": "Algo salió mal. Por favor intente de nuevo.",
    },

    # --- Support summary (end-user final screen) ---
    "ticket_ready": {"en": "Your support summary is ready", "es": "Su resumen de soporte está listo"},
    "ticket_review": {
        "en": "Copy or download this information and use it when creating your official support "
              "ticket. This helps save time and gives the support technician a clearer starting "
              "point. It does not submit an official ticket automatically.",
        "es": "Copie o descargue esta información y úsela al crear su ticket de soporte oficial. "
              "Esto ahorra tiempo y le da al técnico un punto de partida más claro. No envía un "
              "ticket oficial automáticamente.",
    },
    "copy_summary": {"en": "Copy summary", "es": "Copiar resumen"},
    "copy_hint": {
        "en": "Use this information when creating your support ticket. Copy or download it to "
              "save time and help support resolve the issue faster.",
        "es": "Use esta información al crear su ticket de soporte. Cópiela o descárguela para "
              "ahorrar tiempo y ayudar a resolver el problema más rápido.",
    },
    "sum_requester": {"en": "Requester", "es": "Solicitante"},
    "sum_issue": {"en": "What's happening", "es": "Qué está pasando"},
    "sum_tried": {"en": "Troubleshooting already tried", "es": "Pasos ya intentados"},
    "sum_copyready": {"en": "Copy-ready ticket text", "es": "Texto listo para copiar al ticket"},
    "edit_ticket": {"en": "Edit details", "es": "Editar detalles"},
    "download_txt": {"en": "Download .txt", "es": "Descargar .txt"},
    "save_changes": {"en": "Save changes", "es": "Guardar cambios"},
    "cancel": {"en": "Cancel", "es": "Cancelar"},
    "preparing_ticket": {"en": "Preparing your support summary…", "es": "Preparando su resumen de soporte…"},
    "ticket_panel": {"en": "Support summary", "es": "Resumen de soporte"},
    "no_ticket_yet": {
        "en": "A support summary will appear here if a technician is needed.",
        "es": "Aquí aparecerá un resumen de soporte si se necesita un técnico.",
    },
    # --- IT Staff Operations (technician-only detail) ---
    "staff_ops": {"en": "IT Staff Operations (technical triage)", "es": "Operaciones de TI (triaje técnico)"},
    "staff_ops_hint": {
        "en": "Internal routing and triage detail. Not shown on the user's summary.",
        "es": "Detalle interno de enrutamiento y triaje. No se muestra en el resumen del usuario.",
    },

    # --- Feedback ---
    "feedback_title": {"en": "How did we do?", "es": "¿Cómo lo hicimos?"},
    "fb_resolved": {"en": "Was your issue resolved?", "es": "¿Se resolvió su problema?"},
    "fb_helpful": {"en": "How helpful was the assistant?", "es": "¿Qué tan útil fue el asistente?"},
    "fb_easy": {"en": "Were the steps easy to follow?", "es": "¿Fueron fáciles de seguir los pasos?"},
    "fb_accurate": {"en": "Did the summary describe your issue accurately?", "es": "¿El resumen describió su problema con precisión?"},
    "fb_comments": {"en": "What could have been better? (optional)", "es": "¿Qué podría mejorar? (opcional)"},
    "fb_submit": {"en": "Send feedback", "es": "Enviar comentarios"},
    "fb_thanks": {"en": "Thank you. Your feedback helps us improve.", "es": "Gracias. Sus comentarios nos ayudan a mejorar."},
    "yes": {"en": "Yes", "es": "Sí"},
    "no": {"en": "No", "es": "No"},
    "partially": {"en": "Partially", "es": "Parcialmente"},
    "rate_low": {"en": "1 · Needs work", "es": "1 · A mejorar"},
    "rate_mid": {"en": "2 · Okay", "es": "2 · Aceptable"},
    "rate_high": {"en": "3 · Great", "es": "3 · Excelente"},

    # --- Limits / abuse protection ---
    "input_too_long": {
        "en": "That message is a bit long. Could you shorten it to the key details? (max {n} characters)",
        "es": "Ese mensaje es un poco largo. ¿podría acortarlo a los detalles clave? (máximo {n} caracteres)",
    },
    "limit_reached": {
        "en": "We've covered a lot this session. To make sure you get real help, let's create a "
              "support-ready summary with everything so far, or start a fresh session.",
        "es": "Hemos cubierto mucho en esta sesión. Para asegurarnos de que reciba ayuda real, "
              "preparemos un resumen listo para soporte con todo lo recopilado, o inicie una nueva sesión.",
    },
    "slow_down": {"en": "One moment…", "es": "Un momento…"},

    # --- Attachments (M7) ---
    "attach_label": {
        "en": "Add a photo of the issue (optional)",
        "es": "Agregue una foto del problema (opcional)",
    },
    "attach_hint": {
        "en": "A photo of the error or device helps the technician fix it faster. Up to {n} images, {mb} MB each.",
        "es": "Una foto del error o del equipo ayuda al técnico a resolverlo más rápido. Hasta {n} imágenes, {mb} MB cada una.",
    },

    # --- Duplicates (M6) ---
    "dup_notice": {
        "en": "Heads up: {n} similar report(s) from {campus} in the last 48 hours. Technicians "
              "may already be aware. Your ticket was still filed and linked.",
        "es": "Aviso: {n} reporte(s) similar(es) de {campus} en las últimas 48 horas. Es posible "
              "que los técnicos ya lo sepan. Su ticket se registró y se vinculó de todas formas.",
    },

    # --- Dispatch (C2) ---
    "dispatch_sent": {
        "en": "Ticket emailed to the service desk ({to}).",
        "es": "Ticket enviado por correo a la mesa de servicio ({to}).",
    },
    "dispatch_unconfigured": {
        "en": "Email dispatch isn't configured yet. The ticket is saved for the support team. "
              "You can also download it and send it yourself.",
        "es": "El envío por correo aún no está configurado. El ticket quedó guardado para el "
              "equipo de soporte. También puede descargarlo y enviarlo usted mismo.",
    },
    "dispatch_failed": {
        "en": "The email couldn't be sent, but your ticket is saved. Please download it or call "
              "the Service Desk.",
        "es": "No se pudo enviar el correo, pero su ticket quedó guardado. Descárguelo o llame a "
              "la mesa de servicio.",
    },

    # --- Admin ---
    "admin_title": {"en": "Administration", "es": "Administración"},
    "admin_code": {"en": "Demo access code", "es": "Código de acceso de demostración"},
    "demo_framing": {
        "en": "This is a portfolio demo. The IT Staff view is intentionally viewable. "
              "Demo access code: admin123. Please do not enter real district or student data.",
        "es": "Esta es una demostración de portafolio. La vista de personal de TI es visible a "
              "propósito. Código de acceso de demostración: admin123. No escriba datos reales del "
              "distrito o de estudiantes.",
    },
    "admin_denied": {"en": "Incorrect access code.", "es": "Código de acceso incorrecto."},
    "admin_dashboard": {"en": "Improvement Dashboard", "es": "Panel de mejoras"},
    "admin_tickets": {"en": "Ticket History", "es": "Historial de tickets"},
    "admin_queue": {"en": "Review Queue", "es": "Cola de revisión"},
}


def L(key: str, lang: str = "en", **kw) -> str:
    s = STRINGS.get(key, {}).get(lang) or STRINGS.get(key, {}).get("en", key)
    return s.format(**kw) if kw else s


def tr(obj, lang: str = "en"):
    """Pick a language from a {'en':..., 'es':...} dict; pass through strings."""
    if isinstance(obj, dict) and "en" in obj:
        return obj.get(lang) or obj["en"]
    return obj
