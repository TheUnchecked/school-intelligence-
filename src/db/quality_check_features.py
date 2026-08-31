from pathlib import Path
import sqlite3
from collections import defaultdict


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "data" / "database" / "school-intelligence.sqlite"


def main():

    print("=" * 80)
    print("SCHOOL INTELLIGENCE - FEATURE QUALITY CHECK")
    print("=" * 80)
    print()
    print(f"Database: {DB_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # ------------------------------------------------------------------
    # 1. Totale evidence
    # ------------------------------------------------------------------

    total = conn.execute(
        "SELECT COUNT(*) FROM school_features"
    ).fetchone()[0]

    print(f"Evidence totali: {total}")
    print()

    # ------------------------------------------------------------------
    # 2. Scuole con evidence
    # ------------------------------------------------------------------

    print("-" * 80)
    print("SCUOLE")
    print("-" * 80)

    rows = conn.execute(
        """
        SELECT
            s.id,
            s.codice_scuola,
            s.denominazione,
            s.comune,
            COUNT(sf.id) AS evidence
        FROM schools s
        LEFT JOIN school_features sf
            ON sf.school_id = s.id
        GROUP BY s.id
        ORDER BY evidence DESC, s.comune, s.codice_scuola
        """
    ).fetchall()

    for row in rows:
        print(
            f"{row['codice_scuola']:15} | "
            f"{row['comune']:20} | "
            f"{row['evidence']:4} evidence | "
            f"{row['denominazione']}"
        )

    print()

    # ------------------------------------------------------------------
    # 3. Distribuzione confidence
    # ------------------------------------------------------------------

    print("-" * 80)
    print("CONFIDENCE")
    print("-" * 80)

    rows = conn.execute(
        """
        SELECT
            confidence,
            COUNT(*) AS totale
        FROM school_features
        GROUP BY confidence
        ORDER BY confidence DESC
        """
    ).fetchall()

    for row in rows:
        print(
            f"confidence {row['confidence']:>5} | "
            f"{row['totale']:4} evidence"
        )

    print()

    # ------------------------------------------------------------------
    # 4. Feature per scuola
    # ------------------------------------------------------------------

    print("-" * 80)
    print("FEATURE PER SCUOLA")
    print("-" * 80)

    rows = conn.execute(
        """
        SELECT
            s.codice_scuola,
            sf.feature,
            COUNT(*) AS totale,
            MAX(sf.confidence) AS max_confidence,
            ROUND(AVG(sf.confidence), 1) AS avg_confidence
        FROM school_features sf
        JOIN schools s
            ON s.id = sf.school_id
        GROUP BY sf.school_id, sf.feature
        ORDER BY s.codice_scuola, sf.feature
        """
    ).fetchall()

    current_school = None

    for row in rows:

        if row["codice_scuola"] != current_school:
            current_school = row["codice_scuola"]
            print()
            print(f"[{current_school}]")

        print(
            f"  {row['feature']:25} "
            f"n={row['totale']:2} "
            f"max={row['max_confidence']:5.1f} "
            f"avg={row['avg_confidence']:5.1f}"
        )

    print()

    # ------------------------------------------------------------------
    # 5. Duplicate evidence
    # ------------------------------------------------------------------

    print("-" * 80)
    print("DUPLICATE EVIDENCE")
    print("-" * 80)

    duplicates = conn.execute(
        """
        SELECT
            school_id,
            feature,
            evidence,
            COUNT(*) AS totale
        FROM school_features
        GROUP BY school_id, feature, evidence
        HAVING COUNT(*) > 1
        ORDER BY totale DESC
        LIMIT 30
        """
    ).fetchall()

    if not duplicates:
        print("Nessun duplicato trovato.")

    else:
        for row in duplicates:
            print(
                f"school_id={row['school_id']} | "
                f"{row['feature']:25} | "
                f"duplicati={row['totale']}"
            )

    print()

    # ------------------------------------------------------------------
    # 6. Feature sospette
    # ------------------------------------------------------------------

    print("-" * 80)
    print("FEATURE SOSPETTE")
    print("-" * 80)

    suspicious = conn.execute(
        """
        SELECT
            s.codice_scuola,
            sf.feature,
            sf.confidence,
            sf.evidence
        FROM school_features sf
        JOIN schools s
            ON s.id = sf.school_id
        WHERE
            sf.confidence = 100
            AND length(sf.evidence) > 500
        ORDER BY s.codice_scuola, sf.feature
        LIMIT 50
        """
    ).fetchall()

    for row in suspicious:

        evidence = " ".join(row["evidence"].split())

        if len(evidence) > 250:
            evidence = evidence[:250] + "..."

        print(
            f"{row['codice_scuola']} | "
            f"{row['feature']} | "
            f"{row['confidence']}\n"
            f"  {evidence}\n"
        )

    # ------------------------------------------------------------------
    # 7. Feature globali
    # ------------------------------------------------------------------

    print("-" * 80)
    print("FEATURE GLOBALI")
    print("-" * 80)

    rows = conn.execute(
        """
        SELECT
            feature,
            COUNT(*) AS totale,
            COUNT(DISTINCT school_id) AS scuole,
            SUM(
                CASE
                    WHEN confidence = 100 THEN 1
                    ELSE 0
                END
            ) AS explicit
        FROM school_features
        GROUP BY feature
        ORDER BY scuole DESC, feature
        """
    ).fetchall()

    for row in rows:
        print(
            f"{row['feature']:25} | "
            f"evidence={row['totale']:3} | "
            f"scuole={row['scuole']:2} | "
            f"confidence100={row['explicit']:3}"
        )

    print()
    print("=" * 80)
    print("QUALITY CHECK COMPLETATO")
    print("=" * 80)

    conn.close()


if __name__ == "__main__":
    main()

