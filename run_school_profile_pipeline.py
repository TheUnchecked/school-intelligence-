"""
Pipeline unica per school_profile:
  1. Reset dei campi derivati (evita dati sporchi da run precedenti)
  2. Collega sources -> school_profile (dirigenti + iscrizioni)
  3. Esporta docs/data/school_profiles.json

Uso:
    python run_school_profile_pipeline.py
"""

import json
import re
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "database" / "school-intelligence.sqlite"
OUT_PATH = BASE_DIR / "docs" / "data" / "school_profiles.json"

NAME_SPLIT_RE = re.compile(r"\s[-\u2013\u2014]\s")

ENROLMENT_WINDOW = {
    "status": "CLOSED",
    "school_year": "2026/2027",
    "open_from": "2026-01-13",
    "open_until": "2026-02-14",
}


def extract_principal_name(title):
    if not title:
        return None
    parts = NAME_SPLIT_RE.split(title, maxsplit=1)
    if len(parts) != 2:
        return None
    return parts[1].strip() or None


def reset_profile(conn):
    conn.execute("""
        UPDATE school_profile
        SET principal_name = NULL,
            principal_source_id = NULL,
            enrolment_status = NULL,
            enrolment_school_year = NULL,
            enrolment_open_from = NULL,
            enrolment_open_until = NULL,
            enrolment_source_id = NULL
    """)


def link_principals(conn):
    rows = conn.execute("""
        SELECT id, school_id, title FROM sources
        WHERE title LIKE 'Dirigente scolastico%'
        ORDER BY school_id, id
    """).fetchall()

    updated, skipped = 0, []
    for row in rows:
        name = extract_principal_name(row["title"])
        if not name:
            skipped.append((row["id"], row["school_id"], row["title"]))
            continue
        conn.execute("""
            UPDATE school_profile
            SET principal_name = ?, principal_source_id = ?
            WHERE school_id = ?
        """, (name, row["id"], row["school_id"]))
        updated += 1
    return updated, skipped


def link_enrolments(conn):
    rows = conn.execute("""
        SELECT id, school_id FROM sources
        WHERE title LIKE 'MIM %Iscrizioni%'
        ORDER BY school_id, id
    """).fetchall()

    for row in rows:
        conn.execute("""
            UPDATE school_profile
            SET enrolment_status = ?, enrolment_school_year = ?,
                enrolment_open_from = ?, enrolment_open_until = ?,
                enrolment_source_id = ?
            WHERE school_id = ?
        """, (
            ENROLMENT_WINDOW["status"], ENROLMENT_WINDOW["school_year"],
            ENROLMENT_WINDOW["open_from"], ENROLMENT_WINDOW["open_until"],
            row["id"], row["school_id"],
        ))
    return len(rows)


def source_dict(conn, source_id):
    if source_id is None:
        return None
    row = conn.execute("""
        SELECT id, url, title, retrieved_at, status FROM sources WHERE id = ?
    """, (source_id,)).fetchone()
    if row is None:
        return None
    return dict(row)


def export_json(conn):
    rows = conn.execute("""
        SELECT s.id AS school_id, s.denominazione, s.codice_scuola, s.comune,
               s.provincia, s.website, sp.principal_name, sp.principal_source_id,
               sp.enrolment_status, sp.enrolment_school_year,
               sp.enrolment_open_from, sp.enrolment_open_until,
               sp.enrolment_source_id, sp.updated_at
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
    OUT_PATH.write_text(json.dumps(profiles, ensure_ascii=False, indent=2), encoding="utf-8")
    return profiles


def main():
    if not DB_PATH.exists():
        print(f"ERRORE: database non trovato: {DB_PATH}")
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        reset_profile(conn)
        principals, skipped = link_principals(conn)
        enrolments = link_enrolments(conn)
        conn.commit()

        profiles = export_json(conn)

        print("=" * 60)
        print("PIPELINE SCHOOL_PROFILE")
        print("=" * 60)
        print(f"Scuole totali:        {len(profiles)}")
        print(f"Dirigenti collegati:  {principals}")
        print(f"Iscrizioni collegate: {enrolments}")
        print(f"Titoli non riconosciuti: {len(skipped)}")
        print(f"Export: {OUT_PATH}")

        if skipped:
            print("\nDa controllare a mano:")
            for source_id, school_id, title in skipped:
                print(f"  source_id={source_id} school_id={school_id} title={title!r}")

        return 0

    except sqlite3.Error as exc:
        print(f"ERRORE database: {exc}")
        conn.rollback()
        return 1
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
