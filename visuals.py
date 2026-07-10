"""Visual guidance assets for troubleshooting steps.

Each visual: accessible inline SVG diagram + alt text + captions (en/es).
Steps reference visuals by id; the UI renders them inside an optional
"Show me how" expander with a text alternative and a video placeholder,
so the chat stays clean. New visuals/videos can be added here without
touching engine or UI code.
"""

_SVG_STYLE = 'font-family:sans-serif;'


def _frame(inner: str, w=520, h=200, label="") -> str:
    return (
        f'<svg role="img" aria-label="{label}" viewBox="0 0 {w} {h}" width="100%" '
        f'xmlns="http://www.w3.org/2000/svg" style="{_SVG_STYLE}max-width:{w}px;">{inner}</svg>'
    )


VISUALS = {
    "wifi_icon": {
        "alt": {
            "en": "Diagram showing where the Wi-Fi icon appears: bottom-right corner near the clock on Windows, and top-right or bottom-right corner on Chromebook and Mac. The icon looks like curved signal bars.",
            "es": "Diagrama que muestra dónde aparece el ícono de Wi-Fi: esquina inferior derecha cerca del reloj en Windows, y esquina superior o inferior derecha en Chromebook y Mac. El ícono parece barras de señal curvas.",
        },
        "caption": {"en": "Where to find the Wi-Fi icon", "es": "Dónde encontrar el ícono de Wi-Fi"},
        "svg": _frame(
            '<rect x="10" y="20" width="150" height="100" rx="8" fill="#e8effd" stroke="#1d4ed8"/>'
            '<rect x="10" y="104" width="150" height="16" rx="4" fill="#c7d7f7"/>'
            '<circle cx="146" cy="112" r="7" fill="#1d4ed8"/>'
            '<text x="85" y="70" text-anchor="middle" font-size="13" fill="#1a2332">Windows</text>'
            '<text x="85" y="150" text-anchor="middle" font-size="12" fill="#5b6b82">Bottom-right, near clock</text>'
            '<rect x="190" y="20" width="150" height="100" rx="8" fill="#e8effd" stroke="#1d4ed8"/>'
            '<rect x="190" y="104" width="150" height="16" rx="4" fill="#c7d7f7"/>'
            '<circle cx="326" cy="112" r="7" fill="#1d4ed8"/>'
            '<text x="265" y="70" text-anchor="middle" font-size="13" fill="#1a2332">Chromebook</text>'
            '<text x="265" y="150" text-anchor="middle" font-size="12" fill="#5b6b82">Bottom-right shelf</text>'
            '<rect x="370" y="20" width="150" height="100" rx="8" fill="#e8effd" stroke="#1d4ed8"/>'
            '<rect x="370" y="20" width="150" height="16" rx="4" fill="#c7d7f7"/>'
            '<circle cx="506" cy="28" r="7" fill="#1d4ed8"/>'
            '<text x="445" y="75" text-anchor="middle" font-size="13" fill="#1a2332">Mac</text>'
            '<text x="445" y="150" text-anchor="middle" font-size="12" fill="#5b6b82">Top-right menu bar</text>',
            w=540, h=165, label="Wi-Fi icon locations on Windows, Chromebook, and Mac",
        ),
    },
    "caps_lock": {
        "alt": {
            "en": "Diagram of a keyboard highlighting the Caps Lock key on the left side, above the Shift key. Many keyboards show a small light when Caps Lock is on.",
            "es": "Diagrama de un teclado que resalta la tecla Bloq Mayús en el lado izquierdo, arriba de la tecla Shift. Muchos teclados muestran una pequeña luz cuando Bloq Mayús está activado.",
        },
        "caption": {"en": "Finding the Caps Lock key", "es": "Cómo encontrar la tecla Bloq Mayús"},
        "svg": _frame(
            '<rect x="10" y="20" width="500" height="120" rx="10" fill="#f4f6fa" stroke="#94a3b8"/>'
            '<rect x="25" y="60" width="88" height="28" rx="5" fill="#1d4ed8"/>'
            '<text x="69" y="79" text-anchor="middle" font-size="12" fill="#ffffff">Caps Lock</text>'
            '<circle cx="105" cy="66" r="3" fill="#34d399"/>'
            '<rect x="25" y="94" width="110" height="28" rx="5" fill="#e2e8f0" stroke="#94a3b8"/>'
            '<text x="80" y="113" text-anchor="middle" font-size="12" fill="#1a2332">Shift</text>'
            '<rect x="130" y="60" width="360" height="28" rx="5" fill="#e2e8f0" stroke="#94a3b8"/>'
            '<rect x="150" y="94" width="340" height="28" rx="5" fill="#e2e8f0" stroke="#94a3b8"/>'
            '<text x="260" y="165" text-anchor="middle" font-size="12" fill="#5b6b82">Left side of keyboard — green light means Caps Lock is ON</text>',
            w=520, h=175, label="Keyboard diagram highlighting the Caps Lock key",
        ),
    },
    "hdmi_source": {
        "alt": {
            "en": "Diagram of a display remote and panel showing the Input or Source button, and a menu listing HDMI-1, HDMI-2, and VGA. Select the input your computer is plugged into, usually HDMI-1.",
            "es": "Diagrama de un control remoto y panel que muestra el botón Entrada o Fuente, y un menú con HDMI-1, HDMI-2 y VGA. Seleccione la entrada donde está conectada su computadora, normalmente HDMI-1.",
        },
        "caption": {"en": "Choosing the correct input source", "es": "Cómo elegir la fuente de entrada correcta"},
        "svg": _frame(
            '<rect x="20" y="20" width="120" height="150" rx="14" fill="#f4f6fa" stroke="#94a3b8"/>'
            '<rect x="40" y="40" width="80" height="26" rx="6" fill="#1d4ed8"/>'
            '<text x="80" y="58" text-anchor="middle" font-size="11" fill="#fff">INPUT</text>'
            '<circle cx="60" cy="95" r="10" fill="#e2e8f0"/><circle cx="100" cy="95" r="10" fill="#e2e8f0"/>'
            '<circle cx="60" cy="125" r="10" fill="#e2e8f0"/><circle cx="100" cy="125" r="10" fill="#e2e8f0"/>'
            '<text x="80" y="190" text-anchor="middle" font-size="11" fill="#5b6b82">Remote</text>'
            '<rect x="200" y="30" width="290" height="120" rx="8" fill="#e8effd" stroke="#1d4ed8"/>'
            '<rect x="220" y="48" width="250" height="24" rx="4" fill="#1d4ed8"/>'
            '<text x="345" y="65" text-anchor="middle" font-size="12" fill="#fff">HDMI-1  ✓  (your computer)</text>'
            '<rect x="220" y="80" width="250" height="24" rx="4" fill="#ffffff" stroke="#c7d7f7"/>'
            '<text x="345" y="97" text-anchor="middle" font-size="12" fill="#1a2332">HDMI-2</text>'
            '<rect x="220" y="112" width="250" height="24" rx="4" fill="#ffffff" stroke="#c7d7f7"/>'
            '<text x="345" y="129" text-anchor="middle" font-size="12" fill="#1a2332">VGA</text>'
            '<text x="345" y="190" text-anchor="middle" font-size="11" fill="#5b6b82">Input menu on the display</text>',
            w=520, h=205, label="Input source selection on a display remote and menu",
        ),
    },
    "printer_panel": {
        "alt": {
            "en": "Diagram of a printer control panel. A Ready light means the printer is working. A blinking orange light or an error message on the small screen means paper jam, low toner, or another fault.",
            "es": "Diagrama del panel de control de una impresora. Una luz de Lista significa que funciona. Una luz naranja parpadeante o un mensaje de error en la pantalla pequeña significa atasco de papel, poco tóner u otra falla.",
        },
        "caption": {"en": "Reading the printer panel", "es": "Cómo leer el panel de la impresora"},
        "svg": _frame(
            '<rect x="30" y="30" width="460" height="110" rx="12" fill="#f4f6fa" stroke="#94a3b8"/>'
            '<rect x="50" y="50" width="200" height="60" rx="6" fill="#1a2332"/>'
            '<text x="150" y="85" text-anchor="middle" font-size="13" fill="#34d399">READY</text>'
            '<circle cx="300" cy="80" r="12" fill="#34d399"/>'
            '<text x="300" y="115" text-anchor="middle" font-size="10" fill="#5b6b82">Ready</text>'
            '<circle cx="360" cy="80" r="12" fill="#fbbf24"/>'
            '<text x="360" y="115" text-anchor="middle" font-size="10" fill="#5b6b82">Attention</text>'
            '<circle cx="420" cy="80" r="12" fill="#f87171"/>'
            '<text x="420" y="115" text-anchor="middle" font-size="10" fill="#5b6b82">Error</text>'
            '<text x="260" y="165" text-anchor="middle" font-size="12" fill="#5b6b82">Green = OK · Orange/red = check screen message (jam, toner, tray)</text>',
            w=520, h=180, label="Printer control panel status lights",
        ),
    },
    "browser_refresh": {
        "alt": {
            "en": "Diagram of a browser window showing the three-dot menu in the top-right corner. Choose 'New Incognito window' or press Ctrl+Shift+N together to open a private window.",
            "es": "Diagrama de una ventana del navegador que muestra el menú de tres puntos en la esquina superior derecha. Elija 'Nueva ventana de incógnito' o presione Ctrl+Shift+N juntas para abrir una ventana privada.",
        },
        "caption": {"en": "Opening a private / incognito window", "es": "Cómo abrir una ventana privada / de incógnito"},
        "svg": _frame(
            '<rect x="20" y="20" width="480" height="130" rx="10" fill="#f4f6fa" stroke="#94a3b8"/>'
            '<rect x="20" y="20" width="480" height="34" rx="10" fill="#e2e8f0"/>'
            '<circle cx="472" cy="37" r="3" fill="#1a2332"/><circle cx="472" cy="45" r="3" fill="#1a2332"/>'
            '<circle cx="472" cy="29" r="3" fill="#1a2332"/>'
            '<rect x="300" y="58" width="185" height="28" rx="5" fill="#1d4ed8"/>'
            '<text x="392" y="77" text-anchor="middle" font-size="11" fill="#fff">New Incognito window</text>'
            '<rect x="300" y="92" width="185" height="24" rx="5" fill="#ffffff" stroke="#c7d7f7"/>'
            '<text x="392" y="108" text-anchor="middle" font-size="11" fill="#1a2332">Ctrl + Shift + N</text>'
            '<text x="150" y="100" text-anchor="middle" font-size="12" fill="#5b6b82">Click the ⋮ menu →</text>'
            '<text x="260" y="172" text-anchor="middle" font-size="12" fill="#5b6b82">Top-right corner of the browser</text>',
            w=520, h=185, label="Browser menu showing how to open an incognito window",
        ),
    },
}


VISUALS["chromebook_keys"] = {
    "alt": {
        "en": "Diagram of a Chromebook top row showing the circular Refresh key (4th from the left) "
              "and the Power button at the far right. Hold Refresh and tap Power to restart.",
        "es": "Diagrama de la fila superior de un Chromebook que muestra la tecla Actualizar circular "
              "(4.ª desde la izquierda) y el botón de encendido a la derecha. Mantenga Actualizar y "
              "toque Encendido para reiniciar.",
    },
    "caption": {"en": "Refresh + Power to restart a Chromebook", "es": "Actualizar + Encendido para reiniciar"},
    "svg": _frame(
        '<rect x="10" y="30" width="500" height="60" rx="10" fill="#f4f6fa" stroke="#94a3b8"/>'
        + "".join(f'<rect x="{22 + i*44}" y="45" width="34" height="30" rx="5" '
                  f'fill="{"#1d4ed8" if i == 3 else "#e2e8f0"}" stroke="#94a3b8"/>'
                  for i in range(10))
        + '<text x="171" y="66" text-anchor="middle" font-size="15" fill="#fff">⟳</text>'
        '<rect x="462" y="45" width="34" height="30" rx="5" fill="#1a2332"/>'
        '<text x="479" y="65" text-anchor="middle" font-size="13" fill="#fff">⏻</text>'
        '<text x="171" y="108" text-anchor="middle" font-size="11" fill="#1d4ed8" font-weight="700">Refresh</text>'
        '<text x="479" y="108" text-anchor="middle" font-size="11" fill="#5b6b82" font-weight="700">Power</text>'
        '<text x="260" y="135" text-anchor="middle" font-size="12" fill="#5b6b82">Hold Refresh, tap Power, keep holding until it restarts</text>',
        w=540, h=150, label="Chromebook Refresh and Power keys"),
}

VISUALS["audio_picker"] = {
    "alt": {
        "en": "Diagram of the speaker icon near the clock. Click it, make sure volume is up and not "
              "muted, then click the arrow to pick the correct output device (headphones or speakers).",
        "es": "Diagrama del ícono de bocina cerca del reloj. Haga clic, verifique que el volumen esté "
              "alto y sin silenciar, luego haga clic en la flecha para elegir el dispositivo correcto.",
    },
    "caption": {"en": "Volume and choosing the audio device", "es": "Volumen y elección del dispositivo de audio"},
    "svg": _frame(
        '<rect x="20" y="24" width="180" height="150" rx="12" fill="#f4f6fa" stroke="#94a3b8"/>'
        '<text x="52" y="66" font-size="22" fill="#1d4ed8">🔊</text>'
        '<rect x="80" y="52" width="100" height="10" rx="5" fill="#c7d7f7"/>'
        '<rect x="80" y="52" width="66" height="10" rx="5" fill="#1d4ed8"/>'
        '<circle cx="146" cy="57" r="8" fill="#1d4ed8"/>'
        '<text x="110" y="100" text-anchor="middle" font-size="11" fill="#5b6b82">Volume up, not muted</text>'
        '<text x="110" y="150" text-anchor="middle" font-size="24" fill="#1a2332">⌃</text>'
        '<text x="110" y="168" text-anchor="middle" font-size="10" fill="#5b6b82">click arrow →</text>'
        '<rect x="240" y="40" width="270" height="120" rx="8" fill="#e8effd" stroke="#1d4ed8"/>'
        '<rect x="258" y="56" width="234" height="26" rx="4" fill="#1d4ed8"/>'
        '<text x="375" y="74" text-anchor="middle" font-size="12" fill="#fff">✓ Headphones (your device)</text>'
        '<rect x="258" y="90" width="234" height="26" rx="4" fill="#ffffff" stroke="#c7d7f7"/>'
        '<text x="375" y="108" text-anchor="middle" font-size="12" fill="#1a2332">Room speakers</text>'
        '<rect x="258" y="124" width="234" height="26" rx="4" fill="#ffffff" stroke="#c7d7f7"/>'
        '<text x="375" y="142" text-anchor="middle" font-size="12" fill="#1a2332">Monitor speakers</text>',
        w=540, h=190, label="Volume control and audio output device picker"),
}


def get_visual(visual_id: str) -> dict | None:
    return VISUALS.get(visual_id)
