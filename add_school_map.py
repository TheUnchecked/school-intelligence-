"""
Aggiunge una mappa interattiva delle scuole alla home page, usando
Leaflet + tile OpenStreetMap (gratuiti, nessuna chiave API richiesta).

Cosa fa:
  1. Backend (src/export/export_public_data.py): assegna lat/lon ad
     ogni scuola in base al comune. Le scuole nello stesso comune
     vengono disposte in un piccolo cerchio per non sovrapporsi sulla
     mappa (è un badge geografico sul comune, non l'indirizzo esatto
     — per quello serve un servizio di geocodifica vero, non incluso).
  2. Frontend (docs/index.html): aggiunge Leaflet via CDN (con hash di
     integrità SRI ufficiali) e una nuova sezione "Le scuole sulla
     mappa" sopra l'elenco dei risultati.
  3. Frontend (docs/css/app.css): stile del contenitore mappa e dei
     popup dei segnaposto.
  4. Frontend (docs/js/app.js): funzione renderMap() che inizializza
     la mappa, posiziona un segnaposto per scuola con popup (nome,
     comune, punteggio, pulsante "Apri scheda" collegato alla scheda
     dettagliata già esistente).

IMPORTANTE — passo manuale dopo aver eseguito questo script:
   Le coordinate vengono calcolate lato server, quindi vanno
   nell'export pubblico. Serve rigenerare i dati:

       python3 -m src.export.export_public_data

   e poi committare anche il nuovo docs/data/schools.json insieme al
   resto, altrimenti la mappa risulterà vuota (i dati pubblicati non
   avranno ancora lat/lon).

Se in futuro la classifica si estende a comuni diversi dai 6 attuali
(Castelfidardo, Civitanova Marche, Loreto, Osimo, Potenza Picena,
Recanati), aggiungere le nuove coordinate al dizionario
COMUNE_COORDINATES in export_public_data.py — altrimenti quelle
scuole verranno esportate regolarmente ma non appariranno sulla mappa.

Uso:
    python add_school_map.py

Da eseguire nella cartella radice del repository. È idempotente.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def log(msg):
    print(f"- {msg}")


# ---------------------------------------------------------------------
# 1. Backend: coordinate geografiche per ogni scuola
# ---------------------------------------------------------------------
def patch_export_backend():
    path = BASE_DIR / "src" / "export" / "export_public_data.py"
    text = path.read_text(encoding="utf-8")

    if "COMUNE_COORDINATES" in text:
        log("export_public_data.py: già aggiornato, salto.")
        return

    old_import = "from pathlib import Path\nimport json\nimport sqlite3"
    new_import = "from pathlib import Path\nimport json\nimport math\nimport sqlite3"

    if old_import not in text:
        log("ATTENZIONE: blocco import non trovato come atteso in "
            "export_public_data.py, controllo manuale necessario.")
        return

    text = text.replace(old_import, new_import)

    old_func = '''def export_schools(conn):
    rows = conn.execute(
        """
        SELECT
            id,
            school_year,
            sector,
            codice_scuola,
            codice_istituto,
            denominazione,
            denominazione_normalized,
            regione,
            provincia,
            comune,
            comune_normalized,
            indirizzo,
            cap,
            codice_comune,
            tipologia,
            caratteristica,
            website,
            sede_scolastica
        FROM schools
        ORDER BY denominazione
        """
    ).fetchall()

    return [dict(row) for row in rows]'''

    new_func = '''# Coordinate del centro di ogni comune coperto dal dataset.
# Aggiornare quando la classifica si estende a nuovi comuni: la
# scuola risulterebbe altrimenti senza lat/lon e non comparirebbe
# sulla mappa (viene comunque esportata regolarmente nell'elenco).
COMUNE_COORDINATES = {
    "C100": (43.46306, 13.55000),   # Castelfidardo (AN)
    "C770": (43.30700, 13.72060),   # Civitanova Marche (MC)
    "E690": (43.43889, 13.60861),   # Loreto (AN)
    "F632": (43.36700, 13.61700),   # Potenza Picena (MC)
    "G157": (43.48300, 13.48300),   # Osimo (AN)
    "H211": (43.40361, 13.54972),   # Recanati (MC)
}


def attach_coordinates(schools):
    """
    Assegna lat/lon ad ogni scuola. Le scuole nello stesso comune
    vengono disposte in un piccolo cerchio attorno al centro del
    comune (badge geografico, non l'indirizzo esatto) così da non
    sovrapporsi sulla mappa quando sono più di una.
    """

    by_comune = {}

    for school in schools:
        by_comune.setdefault(
            school.get("codice_comune"), []
        ).append(school)

    for codice_comune, group in by_comune.items():
        base = COMUNE_COORDINATES.get(codice_comune)

        if not base:
            for school in group:
                school["lat"] = None
                school["lon"] = None
            continue

        lat0, lon0 = base
        count = len(group)

        ordered = sorted(
            group,
            key=lambda s: s.get("codice_scuola") or ""
        )

        for index, school in enumerate(ordered):

            if count == 1:
                school["lat"] = lat0
                school["lon"] = lon0
                continue

            angle = 2 * math.pi * index / count
            radius_degrees = 0.0035

            school["lat"] = round(
                lat0 + radius_degrees * math.cos(angle), 6
            )
            school["lon"] = round(
                lon0 + (
                    radius_degrees * math.sin(angle)
                    / math.cos(math.radians(lat0))
                ),
                6
            )

    return schools


def export_schools(conn):
    rows = conn.execute(
        """
        SELECT
            id,
            school_year,
            sector,
            codice_scuola,
            codice_istituto,
            denominazione,
            denominazione_normalized,
            regione,
            provincia,
            comune,
            comune_normalized,
            indirizzo,
            cap,
            codice_comune,
            tipologia,
            caratteristica,
            website,
            sede_scolastica
        FROM schools
        ORDER BY denominazione
        """
    ).fetchall()

    schools = [dict(row) for row in rows]

    return attach_coordinates(schools)'''

    if old_func not in text:
        log("ATTENZIONE: funzione export_schools diversa da quella "
            "attesa, controllo manuale necessario in "
            "export_public_data.py")
        return

    text = text.replace(old_func, new_func)
    path.write_text(text, encoding="utf-8")
    log("export_public_data.py: lat/lon aggiunte a ogni scuola esportata.")


# ---------------------------------------------------------------------
# 2. HTML: Leaflet via CDN + sezione mappa
# ---------------------------------------------------------------------
def patch_html():
    path = BASE_DIR / "docs" / "index.html"
    text = path.read_text(encoding="utf-8")

    if "leaflet" in text.lower():
        log("index.html: Leaflet già presente, salto.")
        return

    old_head = '    <link rel="stylesheet" href="css/app.css">\n</head>'
    new_head = '''    <link rel="stylesheet" href="css/app.css">
    <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"
        integrity="sha512-h9FcoyWjHcOcmEVkxOfTLnmZFWIH0iZhZT1H2TbOq55xssQGEJHEaIm+PgoUaZbRvQTNTluNOEfb1ZRy6D3BOw=="
        crossorigin="anonymous"
        referrerpolicy="no-referrer"
    >
</head>'''

    if old_head not in text:
        log("ATTENZIONE: blocco <head> non trovato come atteso in "
            "index.html, controllo manuale necessario.")
        return

    text = text.replace(old_head, new_head)

    old_section = '''<section>

        <div class="section-header">

            <div>
                <span class="eyebrow">
                    RISULTATI
                </span>

                <h2>
                    Le scuole in evidenza
                </h2>

                <p>
                    Classifica costruita sui 21 parametri analizzati.
                </p>
            </div>

            <span id="resultCount">
                —
            </span>

        </div>

        <div id="schoolList" class="school-list"></div>

    </section>'''

    new_section = '''<section>

        <div class="section-header">

            <div>
                <span class="eyebrow">
                    DOVE SI TROVANO
                </span>

                <h2>
                    Le scuole sulla mappa
                </h2>

                <p>
                    Tocca un segnaposto per aprire la scheda della scuola.
                </p>
            </div>

        </div>

        <div id="schoolMap" class="school-map"></div>

    </section>


    <section>

        <div class="section-header">

            <div>
                <span class="eyebrow">
                    RISULTATI
                </span>

                <h2>
                    Le scuole in evidenza
                </h2>

                <p>
                    Classifica costruita sui 21 parametri analizzati.
                </p>
            </div>

            <span id="resultCount">
                —
            </span>

        </div>

        <div id="schoolList" class="school-list"></div>

    </section>'''

    if old_section not in text:
        log("ATTENZIONE: sezione Risultati non trovata come attesa in "
            "index.html, controllo manuale necessario.")
        return

    text = text.replace(old_section, new_section)

    old_script_tag = '<script src="js/app.js?v=20260906-04"></script>'
    new_script_tag = '''<script
    src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"
    integrity="sha512-puJW3E/qXDqYp9IfhAI54BJEaWIfloJ7JWs7OeD5i6ruC9JZL1gERT1wjtwXFlh7CjE7ZJ+/vcRZRkIYIb6p4g=="
    crossorigin="anonymous"
    referrerpolicy="no-referrer"
></script>

<script src="js/app.js?v=20260911-01"></script>'''

    if old_script_tag not in text:
        log("ATTENZIONE: tag <script> di app.js non trovato con la "
            "versione attesa, controllo manuale necessario in "
            "index.html")
        return

    text = text.replace(old_script_tag, new_script_tag)
    path.write_text(text, encoding="utf-8")
    log("index.html: Leaflet aggiunto via CDN, sezione mappa creata.")


# ---------------------------------------------------------------------
# 3. CSS: stile del contenitore mappa e dei popup
# ---------------------------------------------------------------------
def patch_css():
    path = BASE_DIR / "docs" / "css" / "app.css"
    text = path.read_text(encoding="utf-8")

    if ".school-map " in text or ".school-map {" in text:
        log("app.css: stile mappa già presente, salto.")
        return

    addition = '''

/* ============================================================
   MAPPA SCUOLE
   ============================================================ */

.school-map {
    height: 380px;
    width: 100%;
    border-radius: 12px;
    border: 1px solid var(--line);
    overflow: hidden;
}

.school-map-popup {
    font-family: inherit;
    min-width: 180px;
}

.school-map-popup strong {
    display: block;
    font-size: 0.95rem;
    margin-bottom: 4px;
}

.school-map-popup span {
    display: block;
    color: var(--muted);
    font-size: 0.78rem;
    margin-bottom: 8px;
}

.school-map-popup button {
    width: 100%;
    padding: 6px 10px;
    border: 1px solid var(--line);
    border-radius: 8px;
    background: var(--surface);
    cursor: pointer;
    font-size: 0.8rem;
    font-weight: 700;
}

@media (max-width: 700px) {

    .school-map {
        height: 300px;
    }

}
'''

    with path.open("a", encoding="utf-8") as f:
        f.write(addition)

    log("app.css: stile della mappa aggiunto in coda al file.")


# ---------------------------------------------------------------------
# 4. JS: inizializzazione mappa e segnaposto
# ---------------------------------------------------------------------
def patch_js():
    path = BASE_DIR / "docs" / "js" / "app.js"
    text = path.read_text(encoding="utf-8")

    if "function renderMap" in text:
        log("app.js: renderMap() già presente, salto.")
        return

    old = '''let schoolClassEnrolment = [];

const $ = (id) => document.getElementById(id);'''

    new = '''let schoolClassEnrolment = [];
let schoolMap = null;
let schoolMapMarkers = [];

const $ = (id) => document.getElementById(id);


function renderMap() {

    const container = $("schoolMap");

    if (!container || typeof L === "undefined") {
        return;
    }

    const scoreMap = new Map(
        scores.map(s => [s.school_id, s])
    );

    const withCoordinates = schools.filter(
        s => s.lat != null && s.lon != null
    );

    if (!withCoordinates.length) {
        container.innerHTML =
            "<p style=\\"padding:16px;color:var(--muted);\\">" +
            "Coordinate non disponibili per le scuole in elenco." +
            "</p>";
        return;
    }

    if (!schoolMap) {
        schoolMap = L.map(container, {
            scrollWheelZoom: false
        });

        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                maxZoom: 18,
                attribution:
                    "&copy; " +
                    "<a href=\\"https://www.openstreetmap.org/copyright\\">" +
                    "OpenStreetMap</a>"
            }
        ).addTo(schoolMap);
    }

    schoolMapMarkers.forEach(marker => schoolMap.removeLayer(marker));
    schoolMapMarkers = [];

    withCoordinates.forEach(school => {

        const score = scoreMap.get(school.id);

        const scoreText =
            score && Number(score.evidence_count ?? 0) > 0
                ? formatPercent(score.score_percent)
                : "Dati insufficienti";

        const popupHtml = `
            <div class="school-map-popup">
                <strong>${escapeHtml(school.denominazione)}</strong>
                <span>
                    ${escapeHtml(school.comune)} ·
                    ${scoreText}
                </span>
                <button
                    type="button"
                    onclick="showDetail(${school.id})"
                >
                    Apri scheda
                </button>
            </div>
        `;

        const marker =
            L.marker([school.lat, school.lon])
                .addTo(schoolMap)
                .bindPopup(popupHtml);

        schoolMapMarkers.push(marker);
    });

    const bounds = L.featureGroup(schoolMapMarkers).getBounds();
    schoolMap.fitBounds(bounds, { padding: [24, 24] });

    setTimeout(() => schoolMap.invalidateSize(), 150);
}'''

    if old not in text:
        log("ATTENZIONE: punto di inserimento non trovato come atteso "
            "in app.js, controllo manuale necessario.")
        return

    text = text.replace(old, new)

    old_call = '''    populateProvinceFilter();

    renderRanking();
}'''

    new_call = '''    populateProvinceFilter();

    renderRanking();
    renderMap();
}'''

    if old_call not in text:
        log("ATTENZIONE: chiamata a renderRanking() non trovata come "
            "attesa in app.js, controllo manuale necessario.")
        return

    text = text.replace(old_call, new_call)
    path.write_text(text, encoding="utf-8")
    log("app.js: renderMap() aggiunta e collegata al caricamento dati.")


def main():
    print("Aggiunta mappa scuole (Leaflet + OpenStreetMap)")
    print("=" * 60)
    patch_export_backend()
    patch_html()
    patch_css()
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
