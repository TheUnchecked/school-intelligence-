from pathlib import Path
import sqlite3
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "school-intelligence.sqlite"
)


LEVEL_PRIORITY = {
    "EXPLICIT": 3,
    "MENTION": 2,
    "INFERRED": 1,
}


def normalize_text(value):

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def first_existing(columns, candidates):

    for candidate in candidates:

        if candidate in columns:
            return candidate

    return None


def main():

    print("=" * 80)
    print("SCHOOL INTELLIGENCE - EVIDENCE NORMALIZER")
    print("=" * 80)

    print()
    print("Database:")
    print(DB_PATH)

    if not DB_PATH.exists():

        print()
        print("ERRORE: database non trovato.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()

    # ---------------------------------------------------------
    # 1. VERIFICA TABELLA EVIDENCE
    # ---------------------------------------------------------

    cur.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'evidence'
    """)

    if cur.fetchone() is None:

        print()
        print("ERRORE: tabella evidence non trovata.")

        conn.close()
        return

    # ---------------------------------------------------------
    # 2. LEGGI LO SCHEMA
    # ---------------------------------------------------------

    cur.execute("PRAGMA table_info(evidence)")

    schema = cur.fetchall()

    columns = [
        row["name"]
        for row in schema
    ]

    print()
    print("COLONNE EVIDENCE:")

    for column in columns:
        print(" -", column)

    # ---------------------------------------------------------
    # 3. TROVA LE COLONNE
    # ---------------------------------------------------------

    school_col = first_existing(
        columns,
        [
            "school_id",
            "school",
        ],
    )

    feature_col = first_existing(
        columns,
        [
            "feature",
            "evidence_type",
            "type",
        ],
    )

    value_col = first_existing(
        columns,
        [
            "value",
            "evidence_value",
        ],
    )

    level_col = first_existing(
        columns,
        [
            "evidence_level",
            "level",
            "classification",
        ],
    )

    confidence_col = first_existing(
        columns,
        [
            "confidence",
            "confidence_score",
        ],
    )

    text_col = first_existing(
        columns,
        [
            "source_text",
            "text",
            "snippet",
            "evidence",
        ],
    )

    document_col = first_existing(
        columns,
        [
            "document_id",
            "source_document_id",
            "ptof_document_id",
        ],
    )

    print()
    print("MAPPING:")

    print("school_id  :", school_col)
    print("feature    :", feature_col)
    print("value      :", value_col)
    print("level      :", level_col)
    print("confidence :", confidence_col)
    print("text       :", text_col)
    print("document   :", document_col)

    # ---------------------------------------------------------
    # 4. VERIFICA COLONNE MINIME
    # ---------------------------------------------------------

    if not school_col:
        print("ERRORE: manca school_id")
        conn.close()
        return

    if not feature_col:
        print("ERRORE: manca feature")
        conn.close()
        return

    if not level_col:
        print("ERRORE: manca evidence_level")
        conn.close()
        return

    if not confidence_col:
        print("ERRORE: manca confidence")
        conn.close()
        return

    # ---------------------------------------------------------
    # 5. CREA school_features
    # ---------------------------------------------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS school_features (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            school_id INTEGER NOT NULL,

            feature TEXT NOT NULL,

            value TEXT,

            confidence INTEGER NOT NULL DEFAULT 0,

            evidence_level TEXT NOT NULL,

            source_evidence_id INTEGER,

            source_document_id INTEGER,

            source_text TEXT,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL,

            FOREIGN KEY (school_id)
                REFERENCES schools(id)
                ON DELETE CASCADE
        )
    """)

    cur.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_school_features_unique
        ON school_features(
            school_id,
            feature
        )
    """)

    # ---------------------------------------------------------
    # 6. LEGGI LE EVIDENCE
    # ---------------------------------------------------------

    select = [
        f"e.id AS evidence_id",
        f"e.{school_col} AS school_id",
        f"e.{feature_col} AS feature",
        f"e.{level_col} AS evidence_level",
        f"e.{confidence_col} AS confidence",
    ]

    if value_col:
        select.append(
            f"e.{value_col} AS value"
        )
    else:
        select.append(
            "NULL AS value"
        )

    if text_col:
        select.append(
            f"e.{text_col} AS source_text"
        )
    else:
        select.append(
            "NULL AS source_text"
        )

    if document_col:
        select.append(
            f"e.{document_col} AS document_id"
        )
    else:
        select.append(
            "NULL AS document_id"
        )

    query = f"""
        SELECT
            {", ".join(select)}
        FROM evidence e
        WHERE e.{school_col} IS NOT NULL
        AND e.{feature_col} IS NOT NULL
    """

    cur.execute(query)

    rows = cur.fetchall()

    print()
    print("EVIDENCE RAW:", len(rows))

    # ---------------------------------------------------------
    # 7. DEDUPLICAZIONE
    # ---------------------------------------------------------

    best = {}

    for row in rows:

        school_id = row["school_id"]

        feature = normalize_text(
            row["feature"]
        )

        if not feature:
            continue

        feature = feature.upper()

        level = normalize_text(
            row["evidence_level"]
        )

        if level:
            level = level.upper()
        else:
            level = "INFERRED"

        try:
            confidence = int(
                row["confidence"] or 0
            )
        except:
            confidence = 0

        candidate = {
            "evidence_id": row["evidence_id"],
            "school_id": school_id,
            "feature": feature,
            "value": normalize_text(
                row["value"]
            ),
            "level": level,
            "confidence": confidence,
            "source_text": normalize_text(
                row["source_text"]
            ),
            "document_id": row["document_id"],
        }

        key = (
            school_id,
            feature,
        )

        if key not in best:

            best[key] = candidate

            continue

        current = best[key]

        current_rank = (
            LEVEL_PRIORITY.get(
                current["level"],
                0
            ),
            current["confidence"],
            current["evidence_id"],
        )

        candidate_rank = (
            LEVEL_PRIORITY.get(
                candidate["level"],
                0
            ),
            candidate["confidence"],
            candidate["evidence_id"],
        )

        if candidate_rank > current_rank:

            best[key] = candidate

    print(
        "FEATURE UNICHE:",
        len(best)
    )

    print(
        "DUPLICATE ELIMINATE:",
        len(rows) - len(best)
    )

    # ---------------------------------------------------------
    # 8. RICREA DATI NORMALIZZATI
    # ---------------------------------------------------------

    cur.execute("""
        DELETE FROM school_features
    """)

    now = datetime.utcnow().isoformat(
        timespec="seconds"
    )

    for item in best.values():

        cur.execute("""
            INSERT INTO school_features (
                school_id,
                feature,
                value,
                confidence,
                evidence_level,
                source_evidence_id,
                source_document_id,
                source_text,
                created_at,
                updated_at
            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item["school_id"],
            item["feature"],
            item["value"],
            item["confidence"],
            item["level"],
            item["evidence_id"],
            item["document_id"],
            item["source_text"],
            now,
            now,
        ))

    conn.commit()

    # ---------------------------------------------------------
    # 9. REPORT
    # ---------------------------------------------------------

    print()
    print("=" * 80)
    print("FEATURE NORMALIZZATE")
    print("=" * 80)

    cur.execute("""
        SELECT
            feature,
            COUNT(*) AS totale
        FROM school_features
        GROUP BY feature
        ORDER BY totale DESC
    """)

    for row in cur.fetchall():

        print(
            f"{row['feature']:30} "
            f"{row['totale']:4}"
        )

    print()
    print("=" * 80)
    print("LIVELLI")
    print("=" * 80)

    cur.execute("""
        SELECT
            evidence_level,
            COUNT(*) AS totale
        FROM school_features
        GROUP BY evidence_level
    """)

    for row in cur.fetchall():

        print(
            f"{row['evidence_level']:15} "
            f"{row['totale']:4}"
        )

    conn.close()

    print()
    print("=" * 80)
    print("NORMALIZZAZIONE COMPLETATA")
    print("=" * 80)


if __name__ == "__main__":
    main()
