#!/usr/bin/env python3

from __future__ import annotations

import csv
import io
import re
import sqlite3
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data/database/school-intelligence.sqlite"

CATALOG_URL = (
    "https://dati.istruzione.it/opendata/opendata/catalog/"
    "ALUCORSOINDCLASTA"
)

TABLE = "school_class_enrolment"


def download_latest_csv():
    """
    Usa il CSV MIM ufficiale scaricato manualmente.
    """

    candidates = [
        Path("/storage/emulated/0/Download/ALUCORSOINDCLASTA1788721090076.csv"),
        ROOT / "data/mim/ALUCORSOINDCLASTA1788721090076.csv",
    ]

    for path in candidates:
        if path.exists():
            payload = path.read_bytes()

            if not payload:
                raise RuntimeError(
                    f"Il file MIM è vuoto: {path}"
                )

            print(f"CSV MIM locale: {path}")
            print(f"Dimensione: {len(payload):,} byte")

            return str(path), payload

    raise RuntimeError(
        "CSV MIM non trovato. Percorsi verificati:\n"
        + "\n".join(str(p) for p in candidates)
    )


def normalize_header(value):
    value = str(value or "").strip().lower()
    value = (
        value.replace("à", "a")
        .replace("è", "e")
        .replace("ì", "i")
        .replace("ò", "o")
        .replace("ù", "u")
    )
    value = re.sub(r"[^a-z0-9]", "", value)
    return value


def parse_csv(payload):
    text = payload.decode("utf-8-sig", errors="replace")

    sample = text[:10000]
    dialect = csv.Sniffer().sniff(
        sample,
        delimiters=";,|\t",
    )

    reader = csv.reader(
        io.StringIO(text),
        dialect,
    )

    rows = list(reader)

    if not rows:
        raise RuntimeError("CSV MIM vuoto.")

    headers = [
        normalize_header(x)
        for x in rows[0]
    ]

    index = {
        header: i
        for i, header in enumerate(headers)
    }

    required = {
        "annoscolastico",
        "codicescuola",
        "ordinescuola",
        "annocorsoclasse",
        "classi",
        "alunnimaschi",
        "alunnifemmine",
    }

    missing = required - set(index)

    if missing:
        raise RuntimeError(
            "Colonne MIM mancanti: "
            + ", ".join(sorted(missing))
        )

    data = []

    for row in rows[1:]:
        if not row:
            continue

        def get(name):
            i = index[name]
            return row[i].strip() if i < len(row) else ""

        try:
            course = int(get("annocorsoclasse"))
        except ValueError:
            continue

        # Secondaria di primo grado = 1, 2, 3.
        if course not in (1, 2, 3):
            continue

        school_code = get("codicescuola")
        if not school_code:
            continue

        try:
            classes = int(float(get("classi") or 0))
            males = int(float(get("alunnimaschi") or 0))
            females = int(float(get("alunnifemmine") or 0))
        except ValueError:
            continue

        data.append({
            "school_year": get("annoscolastico"),
            "school_code": school_code,
            "course_year": course,
            "classes": classes,
            "male": males,
            "female": females,
            "students": males + females,
        })

    return data


def ensure_table(conn):
    conn.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            school_code TEXT NOT NULL,
            school_year TEXT NOT NULL,
            course_year INTEGER NOT NULL,
            classes INTEGER NOT NULL DEFAULT 0,
            male INTEGER NOT NULL DEFAULT 0,
            female INTEGER NOT NULL DEFAULT 0,
            students INTEGER NOT NULL DEFAULT 0,
            source_url TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            UNIQUE (
                school_code,
                school_year,
                course_year
            )
        )
        """
    )

    conn.execute(
        f"""
        CREATE INDEX IF NOT EXISTS
        idx_school_class_enrolment_school
        ON {TABLE}(school_id, school_year)
        """
    )


def main():
    print("=" * 80)
    print("MIM — ALUNNI E CLASSI PER ANNO DI CORSO")
    print("=" * 80)

    url, payload = download_latest_csv()
    rows = parse_csv(payload)

    if not rows:
        raise RuntimeError(
            "Il dataset MIM non contiene righe utilizzabili."
        )

    conn = sqlite3.connect(DB_PATH)

    try:
        conn.row_factory = sqlite3.Row
        ensure_table(conn)

        schools = {
            row["codice_scuola"]: row["id"]
            for row in conn.execute(
                """
                SELECT id, codice_scuola
                FROM schools
                WHERE codice_scuola IS NOT NULL
                """
            )
        }

        now = datetime.now(timezone.utc).isoformat()

        imported = 0
        ignored = 0

        for row in rows:
            school_id = schools.get(row["school_code"])

            if school_id is None:
                ignored += 1
                continue

            conn.execute(
                f"""
                INSERT INTO {TABLE} (
                    school_id,
                    school_code,
                    school_year,
                    course_year,
                    classes,
                    male,
                    female,
                    students,
                    source_url,
                    retrieved_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (
                    school_code,
                    school_year,
                    course_year
                )
                DO UPDATE SET
                    school_id = excluded.school_id,
                    classes = excluded.classes,
                    male = excluded.male,
                    female = excluded.female,
                    students = excluded.students,
                    source_url = excluded.source_url,
                    retrieved_at = excluded.retrieved_at
                """,
                (
                    school_id,
                    row["school_code"],
                    row["school_year"],
                    row["course_year"],
                    row["classes"],
                    row["male"],
                    row["female"],
                    row["students"],
                    url,
                    now,
                ),
            )

            imported += 1

        conn.commit()

        count = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE}"
        ).fetchone()[0]

        schools_count = conn.execute(
            f"SELECT COUNT(DISTINCT school_id) FROM {TABLE}"
        ).fetchone()[0]

        print()
        print(f"Righe importate : {imported}")
        print(f"Righe ignorate  : {ignored}")
        print(f"Record DB        : {count}")
        print(f"Scuole coperte  : {schools_count}")
        print(f"Fonte            : {url}")
        print()
        print("IMPORT MIM COMPLETATO")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
