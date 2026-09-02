import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB = Path("data/database/school-intelligence.sqlite")
OUT = Path("docs/data/school_profiles.json")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

conn.execute("""
CREATE TABLE IF NOT EXISTS school_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    school_id INTEGER NOT NULL UNIQUE,
    principal_name TEXT,
    enrolment_status TEXT,
    enrolment_school_year TEXT,
    enrolment_open_from TEXT,
    enrolment_open_until TEXT,
    principal_source_id INTEGER,
    principal_evidence_id INTEGER,
    enrolment_source_id INTEGER,
    enrolment_evidence_id INTEGER,
    updated_at TEXT NOT NULL
)
""")

now = datetime.now().isoformat(timespec="seconds")

schools = conn.execute("""
    SELECT id, denominazione, codice_scuola, comune, provincia, website
    FROM schools
    ORDER BY id
""").fetchall()

for school in schools:
    conn.execute("""
        INSERT OR IGNORE INTO school_profile
        (school_id, updated_at)
        VALUES (?, ?)
    """, (school["id"], now))

conn.commit()

rows = conn.execute("""
    SELECT
        sp.school_id,
        s.denominazione,
        s.codice_scuola,
        s.comune,
        s.provincia,
        s.website,
        sp.principal_name,
        sp.enrolment_status,
        sp.enrolment_school_year,
        sp.enrolment_open_from,
        sp.enrolment_open_until,
        sp.principal_source_id,
        sp.principal_evidence_id,
        sp.enrolment_source_id,
        sp.enrolment_evidence_id,
        sp.updated_at
    FROM school_profile sp
    JOIN schools s ON s.id = sp.school_id
    ORDER BY s.id
""").fetchall()

profiles = []

for r in rows:
    profiles.append({
        "school_id": r["school_id"],
        "denominazione": r["denominazione"],
        "codice_scuola": r["codice_scuola"],
        "comune": r["comune"],
        "provincia": r["provincia"],
        "website": r["website"],
        "principal": {
            "name": r["principal_name"],
            "source_id": r["principal_source_id"],
            "evidence_id": r["principal_evidence_id"]
        },
        "enrolment": {
            "status": r["enrolment_status"],
            "school_year": r["enrolment_school_year"],
            "open_from": r["enrolment_open_from"],
            "open_until": r["enrolment_open_until"],
            "source_id": r["enrolment_source_id"],
            "evidence_id": r["enrolment_evidence_id"]
        },
        "updated_at": r["updated_at"]
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    json.dumps(profiles, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print()
print("======================================")
print(" SCHOOL PROFILE")
print("======================================")
print("Scuole:", len(profiles))
print("Profili creati:", len(profiles))
print("Dirigenti valorizzati: 0")
print("Iscrizioni valorizzate: 0")
print("Export:", OUT)
print("======================================")

conn.close()
