"""
Sostituisce le 21 emoji usate come icona dei parametri (🎨🔬🎭⚽...)
con icone SVG coerenti, disegnate apposta: stesso stile a linee su
tutti i parametri, colorate con l'accento blu del sito invece di
dipendere dal set di emoji del telefono di chi guarda (che varia tra
Android/iPhone/Samsung e stona con la grafica pulita del sito).

Le lingue (Inglese, Francese, Spagnolo, Tedesco) usano un cerchio con
la sigla (EN/FR/ES/DE) invece della bandiera — più semplice da
disegnare in modo coerente con lo stile a linee, e senza le
ambiguità geopolitiche delle bandiere.

Da eseguire DOPO add_favicon_seo.py (è indipendente, ma segue lo
stesso repository nello stesso ordine di lavoro).

Uso:
    python replace_icons_svg.py

Da eseguire nella cartella radice del repository. È idempotente.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

ICON_SVG = {
    "INGLESE": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><text x="12" y="15.5" font-size="8" text-anchor="middle" fill="currentColor" stroke="none" font-family="sans-serif" font-weight="700">EN</text></svg>',
    "FRANCESE": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><text x="12" y="15.5" font-size="8" text-anchor="middle" fill="currentColor" stroke="none" font-family="sans-serif" font-weight="700">FR</text></svg>',
    "SPAGNOLO": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><text x="12" y="15.5" font-size="8" text-anchor="middle" fill="currentColor" stroke="none" font-family="sans-serif" font-weight="700">ES</text></svg>',
    "TEDESCO": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><text x="12" y="15.5" font-size="8" text-anchor="middle" fill="currentColor" stroke="none" font-family="sans-serif" font-weight="700">DE</text></svg>',
    "MENSA": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2v8a2 2 0 1 0 4 0V2M8 2v20"/><path d="M17 2c-2 0-3 3-3 6s1 4 3 4v10"/></svg>',
    "PALESTRA": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 9v6M7 7v10M17 7v10M20 9v6M7 12h10"/></svg>',
    "BIBLIOTECA": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5V4.5A1.5 1.5 0 0 1 5.5 3H18a1 1 0 0 1 1 1v14"/><path d="M6.5 3H18v18H6.5A1.5 1.5 0 0 1 5 19.5v0A1.5 1.5 0 0 1 6.5 18H19"/></svg>',
    "LABORATORIO_INFORMATICA": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="12" rx="1.5"/><path d="M8 20h8M12 16v4"/></svg>',
    "LABORATORIO_SCIENZE": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3h6M10 3v5.5L5.5 17a1.8 1.8 0 0 0 1.6 2.6h9.8a1.8 1.8 0 0 0 1.6-2.6L14 8.5V3"/><path d="M7.5 14h9"/></svg>',
    "LABORATORIO_MUSICALE": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="17" r="3"/><path d="M11 17V4l7 3"/></svg>',
    "LABORATORIO_ARTISTICO": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a9 9 0 1 0 0 18c1.5 0 2-1 2-2s-.5-1.5-.5-2.5S14 15 15 15h3a3 3 0 0 0 3-3c0-5-4-9-9-9Z"/><circle cx="7.5" cy="10.5" r="1" fill="currentColor" stroke="none"/><circle cx="9.5" cy="7" r="1" fill="currentColor" stroke="none"/><circle cx="14" cy="7" r="1" fill="currentColor" stroke="none"/></svg>',
    "ATELIER_DIGITALE": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="12" height="16" rx="2"/><path d="M9 17h0"/><path d="M19 13l2 2-7 7h-2v-2Z"/></svg>',
    "AULE_MULTIMEDIALI": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="9" width="8" height="6" rx="1.5"/><circle cx="6" cy="12" r="1.4"/><path d="M10 11l10-4v10l-10-4"/><path d="M21 5v14"/></svg>',
    "STEM": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="1.6" fill="currentColor" stroke="none"/><ellipse cx="12" cy="12" rx="9" ry="4"/><ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(120 12 12)"/></svg>',
    "ARTE": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 15c-2 2-2 4-4 4M13 5c3-3 6-1 6 2s-3 3-3 3l-7 7-4-4 7-7Z"/></svg>',
    "TEATRO": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 8c0-3 3.5-5 8-5s8 2 8 5c0 4-3 5-3 8a5 5 0 0 1-10 0c0-3-3-4-3-8Z"/><circle cx="9" cy="10" r="1" fill="currentColor" stroke="none"/><circle cx="15" cy="10" r="1" fill="currentColor" stroke="none"/><path d="M9 15c1.2 1 2.8 1 4 0"/></svg>',
    "SPORT": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7l3.5 2.5-1.3 4.1H9.8L8.5 9.5Z"/><path d="M12 3v4M4.5 8l3 1.7M4.7 16l3.3-1.6M19.3 16l-3.3-1.6M19.5 8l-3 1.7M12 17v4"/></svg>',
    "PNRR": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3c2 3 3 5.5 3 8a3 3 0 0 1-6 0c0-2.5 1-5 3-8Z"/><path d="M6 16c1.5-1 3-1 4 0M14 16c1-1 2.5-1 4 0M4 21h16"/></svg>',
    "INDIRIZZO_MUSICALE": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="7" cy="18" r="2.4"/><circle cx="15" cy="16" r="2.4"/><path d="M9.4 18V6l8-2v12"/><path d="M9.4 8l8-2"/></svg>',
    "STRUMENTI_MUSICALI": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="14" rx="1.5"/><path d="M8 5v9M12 5v9M16 5v9"/></svg>',
    "TEMPO_SCUOLA": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21V9l8-5 8 5v12"/><path d="M9 21v-6h6v6M4 9h16"/></svg>',
}


def log(msg):
    print(f"- {msg}")


def replace_icons():
    path = BASE_DIR / "docs" / "js" / "app.js"
    text = path.read_text(encoding="utf-8")

    if "<svg viewBox=" in text and "icon: `<svg" in text:
        log("app.js: icone già sostituite, salto.")
        return

    replaced = 0
    skipped = []

    for code, svg in ICON_SVG.items():
        marker_start = text.find(f"{code}: {{")
        if marker_start == -1:
            skipped.append(code)
            continue

        icon_key_pos = text.find('icon: "', marker_start)
        if icon_key_pos == -1:
            skipped.append(code)
            continue

        value_start = icon_key_pos + len('icon: "')
        value_end = text.find('"', value_start)

        new_line = f"icon: `{svg}`"
        text = text[:icon_key_pos] + new_line + text[value_end + 1:]
        replaced += 1

    if skipped:
        log(f"ATTENZIONE: {len(skipped)} parametri non trovati come "
            f"attesi ({', '.join(skipped)}), controllo manuale "
            f"consigliato in app.js")

    path.write_text(text, encoding="utf-8")
    log(f"app.js: {replaced}/21 emoji sostituite con icone SVG.")


def add_css():
    path = BASE_DIR / "docs" / "css" / "app.css"
    text = path.read_text(encoding="utf-8")

    if "ICONE SVG PARAMETRI" in text:
        log("app.css: stile icone già presente, salto.")
        return

    addition = '''

/* ============================================================
   ICONE SVG PARAMETRI (al posto delle emoji)
   ============================================================ */

.parameter-v4-icon,
.school-feature-icon {
    color: var(--accent);
}

.parameter-v4-icon svg,
.school-feature-icon svg {
    width: 55%;
    height: 55%;
}
'''

    with path.open("a", encoding="utf-8") as f:
        f.write(addition)

    log("app.css: stile per le icone SVG aggiunto.")


def main():
    print("Sostituzione emoji con icone SVG")
    print("=" * 60)
    replace_icons()
    add_css()
    print("=" * 60)
    print("Fatto. Controlla il risultato in locale prima di committare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
