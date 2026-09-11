"""
Aggiunge tre cose al sito, in un solo passaggio:

  1. COLORE: introduce un vero colore guida (blu) al posto del
     bianco/nero puro. Applicato a: numeri, link, barra di
     completamento, rank in classifica, "Confronta", pulsanti al
     passaggio del mouse. Il resto (sfondo, testo, bordi) resta
     invariato.

  2. LINK CONDIVISIBILE: aprendo una scheda scuola l'URL cambia in
     ?scuola=CODICE — copiabile e condivisibile (es. su WhatsApp).
     Chi apre quel link arriva direttamente sulla scheda, non sulla
     lista. Aggiunto anche un pulsante "Copia link" nella scheda.

  3. DATA DI AGGIORNAMENTO: la home mostra "dati aggiornati al
     [data]", calcolata automaticamente ad ogni esportazione.

Uso:
    python add_color_share_updated.py

Da eseguire nella cartella radice del repository. È idempotente.

IMPORTANTE — passo manuale dopo aver eseguito questo script:
   La data di aggiornamento viene scritta in statistics.json quando
   si rigenerano i dati pubblici:

       python3 -m src.export.export_public_data

   Senza questo passo la data non comparirà (o mostrerà quella vecchia).
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def log(msg):
    print(f"- {msg}")


# ---------------------------------------------------------------------
# 1. CSS — colore guida (blu) + link condivisibile + data
# ---------------------------------------------------------------------
def patch_css():
    path = BASE_DIR / "docs" / "css" / "app.css"
    text = path.read_text(encoding="utf-8")

    if "ACCENTO COLORE" in text:
        log("app.css: già aggiornato, salto.")
        return

    addition = '''

/* ============================================================
   ACCENTO COLORE
   ============================================================ */

:root {
    --accent: #185fa5;
    --accent-fill: #378add;
    --accent-soft: #e6f1fb;
}

a {
    color: var(--accent);
}

a:hover {
    text-decoration: underline;
}

.eyebrow {
    color: var(--accent);
}

.kpi strong {
    color: var(--accent);
}

.ranking-rank {
    color: var(--accent);
}

.ranking-score-value {
    color: var(--accent);
}

.ranking-score-value.ranking-score-no-data {
    color: var(--muted);
}

.ranking-progress-track {
    background: var(--accent-soft);
}

.ranking-progress-fill {
    background: var(--accent-fill);
    opacity: 1;
}

.school-compare-check {
    color: var(--accent);
}

.reset-filters:hover {
    border-color: var(--accent);
    color: var(--accent);
}

.back-button:hover {
    color: var(--accent);
}

/* ============================================================
   COPIA LINK SCHEDA SCUOLA
   ============================================================ */

.detail-header-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 4px;
}

.copy-link-button {
    padding: 6px 12px;
    border: 1px solid var(--line);
    border-radius: 20px;
    background: transparent;
    color: var(--muted);
    font-size: 0.75rem;
    font-weight: 700;
    cursor: pointer;
    white-space: nowrap;
}

.copy-link-button:hover {
    border-color: var(--accent);
    color: var(--accent);
}

.hero-updated {
    color: var(--muted);
    font-size: 0.82rem;
}
'''

    with path.open("a", encoding="utf-8") as f:
        f.write(addition)

    log("app.css: colore, pulsante copia link e data aggiornamento "
        "aggiunti in coda al file.")


# ---------------------------------------------------------------------
# 2. HTML — paragrafo data nella hero (sempre visibile, anche mobile)
# ---------------------------------------------------------------------
def patch_html():
    path = BASE_DIR / "docs" / "index.html"
    text = path.read_text(encoding="utf-8")

    if 'id="lastUpdated"' in text:
        log("index.html: già aggiornato, salto.")
        return

    old_hero = '''            <p>
                <strong>Non è una valutazione della scuola.</strong>
                È una fotografia documentale dell'offerta dichiarata.
            </p>

        </div>

    </section>'''

    new_hero = '''            <p>
                <strong>Non è una valutazione della scuola.</strong>
                È una fotografia documentale dell'offerta dichiarata.
            </p>

            <p class="hero-updated" id="lastUpdated"></p>

        </div>

    </section>'''

    if old_hero not in text:
        log("ATTENZIONE: paragrafo hero non trovato come atteso, "
            "controllo manuale necessario in index.html")
        return

    text = text.replace(old_hero, new_hero)
    path.write_text(text, encoding="utf-8")
    log("index.html: indicazione data aggiunta nella hero.")


# ---------------------------------------------------------------------
# 3. Backend — timestamp di generazione in statistics.json
# ---------------------------------------------------------------------
def patch_export_backend():
    path = BASE_DIR / "src" / "export" / "export_public_data.py"
    text = path.read_text(encoding="utf-8")

    if "generated_at" in text:
        log("export_public_data.py: già aggiornato, salto.")
        return

    old_import = "from pathlib import Path\nimport json\nimport math\nimport sqlite3"
    new_import = ("from pathlib import Path\nimport json\nimport math\n"
                   "import sqlite3\nfrom datetime import datetime, timezone")

    if old_import not in text:
        log("ATTENZIONE: blocco import non trovato come atteso, "
            "controllo manuale necessario in export_public_data.py")
        return

    text = text.replace(old_import, new_import)

    old_return = '''    return {
        "schools": schools,
        "documents": documents,
        "evidence": evidence,
        "active_parameters": parameters,
        "school_parameters": school_parameters,
        "status": {
            "VERIFIED": verified,
            "PROBABLE": probable,
            "MENTIONED": mentioned,
            "NOT_FOUND": not_found,
        }
    }'''

    new_return = '''    return {
        "schools": schools,
        "documents": documents,
        "evidence": evidence,
        "active_parameters": parameters,
        "school_parameters": school_parameters,
        "status": {
            "VERIFIED": verified,
            "PROBABLE": probable,
            "MENTIONED": mentioned,
            "NOT_FOUND": not_found,
        },
        "generated_at": datetime.now(timezone.utc).isoformat()
    }'''

    if old_return not in text:
        log("ATTENZIONE: return di export_statistics non trovato come "
            "atteso, controllo manuale necessario in "
            "export_public_data.py")
        return

    text = text.replace(old_return, new_return)
    path.write_text(text, encoding="utf-8")
    log("export_public_data.py: timestamp di generazione aggiunto.")


# ---------------------------------------------------------------------
# 4. JS — URL condivisibile, copia link, data aggiornamento
# ---------------------------------------------------------------------
def patch_js():
    path = BASE_DIR / "docs" / "js" / "app.js"
    text = path.read_text(encoding="utf-8")

    if "copySchoolLink" in text:
        log("app.js: già aggiornato, salto.")
        return

    # --- data di ultimo aggiornamento ---
    old_date = '''    $( "schoolCount" ).textContent =
        statistics.schools ??
        schools.length;


    populateProvinceFilter();'''

    new_date = '''    $( "schoolCount" ).textContent =
        statistics.schools ??
        schools.length;

    if (statistics.generated_at && $("lastUpdated")) {
        const generatedDate = new Date(statistics.generated_at);

        if (!Number.isNaN(generatedDate.getTime())) {
            $("lastUpdated").textContent =
                "dati aggiornati al " +
                generatedDate.toLocaleDateString("it-IT", {
                    day: "numeric",
                    month: "long",
                    year: "numeric"
                });
        }
    }


    populateProvinceFilter();'''

    if old_date not in text:
        log("ATTENZIONE: punto di inserimento data aggiornamento non "
            "trovato, controllo manuale necessario in app.js")
        return

    text = text.replace(old_date, new_date)

    # --- apertura automatica da URL condiviso ---
    old_auto_open = '''    populateProvinceFilter();

    renderRanking();
    renderMap();
}'''

    new_auto_open = '''    populateProvinceFilter();

    renderRanking();
    renderMap();

    // Se il link contiene ?scuola=CODICE, apre direttamente quella
    // scheda invece della lista — è quello che rende il link
    // condivisibile utile (es. mandato su WhatsApp).
    const requestedSchoolCode =
        new URLSearchParams(window.location.search).get("scuola");

    if (requestedSchoolCode) {
        const requestedSchool = schools.find(
            s => s.codice_scuola === requestedSchoolCode
        );

        if (requestedSchool) {
            showDetail(requestedSchool.id);
        }
    }
}'''

    if old_auto_open not in text:
        log("ATTENZIONE: punto di aggancio apertura automatica non "
            "trovato, controllo manuale necessario in app.js")
        return

    text = text.replace(old_auto_open, new_auto_open)

    # --- funzione copySchoolLink + intestazione con pulsante ---
    old_header = '''        <div class="detail-header">

            <span class="eyebrow">
                ${escapeHtml(
                    school.codice_scuola
                )}
            </span>

            <h1>
                ${escapeHtml(
                    school.denominazione
                )}
            </h1>

            <div class="detail-meta">

                ${escapeHtml(
                    school.comune
                )}

                ·

                ${escapeHtml(
                    school.provincia
                )}

                ${
                    school.indirizzo
                        ? ` · ${escapeHtml(school.indirizzo)}`
                        : ""
                }

            </div>

        </div>'''

    new_header = '''        <div class="detail-header">

            <div class="detail-header-top">

                <span class="eyebrow">
                    ${escapeHtml(
                        school.codice_scuola
                    )}
                </span>

                <button
                    type="button"
                    class="copy-link-button"
                    id="copyLinkButton"
                    onclick="copySchoolLink(${school.id})"
                >
                    Copia link
                </button>

            </div>

            <h1>
                ${escapeHtml(
                    school.denominazione
                )}
            </h1>

            <div class="detail-meta">

                ${escapeHtml(
                    school.comune
                )}

                ·

                ${escapeHtml(
                    school.provincia
                )}

                ${
                    school.indirizzo
                        ? ` · ${escapeHtml(school.indirizzo)}`
                        : ""
                }

            </div>

        </div>'''

    if old_header not in text:
        log("ATTENZIONE: intestazione scheda scuola non trovata come "
            "attesa, controllo manuale necessario in app.js")
        return

    text = text.replace(old_header, new_header)

    old_fn_anchor = '''function showDetail(schoolId) {'''

    new_fn_anchor = '''function copySchoolLink(schoolId) {

    const school = schools.find(s => s.id === schoolId);

    if (!school) {
        return;
    }

    const shareUrl = new URL(window.location.href);
    shareUrl.searchParams.set("scuola", school.codice_scuola);

    const button = $("copyLinkButton");

    navigator.clipboard.writeText(shareUrl.toString())
        .then(() => {
            if (!button) return;
            const original = button.textContent;
            button.textContent = "Link copiato";
            setTimeout(() => {
                button.textContent = original;
            }, 1800);
        })
        .catch(() => {
            if (!button) return;
            button.textContent = "Copia manuale dalla barra indirizzi";
        });
}


function showDetail(schoolId) {'''

    if old_fn_anchor not in text:
        log("ATTENZIONE: punto di inserimento copySchoolLink non "
            "trovato, controllo manuale necessario in app.js")
        return

    text = text.replace(old_fn_anchor, new_fn_anchor)

    # --- aggiornamento URL quando si apre la scheda ---
    old_open_url = '''    $("schoolList").parentElement.classList.add("hidden");
    $("detail").classList.remove("hidden");'''

    new_open_url = '''    $("schoolList").parentElement.classList.add("hidden");
    $("detail").classList.remove("hidden");

    // URL condivisibile: chi apre questo link arriva direttamente
    // sulla scheda della scuola, senza dover cercarla nell'elenco.
    const shareUrl = new URL(window.location.href);
    shareUrl.searchParams.set("scuola", school.codice_scuola);
    history.pushState(
        { schoolId },
        "",
        shareUrl.toString()
    );
    document.title =
        `${school.denominazione} — School Intelligence`;'''

    if old_open_url not in text:
        log("ATTENZIONE: punto di aggancio apertura scheda non "
            "trovato, controllo manuale necessario in app.js")
        return

    text = text.replace(old_open_url, new_open_url)

    # --- aggiornamento URL quando si chiude la scheda + tasto indietro ---
    old_close = '''$("closeDetail").addEventListener(
    "click",
    () => {

        $("detail").classList.add(
            "hidden"
        );

        $("schoolList").parentElement.classList.remove(
            "hidden"
        );
    }
);'''

    new_close = '''function closeDetailView() {

    $("detail").classList.add(
        "hidden"
    );

    $("schoolList").parentElement.classList.remove(
        "hidden"
    );

    const shareUrl = new URL(window.location.href);
    shareUrl.searchParams.delete("scuola");
    history.pushState(
        {},
        "",
        shareUrl.toString()
    );
    document.title = "School Intelligence";
}


$("closeDetail").addEventListener(
    "click",
    closeDetailView
);

// Torna al ranking anche con il pulsante "indietro" del browser,
// invece di uscire dal sito.
window.addEventListener(
    "popstate",
    () => {
        const codiceScuola =
            new URLSearchParams(window.location.search).get("scuola");

        if (!codiceScuola) {
            closeDetailView();
            return;
        }

        const school = schools.find(
            s => s.codice_scuola === codiceScuola
        );

        if (school) {
            showDetail(school.id);
        }
    }
);'''

    if old_close not in text:
        log("ATTENZIONE: listener closeDetail non trovato, controllo "
            "manuale necessario in app.js")
        return

    text = text.replace(old_close, new_close)

    path.write_text(text, encoding="utf-8")
    log("app.js: URL condivisibile, copia link e data aggiornamento "
        "collegati.")


def main():
    print("Colore, link condivisibile e data di aggiornamento")
    print("=" * 60)
    patch_css()
    patch_html()
    patch_export_backend()
    patch_js()
    print("=" * 60)
    print("Fatto.")
    print()
    print("PASSO SUCCESSIVO OBBLIGATORIO — rigenera i dati pubblici:")
    print("  python3 -m src.export.export_public_data")
    print()
    print("Poi controlla il risultato in locale prima di committare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
