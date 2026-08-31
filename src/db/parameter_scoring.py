from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "school-intelligence.sqlite"
)


STATUS_FACTOR = {
    "VERIFIED": 1.00,
    "PROBABLE": 0.70,
    "MENTIONED": 0.40,
    "NOT_FOUND": 0.00,
}


def calculate_parameter_score(status, confidence, weight):
    """
    Calcola il contributo normalizzato di un parametro.

    Il valore finale è compreso tra 0 e 1.
    """

    factor = STATUS_FACTOR.get(status, 0.0)

    confidence_factor = 0.0

    if confidence is not None:
        confidence_factor = max(
            0.0,
            min(float(confidence) / 100.0, 1.0)
        )

    return factor * confidence_factor * float(weight)


def build_scores(conn):
    """
    Costruisce/aggiorna la tabella school_parameter_scores.
    """

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS school_parameter_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            school_id INTEGER NOT NULL,
            parameter_id INTEGER NOT NULL,

            status TEXT NOT NULL,

            confidence REAL NOT NULL DEFAULT 0,
            scoring_weight REAL NOT NULL DEFAULT 1.0,

            raw_score REAL NOT NULL DEFAULT 0,
            normalized_score REAL NOT NULL DEFAULT 0,

            evidence_count INTEGER NOT NULL DEFAULT 0,

            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (school_id)
                REFERENCES schools(id)
                ON DELETE CASCADE,

            FOREIGN KEY (parameter_id)
                REFERENCES parameter_definitions(id)
                ON DELETE CASCADE,

            UNIQUE (
                school_id,
                parameter_id
            )
        )
        """
    )

    rows = conn.execute(
        """
        SELECT
            sp.school_id,
            sp.parameter_id,
            sp.status,
            sp.confidence,
            sp.evidence_count,
            pd.scoring_weight
        FROM school_parameters sp
        JOIN parameter_definitions pd
            ON pd.id = sp.parameter_id
        WHERE pd.active = 1
        ORDER BY
            sp.school_id,
            sp.parameter_id
        """
    ).fetchall()

    conn.execute(
        """
        DELETE FROM school_parameter_scores
        """
    )

    for row in rows:

        weight = float(row["scoring_weight"] or 1.0)

        raw_score = calculate_parameter_score(
            row["status"],
            row["confidence"],
            weight,
        )

        normalized_score = (
            raw_score / weight
            if weight > 0
            else 0.0
        )

        conn.execute(
            """
            INSERT INTO school_parameter_scores (
                school_id,
                parameter_id,
                status,
                confidence,
                scoring_weight,
                raw_score,
                normalized_score,
                evidence_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["school_id"],
                row["parameter_id"],
                row["status"],
                row["confidence"] or 0.0,
                weight,
                raw_score,
                normalized_score,
                row["evidence_count"] or 0,
            )
        )

    conn.commit()

    return len(rows)


def build_school_scores(conn):
    """
    Costruisce il punteggio complessivo per scuola.

    Il denominatore considera esclusivamente i parametri attivi.
    NOT_FOUND contribuisce zero ma rimane nel denominatore:
    quindi la coverage influenza il risultato.
    """

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS school_scores (
            school_id INTEGER PRIMARY KEY,

            weighted_score REAL NOT NULL DEFAULT 0,
            max_possible_score REAL NOT NULL DEFAULT 0,

            score_percent REAL NOT NULL DEFAULT 0,

            parameter_count INTEGER NOT NULL DEFAULT 0,
            evidence_count INTEGER NOT NULL DEFAULT 0,

            verified_count INTEGER NOT NULL DEFAULT 0,
            probable_count INTEGER NOT NULL DEFAULT 0,
            mentioned_count INTEGER NOT NULL DEFAULT 0,
            not_found_count INTEGER NOT NULL DEFAULT 0,

            coverage_percent REAL NOT NULL DEFAULT 0,
            confidence_percent REAL NOT NULL DEFAULT 0,

            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (school_id)
                REFERENCES schools(id)
                ON DELETE CASCADE
        )
        """
    )

    conn.execute(
        """
        DELETE FROM school_scores
        """
    )

    rows = conn.execute(
        """
        SELECT
            school_id,

            SUM(raw_score) AS weighted_score,

            SUM(scoring_weight) AS max_possible_score,

            COUNT(*) AS parameter_count,

            SUM(evidence_count) AS evidence_count,

            SUM(
                CASE
                    WHEN status = 'VERIFIED'
                    THEN 1 ELSE 0
                END
            ) AS verified_count,

            SUM(
                CASE
                    WHEN status = 'PROBABLE'
                    THEN 1 ELSE 0
                END
            ) AS probable_count,

            SUM(
                CASE
                    WHEN status = 'MENTIONED'
                    THEN 1 ELSE 0
                END
            ) AS mentioned_count,

            SUM(
                CASE
                    WHEN status = 'NOT_FOUND'
                    THEN 1 ELSE 0
                END
            ) AS not_found_count,

            AVG(
                CASE
                    WHEN status != 'NOT_FOUND'
                    THEN confidence
                END
            ) AS confidence_percent

        FROM school_parameter_scores
        GROUP BY school_id
        ORDER BY school_id
        """
    ).fetchall()

    for row in rows:

        weighted_score = float(
            row["weighted_score"] or 0.0
        )

        max_possible_score = float(
            row["max_possible_score"] or 0.0
        )

        score_percent = (
            weighted_score / max_possible_score * 100.0
            if max_possible_score > 0
            else 0.0
        )

        parameter_count = int(
            row["parameter_count"] or 0
        )

        not_found_count = int(
            row["not_found_count"] or 0
        )

        known_count = (
            parameter_count - not_found_count
        )

        coverage_percent = (
            known_count / parameter_count * 100.0
            if parameter_count > 0
            else 0.0
        )

        conn.execute(
            """
            INSERT INTO school_scores (
                school_id,
                weighted_score,
                max_possible_score,
                score_percent,
                parameter_count,
                evidence_count,
                verified_count,
                probable_count,
                mentioned_count,
                not_found_count,
                coverage_percent,
                confidence_percent
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["school_id"],
                weighted_score,
                max_possible_score,
                score_percent,
                parameter_count,
                row["evidence_count"] or 0,
                row["verified_count"] or 0,
                row["probable_count"] or 0,
                row["mentioned_count"] or 0,
                not_found_count,
                coverage_percent,
                row["confidence_percent"] or 0.0,
            )
        )

    conn.commit()

    return len(rows)


def main():

    print("=" * 80)
    print("SCHOOL INTELLIGENCE - PARAMETER SCORING")
    print("=" * 80)

    if not DB_PATH.exists():
        print()
        print("ERRORE: database non trovato.")
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:

        print()
        print("Costruzione parameter scores...")

        parameter_rows = build_scores(conn)

        print(
            f"Righe school_parameter_scores: "
            f"{parameter_rows}"
        )

        print()
        print("Costruzione school scores...")

        school_rows = build_school_scores(conn)

        print(
            f"Righe school_scores: "
            f"{school_rows}"
        )

        print()
        print("=" * 80)
        print("SCHOOL SCORES")
        print("=" * 80)

        rows = conn.execute(
            """
            SELECT
                s.codice_scuola,
                s.denominazione,
                ss.score_percent,
                ss.coverage_percent,
                ss.confidence_percent,
                ss.verified_count,
                ss.probable_count,
                ss.mentioned_count,
                ss.not_found_count
            FROM school_scores ss
            JOIN schools s
                ON s.id = ss.school_id
            ORDER BY
                ss.score_percent DESC,
                ss.coverage_percent DESC,
                s.denominazione
            """
        ).fetchall()

        print()

        for row in rows:

            print(
                f"{row['codice_scuola']:14} | "
                f"{row['score_percent']:6.1f}% | "
                f"coverage={row['coverage_percent']:5.1f}% | "
                f"confidence={row['confidence_percent']:5.1f}% | "
                f"V={row['verified_count']:2} "
                f"P={row['probable_count']:2} "
                f"M={row['mentioned_count']:2} "
                f"N={row['not_found_count']:2} | "
                f"{row['denominazione']}"
            )

        print()
        print("=" * 80)
        print("PARAMETER SCORING COMPLETATO")
        print("=" * 80)

        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
