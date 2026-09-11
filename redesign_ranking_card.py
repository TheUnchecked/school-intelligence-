"""
Redesign della card di classifica (docs/js/app.js + docs/css/app.css).

Sostituisce le 4 metriche affiancate ("Dati disponibili", "Affidabilità
dei dati", "Informazioni verificate", "Riscontri documentali") con:

  1. Una barra di completamento con etichetta leggibile
     ("15/21 parametri verificati" invece di un numero isolato senza
     contesto).
  2. Un footer con il controllo "Confronta" (ora finalmente in flusso
     normale — la posizione assoluta non era mai stata rimossa del
     tutto nella correzione precedente, restava attiva anche dopo lo
     spostamento del markup) e il numero di riscontri documentali,
     retrocesso a dettaglio secondario.

Si applica al template condiviso da tutte le card, quindi corregge
automaticamente tutta la lista scuole in un solo passaggio.

Uso:
    python redesign_ranking_card.py

Da eseguire nella cartella radice del repository. È idempotente.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def log(msg):
    print(f"- {msg}")


def redesign_js():
    path = BASE_DIR / "docs" / "js" / "app.js"
    text = path.read_text(encoding="utf-8")

    if "ranking-progress" in text:
        log("app.js: card già riprogettata, salto.")
        return

    old_block = '''        const statsHtml =
            hasData
                ? `
                    <div class="ranking-stat">
                        <span>Dati disponibili</span>
                        <strong>
                            ${formatPercent(score?.coverage_percent)}
                        </strong>
                    </div>

                    <div class="ranking-stat">
                        <span>Affidabilità dei dati</span>
                        <strong>
                            ${formatPercent(score?.confidence_percent)}
                        </strong>
                    </div>

                    <div class="ranking-stat">
                        <span>Informazioni verificate</span>
                        <strong>
                            ${score?.verified_count ?? 0}
                        </strong>
                    </div>

                    <div class="ranking-stat">
                        <span>Riscontri documentali</span>
                        <strong>
                            ${evidenceCount}
                        </strong>
                    </div>
                `
                : `
                    <div class="ranking-stat ranking-stat-message">
                        <span>Stato della valutazione</span>
                        <strong>
                            Nessun riscontro documentale
                        </strong>
                    </div>

                    <div class="ranking-stat">
                        <span>Parametri da verificare</span>
                        <strong>
                            ${score?.parameter_count ?? 21}
                        </strong>
                    </div>
                `;

        card.innerHTML = `
            <div class="ranking-card ${
    selectedSchools.has(Number(school.id))
        ? "is-selected"
        : ""
}">

                <div class="ranking-card-header">

                    <div class="ranking-card-identity">

                        <div class="ranking-rank">
                            ${rankLabel}
                        </div>

                        <div class="ranking-school-name">
                            ${escapeHtml(school.denominazione)}
                        </div>

                        <div class="ranking-school-meta">
                            ${escapeHtml(school.comune)}
                            ·
                            ${escapeHtml(school.provincia)}
                            ·
                            ${escapeHtml(school.codice_scuola)}
                        </div>

                    </div>

                    <div class="ranking-score">

                        <label class="school-compare-check">

                            <input
                                type="checkbox"
                                ${
                                    selectedSchools.has(Number(school.id))
                                        ? "checked"
                                        : ""
                                }
                                onchange="
                                    finalToggleSchoolSelection(${school.id})
                                "
                                onclick="event.stopPropagation()"
                            >

                            <span>Confronta</span>

                        </label>

                        <div class="ranking-score-value ${
                            hasData
                                ? ""
                                : "ranking-score-no-data"
                        }">
                            ${scoreValue}
                        </div>

                        <div class="ranking-score-label">
                            ${scoreLabel}
                        </div>

                    </div>

                </div>

                <div class="ranking-stats">
                    ${statsHtml}
                </div>

            </div>
        `;'''

    new_block = '''        const verifiedCount =
            hasData
                ? Number(score?.verified_count ?? 0)
                : 0;

        const totalParameters =
            Number(score?.parameter_count ?? 21);

        const coveragePercent =
            hasData
                ? Math.max(0, Math.min(100, Number(score?.coverage_percent ?? 0)))
                : 0;

        card.innerHTML = `
            <div class="ranking-card ${
    selectedSchools.has(Number(school.id))
        ? "is-selected"
        : ""
}">

                <div class="ranking-card-header">

                    <div class="ranking-card-identity">

                        <div class="ranking-rank">
                            ${rankLabel}
                        </div>

                        <div class="ranking-school-name">
                            ${escapeHtml(school.denominazione)}
                        </div>

                        <div class="ranking-school-meta">
                            ${escapeHtml(school.comune)}
                            ·
                            ${escapeHtml(school.provincia)}
                            ·
                            ${escapeHtml(school.codice_scuola)}
                        </div>

                    </div>

                    <div class="ranking-score">

                        <div class="ranking-score-value ${
                            hasData
                                ? ""
                                : "ranking-score-no-data"
                        }">
                            ${scoreValue}
                        </div>

                        <div class="ranking-score-label">
                            ${scoreLabel}
                        </div>

                    </div>

                </div>

                <div class="ranking-progress">

                    <div class="ranking-progress-track">
                        <div
                            class="ranking-progress-fill"
                            style="width: ${coveragePercent}%"
                        ></div>
                    </div>

                    <span class="ranking-progress-label">
                        ${verifiedCount}/${totalParameters} parametri verificati
                    </span>

                </div>

                <div class="ranking-footer">

                    <label class="school-compare-check">

                        <input
                            type="checkbox"
                            ${
                                selectedSchools.has(Number(school.id))
                                    ? "checked"
                                    : ""
                            }
                            onchange="
                                finalToggleSchoolSelection(${school.id})
                            "
                            onclick="event.stopPropagation()"
                        >

                        <span>Confronta</span>

                    </label>

                    <span class="ranking-footer-meta">
                        ${evidenceCount} riscontri documentali
                    </span>

                </div>

            </div>
        `;'''

    if old_block not in text:
        log("ATTENZIONE: struttura della card diversa da quella attesa, "
            "controllo manuale necessario in docs/js/app.js")
        return

    text = text.replace(old_block, new_block)
    path.write_text(text, encoding="utf-8")
    log("app.js: card riprogettata — barra di completamento al posto "
        "delle 4 metriche affiancate, checkbox nel footer.")


def redesign_css():
    path = BASE_DIR / "docs" / "css" / "app.css"
    text = path.read_text(encoding="utf-8")

    if ".ranking-progress" in text:
        log("app.css: stili già aggiornati, salto.")
        return

    replacements = [
        (
            '''.ranking-stats {
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    gap: 20px !important;
    width: 100% !important;
    margin-top: 22px;
    padding-top: 18px;
    border-top: 1px solid var(--line);
}

.ranking-stat {
    min-width: 0;
}

.ranking-stat span {
    display: block;
    color: var(--muted);
    font-size: 0.72rem;
    line-height: 1.2;
}

.ranking-stat strong {
    display: block;
    margin-top: 4px;
    font-size: 0.95rem;
    line-height: 1.2;
}''',
            '''.ranking-progress {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    width: 100% !important;
    margin-top: 20px;
    padding-top: 18px;
    border-top: 1px solid var(--line);
}

.ranking-progress-track {
    flex: 1 1 auto;
    height: 6px;
    border-radius: 3px;
    background: var(--line);
    overflow: hidden;
}

.ranking-progress-fill {
    height: 100%;
    border-radius: 3px;
    background: currentColor;
    opacity: .55;
}

.ranking-progress-label {
    flex: 0 0 auto;
    color: var(--muted);
    font-size: 0.78rem;
    white-space: nowrap;
}

.ranking-footer {
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
    gap: 12px !important;
    width: 100% !important;
    margin-top: 14px;
}

.ranking-footer-meta {
    color: var(--muted);
    font-size: 0.75rem;
    white-space: nowrap;
}''',
        ),
        (
            '''    .ranking-stats {
        grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        gap: 16px 20px !important;
        margin-top: 22px;
        padding-top: 18px;
    }

    .ranking-stat span {
        font-size: 0.7rem;
    }

    .ranking-stat strong {
        font-size: 0.95rem;
    }
}''',
            '''    .ranking-progress {
        margin-top: 20px;
        padding-top: 18px;
    }

    .ranking-footer {
        flex-wrap: wrap;
    }
}''',
        ),
        (
            '''    .ranking-stats {
        gap: 14px !important;
    }
}''',
            '''    .ranking-progress-label {
        font-size: 0.72rem;
    }
}''',
        ),
        (
            '''.school-compare-check {
    position: absolute;
    top: 14px;
    right: 14px;
    z-index: 5;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: .72rem;
    font-weight: 750;
    cursor: pointer;
}''',
            '''.school-compare-check {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: .72rem;
    font-weight: 750;
    cursor: pointer;
}''',
        ),
        (
            '''    .school-compare-check {
        position: static;
        margin-bottom: 10px;
    }
}''',
            '''}''',
        ),
    ]

    missing = [old for old, new in replacements if old not in text]
    if missing:
        log("ATTENZIONE: uno o più blocchi CSS attesi non sono stati "
            "trovati, controllo manuale necessario in docs/css/app.css")
        return

    for old, new in replacements:
        text = text.replace(old, new)

    path.write_text(text, encoding="utf-8")
    log("app.css: barra di completamento, footer aggiunti; "
        "posizionamento assoluto del checkbox 'Confronta' rimosso "
        "definitivamente (non era mai stato tolto del tutto prima).")


def main():
    print("Redesign card classifica — barra di completamento")
    print("=" * 60)
    redesign_js()
    redesign_css()
    print("=" * 60)
    print("Fatto. Controlla il risultato in locale prima di committare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
