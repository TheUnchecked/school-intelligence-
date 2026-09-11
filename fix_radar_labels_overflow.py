"""
Corregge il grafico radar della scheda scuola: su schermi larghi
(desktop) le etichette più lunghe ("Servizi", "Organizzazione",
"Attività e didattica") uscivano dal bordo del grafico e venivano
tagliate a metà.

Causa: il margine tra il bordo del radar e il bordo del disegno era
troppo stretto per le etichette sugli assi quasi orizzontali
(quelli a sinistra e a destra, dove il testo si allunga
orizzontalmente invece di restare centrato).

Correzione:
  - Radar più grande, con più margine per le etichette.
  - "Attività e didattica" -> "Didattica" (coerente col titolo
    "DIDATTICA" già usato altrove nella scheda).
  - "Organizzazione" -> "Orario" (l'unica voce di questa categoria è
    "Tempo scuola").
  - overflow:visible sull'SVG come rete di sicurezza, così anche in
    casi limite il testo non viene mai tagliato bruscamente.

Uso:
    python fix_radar_labels_overflow.py

Da eseguire nella cartella radice del repository, DOPO
fix_radar_categories.py. È idempotente.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def log(msg):
    print(f"- {msg}")


def patch_js():
    path = BASE_DIR / "docs" / "js" / "app.js"
    text = path.read_text(encoding="utf-8")

    if 'label: "Orario"' in text:
        log("app.js: correzione già applicata, salto.")
        return

    old_labels = '{ key: "DIDATTICA", label: "Attività e didattica" },\n    { key: "ORGANIZZAZIONE", label: "Organizzazione" }'
    new_labels = '{ key: "DIDATTICA", label: "Didattica" },\n    { key: "ORGANIZZAZIONE", label: "Orario" }'

    if old_labels not in text:
        log("ATTENZIONE: etichette RADAR_CATEGORIES non trovate come "
            "attese (hai già applicato fix_radar_categories.py?), "
            "controllo manuale necessario in app.js")
        return

    text = text.replace(old_labels, new_labels)

    old_size = '''    const size = 240;
    const center = size / 2;
    const radius = 82;
    const labelRadius = radius + 30;'''

    new_size = '''    const size = 340;
    const center = size / 2;
    const radius = 88;
    const labelRadius = radius + 48;'''

    if old_size not in text:
        log("ATTENZIONE: dimensioni del radar non trovate come "
            "attese, controllo manuale necessario in app.js")
        return

    text = text.replace(old_size, new_size)

    old_labels_block = '''    const labels = scores
        .map((s, i) => {

            const angle = angleFor(i);
            const x = center + labelRadius * Math.cos(angle);
            const y = center + labelRadius * Math.sin(angle);

            const anchor =
                Math.abs(Math.cos(angle)) < 0.2
                    ? "middle"
                    : Math.cos(angle) > 0
                        ? "start"
                        : "end";

            return `
                <text x="${x}" y="${y - 5}" text-anchor="${anchor}" class="radar-label">${escapeHtml(s.category)}</text>
                <text x="${x}" y="${y + 11}" text-anchor="${anchor}" class="radar-label-value">${s.percent}%</text>
            `;
        })
        .join("");'''

    new_labels_block = '''    const labels = scores
        .map((s, i) => {

            const angle = angleFor(i);
            const x = center + labelRadius * Math.cos(angle);
            const y = center + labelRadius * Math.sin(angle);

            const anchor =
                Math.abs(Math.cos(angle)) < 0.25
                    ? "middle"
                    : Math.cos(angle) > 0
                        ? "start"
                        : "end";

            return `
                <text x="${x}" y="${y - 4}" text-anchor="${anchor}" class="radar-label">${escapeHtml(s.category)}</text>
                <text x="${x}" y="${y + 10}" text-anchor="${anchor}" class="radar-label-value">${s.percent}%</text>
            `;
        })
        .join("");'''

    if old_labels_block not in text:
        log("ATTENZIONE: blocco etichette non trovato come atteso, "
            "controllo manuale necessario in app.js")
        return

    text = text.replace(old_labels_block, new_labels_block)
    path.write_text(text, encoding="utf-8")
    log("app.js: radar ingrandito e margini corretti per evitare il "
        "taglio delle etichette.")


def patch_css():
    path = BASE_DIR / "docs" / "css" / "app.css"
    text = path.read_text(encoding="utf-8")

    if ".radar-chart {\n    width: 100%;\n    max-width: 360px;\n    height: auto;\n    overflow: visible;\n}" in text:
        log("app.css: correzione già applicata, salto.")
        return

    old = '''.radar-chart {
    width: 100%;
    max-width: 320px;
    height: auto;
}'''

    new = '''.radar-chart {
    width: 100%;
    max-width: 360px;
    height: auto;
    overflow: visible;
}'''

    if old not in text:
        log("ATTENZIONE: regola .radar-chart non trovata come "
            "attesa, controllo manuale necessario in app.css")
        return

    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    log("app.css: overflow:visible aggiunto come rete di sicurezza.")


def main():
    print("Correzione taglio etichette radar su desktop")
    print("=" * 60)
    patch_js()
    patch_css()
    print("=" * 60)
    print("Fatto. Controlla il risultato in locale prima di committare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
