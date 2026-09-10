"""
Pulizia definitiva del repository school-intelligence.

Corregge in un solo passaggio i problemi rilevati nella revisione più
recente:

  1. Bug di sovrapposizione checkbox "Confronta" / punteggio nella
     classifica: il checkbox era posizionato in modo assoluto sopra il
     punteggio. Viene spostato nel flusso normale della card.
  2. CSS morto rimosso: 3 blocchi duplicati per un controllo checkbox
     che non esiste più nell'HTML (classi .school-compare-checkbox e
     .school-compare-control, mai usate nel markup reale), residuo di
     patch precedenti mai ripulite.
  3. Workflow GitHub Actions: rimossa di nuovo la riga che ri-traccia
     il database SQLite binario su Git (regressione rispetto alla
     correzione precedente, reintrodotta da modifiche successive).
  4. Gestione errori in produzione: il sito mostrava lo stack trace
     completo agli utenti in caso di errore. Ora mostra un messaggio
     comprensibile; il dettaglio tecnico resta nella console del
     browser per chi sta facendo debug.
  5. Archivia fix_school_card.py (già usato, non più necessario nella
     root) in scripts/maintenance/.

Uso:
    python cleanup_repo.py

Da eseguire nella cartella radice del repository. È idempotente.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def log(msg):
    print(f"- {msg}")


# ---------------------------------------------------------------------
# 1. Sposta il checkbox "Confronta" nel flusso normale della card
# ---------------------------------------------------------------------
def fix_compare_checkbox_overlap():
    path = BASE_DIR / "docs" / "js" / "app.js"
    text = path.read_text(encoding="utf-8")

    old_card_open = '''        card.innerHTML = `
            <div class="ranking-card ${
    selectedSchools.has(Number(school.id))
        ? "is-selected"
        : ""
}">

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


                <div class="ranking-card-header">'''

    new_card_open = '''        card.innerHTML = `
            <div class="ranking-card ${
    selectedSchools.has(Number(school.id))
        ? "is-selected"
        : ""
}">

                <div class="ranking-card-header">'''

    old_score_block = '''                    <div class="ranking-score">

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

                    </div>'''

    new_score_block = '''                    <div class="ranking-score">

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

                    </div>'''

    if old_card_open not in text:
        log("app.js: markup checkbox già spostato (o struttura diversa), salto.")
        return

    text = text.replace(old_card_open, new_card_open)

    if old_score_block not in text:
        log("ATTENZIONE: blocco ranking-score non trovato come atteso, "
            "controllo manuale necessario in docs/js/app.js")
        return

    text = text.replace(old_score_block, new_score_block)
    path.write_text(text, encoding="utf-8")
    log("app.js: checkbox 'Confronta' spostato nel flusso normale, sopra "
        "il punteggio — niente più sovrapposizione.")


# ---------------------------------------------------------------------
# 2. Rimuove il CSS morto del vecchio controllo checkbox
# ---------------------------------------------------------------------
def clean_dead_checkbox_css():
    path = BASE_DIR / "docs" / "css" / "app.css"
    text = path.read_text(encoding="utf-8")

    if ".school-compare-checkbox" not in text and ".school-compare-control" not in text:
        log("app.css: CSS morto già rimosso, salto.")
        return

    removed = 0

    # --- Blocco morto 1: subito prima di "/* Tabella confronto */" ---
    old_1 = '''/* Checkbox confronto */

.ranking-card {
  position: relative;
}

.school-compare-checkbox {
  position: absolute;

  top: 13px;
  right: 13px;

  z-index: 5;

  width: 23px;
  height: 23px;

  margin: 0;

  cursor: pointer;
}

.ranking-card.is-selected {
  outline: 2px solid currentColor;
  outline-offset: 2px;
}

/* Tabella confronto */'''
    if old_1 in text:
        text = text.replace(old_1, "/* Tabella confronto */")
        removed += 1

    # --- Regola morta annidata nella relativa media query mobile ---
    old_2 = '''  .school-compare-checkbox {
    top: 9px;
    right: 9px;

    width: 24px;
    height: 24px;
  }

}'''
    if old_2 in text:
        text = text.replace(old_2, "}")
        removed += 1

    # --- Blocco morto 2: "/* Card */" ---
    old_3 = '''/* Card */

.ranking-card {
  position: relative;
}

.school-compare-checkbox {
  position: absolute;

  top: 12px;
  right: 12px;

  z-index: 5;

  width: 23px;
  height: 23px;

  margin: 0;

  cursor: pointer;
}

.ranking-card.is-selected {
  outline: 2px solid currentColor;
  outline-offset: 2px;
}

/* Mobile */'''
    if old_3 in text:
        text = text.replace(old_3, "/* Mobile */")
        removed += 1

    old_4 = '''  .school-compare-checkbox {
    top: 9px;
    right: 9px;

    width: 24px;
    height: 24px;
  }
}'''
    if old_4 in text:
        text = text.replace(old_4, "}")
        removed += 1

    # --- Blocco morto 3: "/* Checkbox */" finale, con .school-compare-control ---
    old_5 = '''/* Checkbox */

.ranking-card {
  position: relative;
}

.school-compare-control {
  position: absolute;

  top: 10px;
  right: 10px;

  z-index: 20;

  display: flex;
  align-items: center;
  justify-content: center;

  width: 34px;
  height: 34px;

  border-radius: 9px;

  background: rgba(255,255,255,.92);

  cursor: pointer;
}

.school-compare-checkbox {
  width: 22px;
  height: 22px;

  margin: 0;

  cursor: pointer;
}

.ranking-card.is-selected {
  outline: 2px solid currentColor;
  outline-offset: 2px;
}
'''
    if old_5 in text:
        text = text.replace(old_5, "")
        removed += 1

    old_6 = '''  .school-compare-control {
    top: 8px;
    right: 8px;

    width: 36px;
    height: 36px;
  }

  .school-compare-checkbox {
    width: 24px;
    height: 24px;
  }
}'''
    if old_6 in text:
        text = text.replace(old_6, "}")
        removed += 1

    if removed:
        path.write_text(text, encoding="utf-8")
        log(f"app.css: rimossi {removed} blocchi di CSS morto "
            f"(controlli checkbox mai usati nell'HTML reale).")
    else:
        log("app.css: nessun blocco morto riconosciuto con i pattern "
            "attesi, controllo manuale consigliato.")


# ---------------------------------------------------------------------
# 3. Workflow: smette di ri-tracciare il database binario
# ---------------------------------------------------------------------
def fix_workflow_sqlite_tracking():
    path = BASE_DIR / ".github" / "workflows" / "update-data.yml"
    if not path.exists():
        log(".github/workflows/update-data.yml non trovato, salto.")
        return

    text = path.read_text(encoding="utf-8")

    old = "          git add data/database/school-intelligence.sqlite docs/data/"
    new = "          git add docs/data/"

    if old not in text:
        if new in text:
            log("Workflow: già corretto, salto.")
        else:
            log("ATTENZIONE: riga 'git add' attesa non trovata nel "
                "workflow, controllo manuale necessario.")
        return

    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    log("Workflow: il database SQLite non verrà più ri-tracciato su Git "
        "ad ogni run automatico (solo docs/data/ viene committato).")


# ---------------------------------------------------------------------
# 4. Rimuove lo stack trace grezzo mostrato agli utenti in produzione
# ---------------------------------------------------------------------
def fix_production_error_display():
    path = BASE_DIR / "docs" / "js" / "app.js"
    text = path.read_text(encoding="utf-8")

    old = '''loadData().catch(error => {

    console.error("SCHOOL INTELLIGENCE RUNTIME ERROR:", error);

    const message = error && error.stack
        ? error.stack
        : String(error);

    $("schoolList").innerHTML = `
        <div class="error" style="white-space:pre-wrap;overflow-wrap:anywhere;">
            <strong>Errore applicazione</strong><br><br>
            ${escapeHtml(message)}
        </div>
    `;
});'''

    new = '''loadData().catch(error => {

    // Il dettaglio tecnico resta in console per chi sta facendo debug;
    // ai visitatori del sito mostriamo solo un messaggio comprensibile,
    // senza esporre lo stack trace interno dell'applicazione.
    console.error("SCHOOL INTELLIGENCE RUNTIME ERROR:", error);

    $("schoolList").innerHTML = `
        <div class="error">
            <strong>Non è stato possibile caricare i dati.</strong><br><br>
            Riprova tra qualche minuto. Se il problema persiste, i dati
            potrebbero essere in fase di aggiornamento.
        </div>
    `;
});'''

    if old not in text:
        if "Non è stato possibile caricare i dati." in text:
            log("app.js: gestione errori già corretta, salto.")
        else:
            log("ATTENZIONE: blocco loadData().catch non trovato come "
                "atteso, controllo manuale necessario.")
        return

    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    log("app.js: in caso di errore i visitatori vedono un messaggio "
        "comprensibile invece dello stack trace tecnico.")


# ---------------------------------------------------------------------
# 5. Archivia lo script fix_school_card.py, ormai usato
# ---------------------------------------------------------------------
def archive_used_scripts():
    src = BASE_DIR / "fix_school_card.py"
    if not src.exists():
        log("fix_school_card.py già assente dalla root, salto.")
        return

    maint_dir = BASE_DIR / "scripts" / "maintenance"
    maint_dir.mkdir(parents=True, exist_ok=True)
    dest = maint_dir / src.name
    src.rename(dest)
    log("fix_school_card.py spostato in scripts/maintenance/ (già applicato).")


def main():
    print("Pulizia definitiva repository school-intelligence")
    print("=" * 60)
    fix_compare_checkbox_overlap()
    clean_dead_checkbox_css()
    fix_workflow_sqlite_tracking()
    fix_production_error_display()
    archive_used_scripts()
    print("=" * 60)
    print("Fatto. Controlla 'git status' e 'git diff' prima di committare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
