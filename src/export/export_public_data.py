from pathlib import Path
import json
import math
import sqlite3
from datetime import datetime, timezone
from xml.sax.saxutils import escape as xml_escape


BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "school-intelligence.sqlite"
)

OUTPUT_DIR = BASE_DIR / "docs" / "data"


def write_json(filename, data):
    path = OUTPUT_DIR / filename

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return path


SITE_BASE_URL = "https://theunchecked.github.io/school-intelligence-/"


def write_sitemap(schools):
    """
    Genera docs/sitemap.xml con la home e un URL per ogni scuola
    (?scuola=CODICE), così i motori di ricerca possono indicizzare
    anche le singole schede, non solo la home.
    """

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    urls = [(SITE_BASE_URL, "1.0")]

    for school in schools:
        codice = school.get("codice_scuola")

        if not codice:
            continue

        url = f"{SITE_BASE_URL}?scuola={xml_escape(codice)}"
        urls.append((url, "0.7"))

    entries = "\n".join(
        f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{today}</lastmod>
    <priority>{priority}</priority>
  </url>"""
        for loc, priority in urls
    )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n"
        "</urlset>\n"
    )

    path = OUTPUT_DIR.parent / "sitemap.xml"
    path.write_text(xml, encoding="utf-8")

    return path


# Coordinate del centro di ogni comune coperto dal dataset.
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

    return attach_coordinates(schools)


def export_parameters(conn):
    rows = conn.execute(
        """
        SELECT
            id,
            code,
            category,
            name,
            description,
            value_type,
            unit,
            allowed_values,
            evidence_policy,
            source_priority,
            scoring_weight,
            active
        FROM parameter_definitions
        WHERE active = 1
        ORDER BY category, id
        """
    ).fetchall()

    return [dict(row) for row in rows]


def export_school_parameters(conn):
    rows = conn.execute(
        """
        SELECT
            sp.id,
            sp.school_id,
            pd.code AS parameter_code,
            pd.category,
            pd.name AS parameter_name,
            sp.value,
            sp.normalized_value,
            sp.value_type,
            sp.confidence,
            sp.status,
            sp.evidence_count,
            sp.primary_evidence_id,
            sp.primary_document_id
        FROM school_parameters sp
        JOIN parameter_definitions pd
            ON pd.id = sp.parameter_id
        WHERE pd.active = 1
        ORDER BY
            sp.school_id,
            pd.category,
            pd.id
        """
    ).fetchall()

    return [dict(row) for row in rows]


def export_school_scores(conn):
    rows = conn.execute(
        """
        SELECT
            ss.school_id,
            s.codice_scuola,
            s.denominazione,
            s.comune,
            s.provincia,
            ss.weighted_score,
            ss.max_possible_score,
            ss.score_percent,
            ss.parameter_count,
            ss.evidence_count,
            ss.verified_count,
            ss.probable_count,
            ss.mentioned_count,
            ss.not_found_count,
            ss.coverage_percent,
            ss.confidence_percent
        FROM school_scores ss
        JOIN schools s
            ON s.id = ss.school_id
        ORDER BY
            ss.score_percent DESC,
            ss.coverage_percent DESC,
            s.denominazione
        """
    ).fetchall()

    return [dict(row) for row in rows]



def export_evidence(conn):
    print("Esportazione evidence...")

    rows = conn.execute("""
        SELECT
            sf.id,
            sf.school_id,
            sf.feature AS parameter_code,
            sf.value,
            sf.normalized_value,
            sf.evidence,
            sf.confidence,
            sf.evidence_type,
            sf.document_id,
            sf.source_id,
            sf.verified_at
        FROM school_features sf
        ORDER BY sf.school_id, sf.feature, sf.id
    """).fetchall()

    data = [dict(row) for row in rows]

    write_json(
        "evidence.json",
        data
    )

    print(f"  evidence.json: {len(data)}")


def export_ptof_documents(conn):
    rows = conn.execute("""
        SELECT
            id,
            school_id,
            school_year,
            url,
            title,
            status,
            document_date,
            pages,
            document_type,
            relevance,
            relevance_score,
            source_key,
            version_number,
            is_current
        FROM ptof_documents
        ORDER BY
            school_id,
            source_key,
            version_number DESC,
            relevance_score DESC,
            id
    """).fetchall()

    columns = [
        "id",
        "school_id",
        "school_year",
        "url",
        "title",
        "status",
        "document_date",
        "pages",
        "document_type",
        "relevance",
        "relevance_score",
        "source_key",
        "version_number",
        "is_current",
    ]

    data = []

    for row in rows:
        item = dict(zip(columns, row))
        item["is_latest"] = bool(item["is_current"])
        data.append(item)

    return data



def export_school_class_enrolment(conn):
    # La tabella esiste solo dopo che qualcuno ha importato a mano un
    # CSV MIM (src.collectors.mim_class_enrolment): non fa parte della
    # pipeline automatica. Sul runner GitHub, dove il database viene
    # ricostruito da zero ad ogni run, la tabella non c'è quasi mai:
    # in quel caso ritorniamo None per dire "non toccare il file
    # pubblicato", invece di sovrascriverlo con dati vuoti.
    table_exists = conn.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name = 'school_class_enrolment'
        """
    ).fetchone()

    if not table_exists:
        return None

    rows = conn.execute(
        """
        SELECT
            e.school_id,
            e.school_code,
            e.school_year,
            e.course_year,
            e.classes,
            e.male,
            e.female,
            e.students,
            e.source_url,
            e.retrieved_at
        FROM school_class_enrolment e
        ORDER BY
            e.school_id,
            e.school_year DESC,
            e.course_year
        """
    ).fetchall()

    return [dict(row) for row in rows]


def export_statistics(conn):
    schools = conn.execute(
        "SELECT COUNT(*) FROM schools"
    ).fetchone()[0]

    documents = conn.execute(
        "SELECT COUNT(*) FROM ptof_documents"
    ).fetchone()[0]

    evidence = conn.execute(
        "SELECT COUNT(*) FROM school_features"
    ).fetchone()[0]

    parameters = conn.execute(
        """
        SELECT COUNT(*)
        FROM parameter_definitions
        WHERE active = 1
        """
    ).fetchone()[0]

    school_parameters = conn.execute(
        "SELECT COUNT(*) FROM school_parameters"
    ).fetchone()[0]

    verified = conn.execute(
        """
        SELECT COUNT(*)
        FROM school_parameters
        WHERE status = 'VERIFIED'
        """
    ).fetchone()[0]

    probable = conn.execute(
        """
        SELECT COUNT(*)
        FROM school_parameters
        WHERE status = 'PROBABLE'
        """
    ).fetchone()[0]

    mentioned = conn.execute(
        """
        SELECT COUNT(*)
        FROM school_parameters
        WHERE status = 'MENTIONED'
        """
    ).fetchone()[0]

    not_found = conn.execute(
        """
        SELECT COUNT(*)
        FROM school_parameters
        WHERE status = 'NOT_FOUND'
        """
    ).fetchone()[0]

    return {
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
    }


def main():
    print("=" * 80)
    print("SCHOOL INTELLIGENCE - PUBLIC DATA EXPORT")
    print("=" * 80)

    if not DB_PATH.exists():
        print()
        print("ERRORE: database non trovato.")
        return 1

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        print()
        print("Database:", DB_PATH)
        print("Output  :", OUTPUT_DIR)

        print()
        print("Esportazione schools...")

        schools = export_schools(conn)
        write_json(
            "schools.json",
            schools
        )

        print(
            f"  schools.json: {len(schools)}"
        )

        sitemap_path = write_sitemap(schools)
        print(
            f"  sitemap.xml: {len(schools) + 1} URL "
            f"({sitemap_path.name})"
        )

        print()
        print("Esportazione parameters...")

        parameters = export_parameters(conn)
        write_json(
            "parameters.json",
            parameters
        )

        print(
            f"  parameters.json: {len(parameters)}"
        )

        print()
        print("Esportazione school parameters...")

        school_parameters = export_school_parameters(conn)
        write_json(
            "school_parameters.json",
            school_parameters
        )

        print(
            f"  school_parameters.json: "
            f"{len(school_parameters)}"
        )

        print()
        print("Esportazione school scores...")

        school_scores = export_school_scores(conn)
        write_json(
            "school_scores.json",
            school_scores
        )

        print(
            f"  school_scores.json: "
            f"{len(school_scores)}"
        )

        print()
        print("Esportazione evidence...")

        evidence = export_evidence(conn)

        print()
        print("Esportazione PTOF...")

        ptof_documents = export_ptof_documents(conn)

        write_json(
            "ptof_documents.json",
            ptof_documents
        )

        print(
            f"  ptof_documents.json: "
            f"{len(ptof_documents)}"
        )

        print()
        print("Esportazione classi/alunni MIM...")

        class_enrolment = export_school_class_enrolment(conn)

        if class_enrolment is None:
            # manteniamo i dati già pubblicati: nessuna tabella in
            # questo run, quindi non tocchiamo il file esistente.
            print(
                "  school_class_enrolment.json: tabella assente, "
                "file esistente lasciato invariato"
            )
        else:
            write_json(
                "school_class_enrolment.json",
                class_enrolment
            )

            print(
                f"  school_class_enrolment.json: "
                f"{len(class_enrolment)}"
            )

        print()
        print("Esportazione statistics...")

        statistics = export_statistics(conn)
        write_json(
            "statistics.json",
            statistics
        )

        print(
            "  statistics.json: OK"
        )

        print()
        print("=" * 80)
        print("PUBLIC DATA EXPORT COMPLETATO")
        print("=" * 80)

        print()
        print(
            f"Scuole             : "
            f"{statistics['schools']}"
        )

        print(
            f"Documenti          : "
            f"{statistics['documents']}"
        )

        print(
            f"Evidence           : "
            f"{statistics['evidence']}"
        )

        print(
            f"Parametri attivi   : "
            f"{statistics['active_parameters']}"
        )

        print(
            f"School parameters  : "
            f"{statistics['school_parameters']}"
        )

        print()
        print("File generati:")

        for path in sorted(OUTPUT_DIR.glob("*.json")):
            print(
                f"  {path.name:30} "
                f"{path.stat().st_size:,} bytes"
            )

        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
