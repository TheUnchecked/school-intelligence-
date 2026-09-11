"""
Tre miglioramenti in un unico script:

  1. PULIZIA CSS: rimuove le riscritture duplicate morte di
     .ranking-card e .comparison-toolbar (stesso problema già
     affrontato altre volte in questo repository — patch successive
     che ridefinivano lo stesso selettore invece di modificare quello
     esistente). Il comportamento visivo non cambia: resta solo la
     versione che vinceva già in cascata.

  2. BADGE NUMERICO: il checkbox "Confronta" di ogni scuola mostra
     ora quante scuole hai già selezionato, aggiornato in tempo reale
     su tutte le card contemporaneamente — non serve più scorrere
     fino alla barra in basso per saperlo.

  3. GRAFICO RADAR: nella scheda scuola, prima dell'elenco dettagliato
     dei 21 parametri, un radar a 5 assi (Lingue, Servizi, Strutture,
     Attività e didattica, Organizzazione) dà un colpo d'occhio
     immediato su dove la scuola è documentata meglio o peggio.
     Il punteggio per categoria pesa gli stati dei parametri:
     Verificato=100%, Probabile=70%, Menzionato=40%, Non rilevato=0%.

Nota: l'anteprima dei risultati filtro NON è in questo script perché,
controllando il codice, esiste già — i filtri aggiornano il conteggio
risultati in tempo reale.

Uso:
    python design_pass_2.py

Da eseguire nella cartella radice del repository. È idempotente.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def log(msg):
    print(f"- {msg}")


# ---------------------------------------------------------------------
# 1. Pulizia CSS duplicato
# ---------------------------------------------------------------------
def clean_duplicate_css():
    path = BASE_DIR / "docs" / "css" / "app.css"
    text = path.read_text(encoding="utf-8")

    changed = False

    # --- Merge position:relative nel blocco canonico di .ranking-card ---
    old_canonical = '''.ranking-card {
    display: block !important;
    width: 100% !important;
    min-width: 0 !important;
    padding: 24px !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    background: var(--surface) !important;
    box-sizing: border-box !important;
    cursor: pointer;
}'''

    new_canonical = '''.ranking-card {
    position: relative;
    display: block !important;
    width: 100% !important;
    min-width: 0 !important;
    padding: 24px !important;
    border: 1px solid var(--line) !important;
    border-radius: 12px !important;
    background: var(--surface) !important;
    box-sizing: border-box !important;
    cursor: pointer;
}'''

    if old_canonical in text:
        text = text.replace(old_canonical, new_canonical)
        changed = True

    old_dup = '''.ranking-card {
    position: relative;
}

.ranking-card.is-selected {
    outline: 2px solid currentColor;
    outline-offset: 2px;
}'''

    new_dup = '''.ranking-card.is-selected {
    outline: 2px solid currentColor;
    outline-offset: 2px;
}'''

    if old_dup in text:
        text = text.replace(old_dup, new_dup)
        changed = True

    old_dup1 = '''.comparison-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 16px;
    margin: 18px 0;
    padding: 15px 18px;
    border: 1px solid var(--border, #ddd);
    border-radius: 14px;
    background: var(--surface, #fff);
}

'''

    if old_dup1 in text:
        text = text.replace(old_dup1, "")
        changed = True

    old_dup2 = '''.comparison-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;

  margin: 18px 0;

  padding: 10px 13px;

  border: 1px solid var(--border-color, #ddd);
  border-radius: 12px;

  background: var(--card-background, #fff);

  box-sizing: border-box;
}

'''

    if old_dup2 in text:
        text = text.replace(old_dup2, "")
        changed = True

    if changed:
        path.write_text(text, encoding="utf-8")
        log("app.css: rimosse le riscritture duplicate di .ranking-card "
            "e .comparison-toolbar.")
    else:
        log("app.css: CSS già pulito, salto.")


# ---------------------------------------------------------------------
# 2. Badge numerico sul checkbox Confronta
# ---------------------------------------------------------------------
def add_compare_badge_js():
    path = BASE_DIR / "docs" / "js" / "app.js"
    text = path.read_text(encoding="utf-8")

    if "compare-count-badge" in text:
        log("app.js: badge Confronta già presente, salto.")
        return

    old_label = '''                    <label class="school-compare-check">

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

                    </label>'''

    new_label = '''                    <label class="school-compare-check">

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

                        <span
                            class="compare-count-badge"
                            ${
                                finalComparisonCount() > 0
                                    ? ""
                                    : "hidden"
                            }
                        >${finalComparisonCount()}</span>

                    </label>'''

    if old_label not in text:
        log("ATTENZIONE: markup checkbox Confronta non trovato come "
            "atteso, controllo manuale necessario in app.js")
        return

    text = text.replace(old_label, new_label)

    old_update = '''  if (countEl) {
    countEl.textContent = `${count}/4 selezionate`;
  }

  button.disabled = count < 2;'''

    new_update = '''  if (countEl) {
    countEl.textContent = `${count}/4 selezionate`;
  }

  document
    .querySelectorAll(".compare-count-badge")
    .forEach(badge => {
      badge.textContent = String(count);
      badge.hidden = count === 0;
    });

  button.disabled = count < 2;'''

    if old_update not in text:
        log("ATTENZIONE: punto di aggiornamento UI confronto non "
            "trovato come atteso, controllo manuale necessario in "
            "app.js")
        return

    text = text.replace(old_update, new_update)
    path.write_text(text, encoding="utf-8")
    log("app.js: badge numerico aggiunto al checkbox Confronta, "
        "sincronizzato su tutte le card.")


def add_compare_badge_css():
    path = BASE_DIR / "docs" / "css" / "app.css"
    text = path.read_text(encoding="utf-8")

    if "BADGE NUMERICO CONFRONTA" in text:
        log("app.css: stile badge già presente, salto.")
        return

    addition = '''

/* ============================================================
   BADGE NUMERICO CONFRONTA
   ============================================================ */

.compare-count-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 16px;
    height: 16px;
    padding: 0 4px;
    margin-left: 2px;

    border-radius: 8px;
    background: var(--accent);
    color: #fff;

    font-size: 0.68rem;
    font-weight: 800;
    line-height: 1;
}
'''

    with path.open("a", encoding="utf-8") as f:
        f.write(addition)

    log("app.css: stile del badge numerico aggiunto.")


# ---------------------------------------------------------------------
# 3. Grafico radar per categoria
# ---------------------------------------------------------------------
def add_radar_js():
    path = BASE_DIR / "docs" / "js" / "app.js"
    text = path.read_text(encoding="utf-8")

    if "function renderRadarChart" in text:
        log("app.js: grafico radar già presente, salto.")
        return

    anchor = '''function parameterMeta(code) {'''

    radar_functions = '''const RADAR_CATEGORIES = [
    "Lingue",
    "Servizi",
    "Strutture",
    "Attività e didattica",
    "Organizzazione"
];

function computeCategoryScores(records) {

    const totals = {};

    RADAR_CATEGORIES.forEach(category => {
        totals[category] = { total: 0, score: 0 };
    });

    records.forEach(record => {

        const category = record.category;

        if (!totals[category]) return;

        totals[category].total++;

        const weight =
            record.status === "VERIFIED" ? 1 :
            record.status === "PROBABLE" ? 0.7 :
            record.status === "MENTIONED" ? 0.4 :
            0;

        totals[category].score += weight;
    });

    return RADAR_CATEGORIES.map(category => {

        const { total, score } = totals[category];

        return {
            category,
            percent:
                total > 0
                    ? Math.round((score / total) * 100)
                    : 0
        };
    });
}

function renderRadarChart(records) {

    const scores = computeCategoryScores(records);
    const n = scores.length;

    const size = 240;
    const center = size / 2;
    const radius = 82;
    const labelRadius = radius + 30;

    const angleFor = (i) =>
        (Math.PI * 2 * i) / n - Math.PI / 2;

    const pointAt = (i, fraction) => {
        const angle = angleFor(i);
        return [
            center + radius * fraction * Math.cos(angle),
            center + radius * fraction * Math.sin(angle)
        ];
    };

    const gridRings = [0.33, 0.66, 1]
        .map(fraction => {
            const points = scores
                .map((_, i) => pointAt(i, fraction).join(","))
                .join(" ");
            return `<polygon points="${points}" fill="none" stroke="var(--line)" stroke-width="1" />`;
        })
        .join("");

    const axisLines = scores
        .map((_, i) => {
            const [x, y] = pointAt(i, 1);
            return `<line x1="${center}" y1="${center}" x2="${x}" y2="${y}" stroke="var(--line)" stroke-width="1" />`;
        })
        .join("");

    const dataPoints = scores
        .map((s, i) => pointAt(i, Math.max(0.04, s.percent / 100)).join(","))
        .join(" ");

    const labels = scores
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
        .join("");

    return `
        <svg viewBox="0 0 ${size} ${size}" class="radar-chart" role="img" aria-label="Punteggio per categoria">
            ${gridRings}
            ${axisLines}
            <polygon points="${dataPoints}" fill="var(--accent)" fill-opacity="0.18" stroke="var(--accent)" stroke-width="2" stroke-linejoin="round" />
            ${labels}
        </svg>
    `;
}


function parameterMeta(code) {'''

    if anchor not in text:
        log("ATTENZIONE: punto di inserimento parameterMeta non "
            "trovato, controllo manuale necessario in app.js")
        return

    text = text.replace(anchor, radar_functions, 1)

    old_insert = '''                <span class="school-information-count">
                    ${records.length}
                </span>

            </div>

            <div class="parameters-container">
                ${parametersHtml}
            </div>

        </section>'''

    new_insert = '''                <span class="school-information-count">
                    ${records.length}
                </span>

            </div>

            <div class="radar-chart-wrap">
                ${renderRadarChart(records)}
            </div>

            <div class="parameters-container">
                ${parametersHtml}
            </div>

        </section>'''

    if old_insert not in text:
        log("ATTENZIONE: punto di inserimento del radar nella scheda "
            "scuola non trovato, controllo manuale necessario in "
            "app.js")
        return

    text = text.replace(old_insert, new_insert)
    path.write_text(text, encoding="utf-8")
    log("app.js: grafico radar aggiunto alla scheda scuola.")


def add_radar_css():
    path = BASE_DIR / "docs" / "css" / "app.css"
    text = path.read_text(encoding="utf-8")

    if "RADAR PER CATEGORIA" in text:
        log("app.css: stile radar già presente, salto.")
        return

    addition = '''

/* ============================================================
   RADAR PER CATEGORIA
   ============================================================ */

.radar-chart-wrap {
    display: flex;
    justify-content: center;
    margin: 8px 0 24px;
}

.radar-chart {
    width: 100%;
    max-width: 320px;
    height: auto;
}

.radar-label {
    font-size: 9px;
    font-weight: 700;
    fill: var(--text);
}

.radar-label-value {
    font-size: 9px;
    fill: var(--accent);
    font-weight: 800;
}

@media (max-width: 700px) {
    .radar-chart {
        max-width: 260px;
    }
}
'''

    with path.open("a", encoding="utf-8") as f:
        f.write(addition)

    log("app.css: stile del radar aggiunto.")


def main():
    print("Pulizia CSS, badge Confronta, grafico radar")
    print("=" * 60)
    clean_duplicate_css()
    add_compare_badge_js()
    add_compare_badge_css()
    add_radar_js()
    add_radar_css()
    print("=" * 60)
    print("Fatto. Controlla il risultato in locale prima di committare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
