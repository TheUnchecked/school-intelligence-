import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "database" / "school-intelligence.sqlite"
OUT_PATH = BASE_DIR / "docs" / "data" / "school_profiles.json"


def source_dict(conn, source_id):
    if source_id is None:
        return None
    row = conn.execute("""
        SELECT id, url, title, retrieved_at, status
        FROM sources
        WHERE id = ?
    """, (source_id,)).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "url": row["url"],
        "title": row["title"],
        "retrieved_at": row["retrieved_at"],
        "status": row["status"],
    }


def main():
    if not DB_PATH.exists():
        print(f"ERRORE: database non trovato: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute("""
        SELECT
            s.id AS school_id,
            s.denominazione,
            s.codice_scuola,
            s.comune,
            s.provincia,
            s.website,
            sp.principal_name,
            sp.principal_source_id,
            sp.enrolment_status,
            sp.enrolment_school_year,
            sp.enrolment_open_from,
            sp.enrolment_open_until,
            sp.enrolment_source_id,
            sp.updated_at
        FROM schools s
        LEFT JOIN school_profile sp ON sp.school_id = s.id
        ORDER BY s.id
    """).fetchall()

    profiles = []
    for r in rows:
        profiles.append({
            "school_id": r["school_id"],
            "codice_scuola": r["codice_scuola"],
            "denominazione": r["denominazione"],
            "comune": r["comune"],
            "provincia": r["provincia"],
            "website": r["website"],
            "principal": {
                "name": r["principal_name"],
                "source": source_dict(conn, r["principal_source_id"]),
            },
            "enrolment": {
                "status": r["enrolment_status"],
                "school_year": r["enrolment_school_year"],
                "open_from": r["enrolment_open_from"],
                "open_until": r["enrolment_open_until"],
                "source": source_dict(conn, r["enrolment_source_id"]),
            },
            "updated_at": r["updated_at"],
        })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps(profiles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with_principal = sum(1 for p in profiles if p["principal"]["name"])
    with_enrolment = sum(1 for p in profiles if p["enrolment"]["status"])

    print("=" * 60)
    print("EXPORT SCHOOL_PROFILES.JSON")
    print("=" * 60)
    print(f"Scuole totali:        {len(profiles)}")
    print(f"Con dirigente:        {with_principal}")
    print(f"Con dati iscrizione:  {with_enrolment}")
    print(f"Output: {OUT_PATH}")

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
