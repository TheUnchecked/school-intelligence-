from pathlib import Path
import sqlite3
import re
import sys


BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "school-intelligence.sqlite"
)


# =============================================================================
# TEXT NORMALIZATION
# =============================================================================

def normalize_text(value):
    if value is None:
        return ""

    text = str(value).lower()

    text = text.replace("\xa0", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def normalize_for_match(value):
    """
    Normalizzazione più aggressiva utilizzata esclusivamente
    per il matching del testo.

    Manteniamo comunque il testo originale nel database.
    """

    text = normalize_text(value)

    if not text:
        return ""

    text = re.sub(
        r"[^\w\sàèéìòù]",
        " ",
        text,
        flags=re.UNICODE
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =============================================================================
# DOCUMENTS
# =============================================================================

def load_documents(conn):

    rows = conn.execute(
        """
        SELECT
            id,
            school_id,
            title,
            local_path
        FROM ptof_documents
        WHERE local_path IS NOT NULL
          AND TRIM(local_path) <> ''
        ORDER BY school_id, id
        """
    ).fetchall()

    documents = []

    for row in rows:

        pdf_path = Path(
            row["local_path"]
        )

        txt_path = pdf_path.with_suffix(".txt")

        text = ""

        if txt_path.exists():

            try:

                text = txt_path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

            except Exception:

                text = ""

        normalized_text = normalize_text(
            text
        )

        normalized_match_text = normalize_for_match(
            text
        )

        documents.append(
            {
                "id": row["id"],
                "school_id": row["school_id"],
                "title": row["title"] or "",
                "local_path": row["local_path"],
                "txt_path": str(txt_path),
                "text": text,
                "normalized_text": normalized_text,
                "normalized_match_text": normalized_match_text,
            }
        )

    return documents


# =============================================================================
# MATCHING
# =============================================================================

def build_probes(evidence):

    evidence_norm = normalize_text(
        evidence
    )

    if not evidence_norm:
        return []

    words = evidence_norm.split()

    probes = []

    # -----------------------------------------------------------------
    # 1. Evidence completa
    # -----------------------------------------------------------------

    if len(evidence_norm) >= 20:

        probes.append(
            (
                "EXACT",
                evidence_norm
            )
        )

    # -----------------------------------------------------------------
    # 2. Prime 12 parole
    # -----------------------------------------------------------------

    if len(words) >= 12:

        probes.append(
            (
                "PREFIX_12",
                " ".join(words[:12])
            )
        )

    # -----------------------------------------------------------------
    # 3. Prime 8 parole
    # -----------------------------------------------------------------

    if len(words) >= 8:

        probes.append(
            (
                "PREFIX_8",
                " ".join(words[:8])
            )
        )

    # -----------------------------------------------------------------
    # 4. Ultime 8 parole
    # -----------------------------------------------------------------

    if len(words) >= 8:

        probes.append(
            (
                "SUFFIX_8",
                " ".join(words[-8:])
            )
        )

    # -----------------------------------------------------------------
    # 5. Finestra centrale
    # -----------------------------------------------------------------

    if len(words) >= 16:

        start = max(
            0,
            (len(words) // 2) - 4
        )

        probes.append(
            (
                "MIDDLE_8",
                " ".join(
                    words[start:start + 8]
                )
            )
        )

    return probes


def find_document_for_evidence(
    evidence,
    school_id,
    documents
):

    evidence_norm = normalize_text(
        evidence
    )

    if not evidence_norm:
        return None

    evidence_match = normalize_for_match(
        evidence
    )

    if not evidence_match:
        return None

    school_documents = [
        d
        for d in documents
        if d["school_id"] == school_id
    ]

    if not school_documents:
        return None

    # =================================================================
    # STRATEGIA 1
    # Match esatto sul testo normalizzato.
    # =================================================================

    for document in school_documents:

        if not document["normalized_text"]:
            continue

        if evidence_norm in document["normalized_text"]:

            return document["id"]

    # =================================================================
    # STRATEGIA 2
    # Match esatto sulla normalizzazione aggressiva.
    # =================================================================

    for document in school_documents:

        document_text = document[
            "normalized_match_text"
        ]

        if not document_text:
            continue

        if evidence_match in document_text:

            return document["id"]

    # =================================================================
    # STRATEGIA 3
    # Probe progressivi.
    # =================================================================

    probes = build_probes(
        evidence
    )

    for strategy, probe in probes:

        probe_match = normalize_for_match(
            probe
        )

        if not probe_match:
            continue

        # Evitiamo probe troppo corti.
        if len(probe_match) < 40:
            continue

        matches = []

        for document in school_documents:

            document_text = document[
                "normalized_match_text"
            ]

            if not document_text:
                continue

            if probe_match in document_text:

                matches.append(
                    document["id"]
                )

        # Un solo documento candidato = match affidabile.
        if len(matches) == 1:

            return matches[0]

        # Più documenti candidati:
        # non facciamo una scelta arbitraria.
        if len(matches) > 1:

            continue

    return None


# =============================================================================
# SOURCE MAP
# =============================================================================

def build_source_map(conn):

    rows = conn.execute(
        """
        SELECT
            id,
            school_id,
            url
        FROM sources
        """
    ).fetchall()

    return {
        (
            row["school_id"],
            row["url"]
        ): row["id"]
        for row in rows
    }


def update_source_ids(conn):

    rows = conn.execute(
        """
        SELECT
            sf.id,
            sf.school_id,
            sf.document_id,
            pd.url
        FROM school_features sf
        JOIN ptof_documents pd
            ON pd.id = sf.document_id
        WHERE sf.document_id IS NOT NULL
          AND sf.source_id IS NULL
        """
    ).fetchall()

    updated = 0

    for row in rows:

        source = conn.execute(
            """
            SELECT id
            FROM sources
            WHERE school_id = ?
              AND url = ?
            LIMIT 1
            """,
            (
                row["school_id"],
                row["url"],
            ),
        ).fetchone()

        if source:

            conn.execute(
                """
                UPDATE school_features
                SET source_id = ?
                WHERE id = ?
                """,
                (
                    source["id"],
                    row["id"],
                ),
            )

            updated += 1

    conn.commit()

    return updated


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("=" * 80)
    print("SCHOOL INTELLIGENCE - PROVENANCE BACKFILL")
    print("=" * 80)

    if not DB_PATH.exists():

        print(
            "ERRORE: database non trovato."
        )

        return 1

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    try:

        # -------------------------------------------------------------
        # CHECK SCHEMA
        # -------------------------------------------------------------

        columns = [
            row["name"]
            for row in conn.execute(
                "PRAGMA table_info(school_features)"
            ).fetchall()
        ]

        if "document_id" not in columns:

            print(
                "ERRORE: document_id non presente."
            )

            return 1

        # -------------------------------------------------------------
        # COUNTS
        # -------------------------------------------------------------

        total = conn.execute(
            """
            SELECT COUNT(*)
            FROM school_features
            """
        ).fetchone()[0]

        already = conn.execute(
            """
            SELECT COUNT(*)
            FROM school_features
            WHERE document_id IS NOT NULL
            """
        ).fetchone()[0]

        missing_before = (
            total - already
        )

        print()
        print(
            "Evidence totali      :",
            total
        )

        print(
            "Con document_id      :",
            already
        )

        print(
            "Da collegare         :",
            missing_before
        )

        # -------------------------------------------------------------
        # DOCUMENTS
        # -------------------------------------------------------------

        documents = load_documents(
            conn
        )

        print()
        print(
            "Documenti disponibili:",
            len(documents)
        )

        # -------------------------------------------------------------
        # DOCUMENTS WITH TEXT
        # -------------------------------------------------------------

        documents_with_text = sum(
            1
            for d in documents
            if d["normalized_text"]
        )

        print(
            "Documenti con TXT    :",
            documents_with_text
        )

        # -------------------------------------------------------------
        # BACKFILL
        # -------------------------------------------------------------

        rows = conn.execute(
            """
            SELECT
                id,
                school_id,
                feature,
                evidence
            FROM school_features
            WHERE document_id IS NULL
            ORDER BY school_id, id
            """
        ).fetchall()

        matched = 0
        unmatched = 0

        for index, row in enumerate(
            rows,
            start=1
        ):

            document_id = find_document_for_evidence(
                row["evidence"],
                row["school_id"],
                documents
            )

            if document_id is not None:

                conn.execute(
                    """
                    UPDATE school_features
                    SET document_id = ?
                    WHERE id = ?
                    """,
                    (
                        document_id,
                        row["id"],
                    ),
                )

                matched += 1

            else:

                unmatched += 1

            if (
                index % 25 == 0
                or index == len(rows)
            ):

                print(
                    f"Processate: {index}/{len(rows)} "
                    f"| match={matched} "
                    f"| missing={unmatched}"
                )

        conn.commit()

        # -------------------------------------------------------------
        # SOURCE_ID
        # -------------------------------------------------------------

        print()
        print(
            "Aggiornamento source_id..."
        )

        source_updates = update_source_ids(
            conn
        )

        # -------------------------------------------------------------
        # FINAL COUNTS
        # -------------------------------------------------------------

        linked = conn.execute(
            """
            SELECT COUNT(*)
            FROM school_features
            WHERE document_id IS NOT NULL
            """
        ).fetchone()[0]

        missing = conn.execute(
            """
            SELECT COUNT(*)
            FROM school_features
            WHERE document_id IS NULL
            """
        ).fetchone()[0]

        sources = conn.execute(
            """
            SELECT COUNT(*)
            FROM school_features
            WHERE source_id IS NOT NULL
            """
        ).fetchone()[0]

        # -------------------------------------------------------------
        # FINAL
        # -------------------------------------------------------------

        print()
        print("=" * 80)
        print("BACKFILL COMPLETATO")
        print("=" * 80)

        print()
        print(
            "Evidence totali       :",
            total
        )

        print(
            "Già collegate         :",
            already
        )

        print(
            "Nuovi match           :",
            matched
        )

        print(
            "Documenti collegati   :",
            linked
        )

        print(
            "Documenti mancanti    :",
            missing
        )

        print(
            "Source ID collegati   :",
            sources
        )

        print(
            "Source ID aggiornati  :",
            source_updates
        )

        # -------------------------------------------------------------
        # STATUS
        # -------------------------------------------------------------

        print()

        if missing == 0:

            print(
                "STATUS: OK - provenance completa."
            )

            return 0

        if matched > 0:

            print(
                "STATUS: PARTIAL - alcuni record "
                "restano senza document_id."
            )

            return 0

        print(
            "STATUS: NO MATCH - nessun nuovo "
            "document_id collegato."
        )

        return 0

    finally:

        conn.close()


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
