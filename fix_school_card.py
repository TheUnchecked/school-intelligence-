"""
Patch unica per riordinare la scheda scuola (docs/js/app.js).

Il problema: dopo "Cosa offre la scuola" la pagina mostrava, in
sequenza, un titolo doppio "Informazioni sulla scuola" (uno orfano,
senza contenuto proprio, e uno reale più sotto), poi due tabelle molto
tecniche ("Riscontri documentali" con dettagli di affidabilità per
singolo documento, e "Documenti analizzati") PRIMA della griglia
leggibile con le icone per categoria (Didattica, Lingue, Servizi...).
Risultato: la parte tecnica dominava la scheda invece della parte
leggibile per un utente qualunque.

La correzione:
  1. Sposta la griglia leggibile ("Informazioni sulla scuola", icone
     per categoria) subito dopo "Cosa offre la scuola".
  2. Rimuove il titolo duplicato/orfano.
  3. Racchiude le due tabelle tecniche ("Riscontri documentali" e
     "Documenti analizzati") dentro un unico blocco <details>
     collassabile "Dettagli e fonti documentali", chiuso di default,
     in fondo alla scheda — riusando lo stile .technical-details
     già presente (ma inutilizzato) in docs/css/app.css.

Si applica una sola volta al template condiviso da tutte le schede
scuola: corregge automaticamente tutte le schede insieme.

Uso:
    python fix_school_card.py

Da eseguire nella cartella radice del repository. È idempotente:
se il file è già nel nuovo ordine, non fa nulla.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_JS = BASE_DIR / "docs" / "js" / "app.js"


def section_span(text, open_marker, start_from=0):
    start = text.index(open_marker, start_from)
    close = text.index("\n        </section>", start) + len("\n        </section>")
    return start, close


def indent_block(block, extra="    "):
    return "\n".join(
        (extra + line if line.strip() else line)
        for line in block.split("\n")
    )


def main():
    if not APP_JS.exists():
        print(f"ERRORE: file non trovato: {APP_JS}")
        return 1

    text = APP_JS.read_text(encoding="utf-8")

    if 'class="technical-details"' in text:
        print("docs/js/app.js: già riordinato, nessuna modifica necessaria.")
        return 0

    required_markers = [
        '        <section class="school-snapshot">',
        '        <section class="detail-ptof">',
        '        <section class="school-data-section evidence-section">',
        '        <section class="school-data-section documents-section">',
        '        <section class="school-information-section">',
    ]
    for marker in required_markers:
        if text.count(marker) != 1:
            print(f"ATTENZIONE: struttura inattesa in docs/js/app.js, "
                  f"marcatore non trovato una sola volta: {marker!r}")
            print("Nessuna modifica applicata. Controllo manuale necessario.")
            return 1

    head_end = text.index('        <section class="school-snapshot">')
    snap_start, snap_end = section_span(text, '        <section class="school-snapshot">')
    ptof_start, ptof_end = section_span(text, '        <section class="detail-ptof">')
    evid_start, evid_end = section_span(text, '        <section class="school-data-section evidence-section">')
    docs_start, docs_end = section_span(text, '        <section class="school-data-section documents-section">')
    info_start, info_end = section_span(text, '        <section class="school-information-section">')

    # Le sezioni devono comparire in quest'ordine nel file originale,
    # altrimenti la struttura è cambiata rispetto a quella attesa.
    if not (snap_end < ptof_start < ptof_end < evid_start < evid_end
            < docs_start < docs_end < info_start < info_end):
        print("ATTENZIONE: l'ordine delle sezioni non è quello atteso, "
              "controllo manuale necessario. Nessuna modifica applicata.")
        return 1

    head = text[:head_end]
    snap_block = text[snap_start:snap_end]
    ptof_block = text[ptof_start:ptof_end]
    evid_block = text[evid_start:evid_end]
    docs_block = text[docs_start:docs_end]
    info_block = text[info_start:info_end]
    tail = text[info_end:]

    evid_block_indented = indent_block(evid_block)
    docs_block_indented = indent_block(docs_block)

    technical_section = f'''        <details class="technical-details">

            <summary class="technical-details-summary">

                <div>
                    <span class="eyebrow">
                        APPROFONDIMENTO
                    </span>
                    <strong>
                        Dettagli e fonti documentali
                    </strong>
                </div>

                <span class="technical-details-count">
                    ${{schoolEvidence.length + documentIds.length}}
                </span>

            </summary>

{evid_block_indented}

{docs_block_indented}

        </details>'''

    new_text = (
        head
        + snap_block
        + "\n\n\n"
        + info_block
        + "\n\n\n"
        + ptof_block
        + "\n\n\n"
        + technical_section
        + "\n\n"
        + tail
    )

    APP_JS.write_text(new_text, encoding="utf-8")

    print("docs/js/app.js riordinato:")
    print("  1. 'Informazioni sulla scuola' spostata subito dopo 'Cosa offre la scuola'")
    print("  2. Titolo duplicato/orfano rimosso")
    print("  3. 'Riscontri documentali' + 'Documenti analizzati' raggruppati in un")
    print("     unico blocco collassabile 'Dettagli e fonti documentali' in fondo")
    print("\nControlla il risultato visivamente prima di committare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
