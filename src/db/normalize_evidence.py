from pathlib import Path
import sqlite3
from datetime import datetime, timezone

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
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        cur = conn.cursor()

        # -----------------------------------------------------------------
        # 1. VERIFICA MODELLO ATTUALE
        # -----------------------------------------------------------------

        cur.execute("PRAGMA table_info(school_features)")
        schema = cur.fetchall()

        if not schema:
            print()
            print("ERRORE: tabella school_features non trovata.")
            return 1

        columns = [row["name"] for row in schema]

        print()
        print("COLONNE SCHOOL_FEATURES:")

        for column in columns:
            print(" -", column)

        required = [
            "school_id",
            "feature",
            "confidence",
            "evidence_type",
        ]

        missing = [
            column
            for column in required
            if column not in columns
        ]

        if missing:
            print()
            print(
                "ERRORE: colonne mancanti:",
                ", ".join(missing),
            )
            return 1

        # -----------------------------------------------------------------
        # 2. LEGGI LE EVIDENZE ATTUALI
        # -----------------------------------------------------------------

        select = [
            "id",
            "school_id",
            "feature",
            "confidence",
            "evidence_type",
        ]

        for column in (
            "value",
            "normalized_value",
            "document_id",
            "source_id",
            "evidence",
            "verified_at",
        ):
            if column in columns:
                select.append(column)

        rows = cur.execute(
            f"""
            SELECT {", ".join(select)}
            FROM school_features
            WHERE school_id IS NOT NULL
              AND feature IS NOT NULL
            ORDER BY id
            """
        ).fetchall()

        print()
        print("EVIDENCE RAW:", len(rows))

        if not rows:
            print()
            print("ATTENZIONE: nessuna evidence da normalizzare.")
            return 0

        # -----------------------------------------------------------------
        # 3. NORMALIZZAZIONE IN PLACE
        # -----------------------------------------------------------------

        now = datetime.now(timezone.utc).isoformat()

        normalized = 0

        for row in rows:
            feature = normalize_text(row["feature"])

            if feature:
                feature = feature.upper()

            value = (
                normalize_text(row["value"])
                if "value" in row.keys()
                else None
            )

            normalized_value = (
                normalize_text(row["normalized_value"])
                if "normalized_value" in row.keys()
                else None
            )

            evidence_type = normalize_text(
                row["evidence_type"]
            )

            if evidence_type:
                evidence_type = evidence_type.upper()
            else:
                evidence_type = "INFERRED"

            try:
                confidence = int(row["confidence"] or 0)
            except (TypeError, ValueError):
                confidence = 0

            if confidence < 0:
                confidence = 0

            if confidence > 100:
                confidence = 100

            updates = [
                "feature = ?",
                "confidence = ?",
                "evidence_type = ?",
            ]

            params = [
                feature,
                confidence,
                evidence_type,
            ]

            if "normalized_value" in columns:
                if normalized_value is None and value is not None:
                    normalized_value = value

                updates.append("normalized_value = ?")
                params.append(normalized_value)

            if "verified_at" in columns:
                updates.append(
                    "verified_at = COALESCE(verified_at, ?)"
                )
                params.append(now)

            params.append(row["id"])

            cur.execute(
                f"""
                UPDATE school_features
                SET {", ".join(updates)}
                WHERE id = ?
                """,
                params,
            )

            normalized += 1

        conn.commit()

        # -----------------------------------------------------------------
        # 4. REPORT FINALE
        # -----------------------------------------------------------------

        cur.execute(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(DISTINCT school_id) AS schools,
                COUNT(DISTINCT feature) AS features
            FROM school_features
            """
        )

        summary = cur.fetchone()

        print()
        print("=" * 80)
        print("NORMALIZZAZIONE COMPLETATA")
        print("=" * 80)
        print()
        print("Evidence normalizzate :", normalized)
        print("Evidence totali       :", summary["total"])
        print("Scuole coinvolte      :", summary["schools"])
        print("Feature distinte      :", summary["features"])
        print()
        print("Nota: tutte le evidence individuali sono state conservate.")
        print("=" * 80)

        return 0

    except Exception as exc:
        conn.rollback()
        print()
        print("ERRORE NORMALIZZATORE:", exc)
        return 1

    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
