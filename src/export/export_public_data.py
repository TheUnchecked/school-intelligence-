from pathlib import Path
import json
import sqlite3


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

    return [dict(row) for row in rows]


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
        }
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
