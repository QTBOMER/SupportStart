"""Application configuration and enterprise reference data."""

import os

# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------
# This is a personal portfolio PROTOTYPE. Not an official system for any real
# district. Keep all branding clearly demo/portfolio and avoid any real
# organization's name, logo, or wording.
APP_NAME = "SupportStart"
APP_BADGE = "Demo"                       # shown next to the name so it's clearly a prototype
ORG_NAME = "Portfolio prototype. Not an official district system"
ORG_SHORT = "S"
SERVICE_DESK_PHONE = "your local IT help desk"

# ---------------------------------------------------------------------------
# Model / admin
# ---------------------------------------------------------------------------
MODEL = os.environ.get("IT_ASSISTANT_MODEL", "claude-sonnet-4-5")
MAX_TOKENS = 2048
TICKET_MAX_TOKENS = 4096
ADMIN_CODE = os.environ.get("IT_ASSISTANT_ADMIN_CODE", "admin123")
DB_PATH = os.environ.get("IT_ASSISTANT_DB", "support_data.db")

# ---------------------------------------------------------------------------
# Abuse / cost limits (C5)
# ---------------------------------------------------------------------------
MAX_MESSAGES = int(os.environ.get("IT_ASSISTANT_MAX_MESSAGES", "60"))
MAX_INPUT_CHARS = int(os.environ.get("IT_ASSISTANT_MAX_INPUT_CHARS", "1000"))
COOLDOWN_SECONDS = float(os.environ.get("IT_ASSISTANT_COOLDOWN_SECONDS", "1.5"))
MAX_CONTEXT_MESSAGES = 40   # cap conversation context sent to the AI engine
MAX_ATTACHMENTS = 3
MAX_ATTACHMENT_MB = 5

# ---------------------------------------------------------------------------
# Routing reference data
# ---------------------------------------------------------------------------
ASSIGNMENT_GROUPS = [
    "Desktop Support",
    "Network Services",
    "Identity & Access Management",
    "Application Support",
    "Device Management",
    "Security Operations",
    "Audio Visual / Smartboard Support",
    "Printer Support",
    "Parent Portal Support",
    "Student Systems Support",
    "Telecommunications",
    "Facilities Technology",
]

# Issue categories: key -> (English label, Spanish label)
CATEGORY_LABELS = {
    "password_login": ("Password & login", "Contraseña e inicio de sesión"),
    "wifi": ("Wi-Fi & network", "Wi-Fi y red"),
    "chromebook": ("Chromebook problem", "Problema con Chromebook"),
    "windows": ("Windows laptop problem", "Problema con laptop Windows"),
    "smartboard": ("Smartboard issue", "Problema con pizarra digital"),
    "projector_av": ("Projector / audio-video", "Proyector / audio y video"),
    "printer": ("Printer issue", "Problema de impresora"),
    "email": ("Outlook / email", "Outlook / correo electrónico"),
    "software": ("Software install or access", "Instalación o acceso a software"),
    "parent_portal": ("Parent portal", "Portal para padres"),
    "student_account": ("Student account", "Cuenta de estudiante"),
    "device_checkout": ("Device checkout / assignment", "Préstamo o asignación de equipo"),
    "testing": ("Testing platform", "Plataforma de exámenes"),
    "browser": ("Browser issue", "Problema del navegador"),
    "mfa": ("MFA / authentication", "MFA / autenticación"),
    "shared_drive": ("Shared drive / file access", "Unidad compartida / acceso a archivos"),
    "security": ("Security concern / suspicious email", "Seguridad / correo sospechoso"),
    "other": ("Something else", "Otro problema"),
}

# Ticket taxonomy (category -> subcategories)
CATEGORIES = {
    "Hardware": ["Laptop / Desktop", "Chromebook / Tablet", "Printer / Scanner", "Peripherals", "Interactive Display"],
    "Network": ["Wi-Fi", "Wired Network", "VPN / Remote Access", "Internet Filtering"],
    "Accounts & Access": ["Password Reset", "Account Lockout", "MFA / SSO", "Permissions / Roles"],
    "Software": ["District Application", "Instructional Software", "Operating System", "Email / Collaboration"],
    "Security": ["Phishing / Suspicious Email", "Malware", "Data Incident"],
    "Facilities & AV": ["Classroom AV", "Phones / Intercom", "Bell / PA System"],
}

PRIORITIES = {
    "Urgent": ("Outage or safety/testing impact at a school site", "Interrupción o impacto en seguridad/exámenes en una escuela"),
    "High": ("User cannot work or teach; no workaround", "El usuario no puede trabajar o enseñar; sin alternativa"),
    "Medium": ("Degraded but a workaround exists", "Funciona parcialmente; existe una alternativa"),
    "Low": ("Minor inconvenience or request", "Inconveniente menor o solicitud"),
}

RISK_LEVELS = ["Low", "Medium", "High"]

ROLES = {
    "staff": ("Teacher", "Maestro/a"),
    "student": ("Student", "Estudiante"),
    "parent": ("Parent / Guardian", "Padre / Tutor"),
    "admin": ("Administrator", "Administrador"),
    "technician": ("Technician", "Técnico"),
    "other": ("Other", "Otro"),
}

DEVICE_TYPES = {
    "chromebook": ("Chromebook", "Chromebook"),
    "windows": ("Windows laptop/desktop", "Laptop/computadora Windows"),
    "mac": ("Mac", "Mac"),
    "ipad_tablet": ("iPad / tablet", "iPad / tableta"),
    "phone": ("Phone", "Teléfono"),
    "smartboard": ("Smartboard / display", "Pizarra digital / pantalla"),
    "printer": ("Printer / copier", "Impresora / copiadora"),
    "other": ("Other / not sure", "Otro / no estoy seguro"),
}

DATA_TYPES = {
    "none": ("No sensitive data", "Sin datos confidenciales"),
    "student_device": ("Student device/account issue", "Problema con equipo/cuenta de estudiante"),
    "staff_account": ("Staff account issue", "Problema con cuenta del personal"),
    "parent_portal": ("Parent portal issue", "Problema con el portal para padres"),
    "instructional": ("Instructional software", "Software educativo"),
    "sis": ("Student information system", "Sistema de información estudiantil"),
    "unsure": ("Unsure", "No estoy seguro"),
}

SENSITIVE_DATA_TYPES = {"student_device", "staff_account", "parent_portal", "sis", "unsure"}

# NOTE: Location is now a free-text question (no preset school buttons), so no
# real or example school names are hardcoded or shown anywhere in the app.
# These lists are intentionally empty and kept only for backward compatibility.
SCHOOL_SITES: list[str] = []
CAMPUSES: list[str] = []

IMPACT_AREAS = {
    "instruction": ("Instruction / teaching", "Instrucción / enseñanza"),
    "testing": ("State or district testing", "Exámenes estatales o del distrito"),
    "attendance": ("Attendance", "Asistencia"),
    "payroll": ("Payroll / business office", "Nómina / oficina administrativa"),
    "safety": ("Safety systems", "Sistemas de seguridad"),
    "parent_access": ("Parent access", "Acceso de padres"),
    "none": ("None of these", "Ninguno de estos"),
}

PHASES = {
    "intake": ("Gathering information", "Recopilando información"),
    "diagnosis": ("Diagnosing issue", "Diagnosticando el problema"),
    "troubleshooting": ("Guided troubleshooting", "Solución guiada"),
    "resolved": ("Resolved", "Resuelto"),
    "escalation_offer": ("Support summary available", "Resumen de soporte disponible"),
}
