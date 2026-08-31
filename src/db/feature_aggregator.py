from pathlib import Path
import sqlite3
import sys


BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "school-intelligence.sqlite"
)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_summary_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS school_feature_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_id INTEGER NOT NULL,
            feature TEXT NOT NULL,

            evidence_count INTEGER NOT NULL DEFAULT 0,
            explicit_count INTEGER NOT NULL DEFAULT 0,
            inferred_count INTEGER NOT NULL DEFAULT 0,
            mention_count INTEGER NOT NULL DEFAULT 0,

            avg_confidence REAL,
            max_confidence REAL,
            status TEXT NOT NULL,

            UNIQUE(school_id, feature)
        )
        """
    )

    conn.commit()


def calculate_status(
    evidence_count,
    explicit_count,
    inferred_count,
    mention_count,
):
    """
    Determina lo stato aggregato della feature.

    Regole:

    VERIFIED
        almeno una evidence EXPLICIT

    PROBABLE
        nessuna EXPLICIT ma almeno una INFERRED

    MENTIONED
        solo MENTION

    UNKNOWN
        fallback difensivo
    """

    if explicit_count > 0:
        return "VERIFIED"

    if inferred_count > 0:
        return "PROBABLE"

    if mention_count > 0:
        return "MENTIONED"

    return "UNKNOWN"


def aggregate(conn):
    rows = conn.execute(
        """
        SELECT
            school_id,
            feature,

            COUNT(*) AS evidence_count,

            SUM(
                CASE
                    WHEN UPPER(TRIM(COALESCE(evidence_type, '')))
                         = 'EXPLICIT'
                    THEN 1
                    ELSE 0
                END
            ) AS explicit_count,

            SUM(
                CASE
                    WHEN UPPER(TRIM(COALESCE(evidence_type, '')))
                         = 'INFERRED'
                    THEN 1
                    ELSE 0
                END
            ) AS inferred_count,

            SUM(
                CASE
                    WHEN UPPER(TRIM(COALESCE(evidence_type, '')))
                         IN ('MENTION', 'MENTIONED')
                    THEN 1
                    ELSE 0
                END
            ) AS mention_count,

            AVG(confidence) AS avg_confidence,
            MAX(confidence) AS max_confidence

        FROM school_features

        WHERE feature IS NOT NULL
          AND TRIM(feature) <> ''

        GROUP BY
            school_id,
            feature

        ORDER BY
            school_id,
            feature
        """
    ).fetchall()

    print(
        f"Gruppi feature trovati: {len(rows)}"
    )

    conn.execute(
        "DELETE FROM school_feature_summary"
    )

    for row in rows:

        evidence_count = int(
            row["evidence_count"] or 0
        )

        explicit_count = int(
            row["explicit_count"] or 0
        )

        inferred_count = int(
            row["inferred_count"] or 0
        )

        mention_count = int(
            row["mention_count"] or 0
        )

        avg_confidence = row["avg_confidence"]
        max_confidence = row["max_confidence"]

        status = calculate_status(
            evidence_count,
            explicit_count,
            inferred_count,
            mention_count,
        )

        conn.execute(
            """
            INSERT INTO school_feature_summary (
                school_id,
                feature,
                evidence_count,
                explicit_count,
                inferred_count,
                mention_count,
                avg_confidence,
                max_confidence,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["school_id"],
                row["feature"],
                evidence_count,
                explicit_count,
                inferred_count,
                mention_count,
                avg_confidence,
                max_confidence,
                status,
            ),
        )

        print(
            f"{row['school_id']:>3} | "
            f"{row['feature']:<25} | "
            f"evidence={evidence_count:>3} | "
            f"100={explicit_count:>3} | "
            f"70={inferred_count:>3} | "
            f"40={mention_count:>3} | "
            f"status={status}"
        )

    conn.commit()

    return len(rows)


def print_summary(conn):
    rows = conn.execute(
        """
        SELECT
            status,
            COUNT(*) AS n
        FROM school_feature_summary
        GROUP BY status
        ORDER BY
            CASE status
                WHEN 'VERIFIED' THEN 1
                WHEN 'PROBABLE' THEN 2
                WHEN 'MENTIONED' THEN 3
                ELSE 4
            END
        """
    ).fetchall()

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for row in rows:
        print(
            f"{row['status']:<12} | {row['n']}"
        )


def main():
    print("=" * 80)
    print("SCHOOL INTELLIGENCE - FEATURE AGGREGATOR")
    print("=" * 80)
    print()
    print(f"Database:")
    print(DB_PATH)
    print()
    print("=" * 80)
    print("AGGREGAZIONE FEATURE")
    print("=" * 80)
    print()

    if not DB_PATH.exists():
        print(
            f"ERRORE: database non trovato: {DB_PATH}",
            file=sys.stderr,
        )
        return 1

    conn = get_connection()

    try:
        ensure_summary_table(conn)

        count = aggregate(conn)

        print_summary(conn)

        print()
        print("=" * 80)
        print("AGGREGAZIONE COMPLETATA")
        print("=" * 80)
        print()
        print(
            f"Feature aggregate create: {count}"
        )

        return 0

    except Exception as exc:
        conn.rollback()

        print()
        print("=" * 80)
        print("ERRORE")
        print("=" * 80)
        print(exc)

        return 1

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
