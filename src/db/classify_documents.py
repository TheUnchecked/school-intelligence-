from pathlib import Path
import sqlite3
import re


BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "school-intelligence.sqlite"
)


def normalize(text):
    if not text:
        return ""

    text = str(text).lower()

    replacements = {
        "_": " ",
        "-": " ",
        "–": " ",
        "—": " ",
        "/": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def has_year(text, year1, year2):

    return bool(
        re.search(
            rf"\b{year1}\s*(?:\s|/|-)+\s*{year2}\b",
            text
        )
    )


def classify(title, local_path):

    text = normalize(
        f"{title or ''} {local_path or ''}"
    )

    # =========================================================
    # 1. DIRECTIVE
    # =========================================================

    if (
        "atto di indirizzo" in text
        or (
            "atto" in text
            and "indirizzo" in text
        )
    ):

        return (
            "DIRECTIVE",
            "CONTEXT",
            100,
        )

    # =========================================================
    # 2. PROJECTS / ATTIVITÀ
    # Prima di PTOF.
    #
    # Un allegato che contiene "PTOF" nel titolo
    # NON diventa automaticamente un PTOF.
    # =========================================================

    project_keywords = [
        "schede progettuali",
        "ampliamento dell offerta formativa",
        "ampliamento curricolare",
        "iniziative di ampliamento",
        "attività esterne",
        "viaggiando si impara",
        "uscite didattiche",
        "visite guidate",
        "viaggi di istruzione",
    ]

    if any(
        keyword in text
        for keyword in project_keywords
    ):

        return (
            "PROJECTS",
            "SUPPORT",
            70,
        )

    # =========================================================
    # 3. CURRICULUM
    # =========================================================

    if "curricolo" in text:

        return (
            "CURRICULUM",
            "SUPPORT",
            70,
        )

    # =========================================================
    # 4. DOCUMENTI STORICI
    #
    # Solo se l'anno storico è esplicitamente riconoscibile.
    # =========================================================

    historical_years = [
        ("2024", "2025"),
        ("2023", "2024"),
        ("2022", "2025"),
        ("2022", "2023"),
        ("2019", "2022"),
        ("2021", "2022"),
        ("2020", "2021"),
    ]

    for y1, y2 in historical_years:

        if has_year(text, y1, y2):

            return (
                "ARCHIVE",
                "ARCHIVE",
                0,
            )

    # =========================================================
    # 5. PTOF UPDATE
    # =========================================================

    if (
        "ptof" in text
        and "aggiornamento" in text
        and has_year(text, "2025", "2026")
    ):

        return (
            "PTOF_UPDATE",
            "PRIMARY",
            100,
        )

    # =========================================================
    # 6. PTOF PRINCIPALE 2025-2028
    # =========================================================

    if (
        "ptof" in text
        and has_year(text, "2025", "2028")
        and "sintesi" not in text
        and "presentazione" not in text
        and "aggiornamento" not in text
    ):

        return (
            "PTOF",
            "PRIMARY",
            100,
        )

    # =========================================================
    # 7. PTOF 2025/26
    # =========================================================

    if (
        "ptof" in text
        and has_year(text, "2025", "2026")
        and "sintesi" not in text
        and "presentazione" not in text
        and "aggiornamento" not in text
    ):

        return (
            "PTOF",
            "PRIMARY",
            90,
        )

    # =========================================================
    # 8. PTOF SUMMARY
    # =========================================================

    if (
        "ptof" in text
        and "sintesi" in text
    ):

        return (
            "PTOF_SUMMARY",
            "SUPPORT",
            70,
        )

    # =========================================================
    # 9. PTOF PRESENTATION
    # =========================================================

    if (
        "ptof" in text
        and "presentazione" in text
    ):

        return (
            "PTOF_PRESENTATION",
            "SUPPORT",
            60,
        )

    # =========================================================
    # 10. OTHER
    # =========================================================

    return (
        "OTHER",
        "CONTEXT",
        0,
    )


def main():

    if not DB_PATH.exists():

        raise FileNotFoundError(
            f"Database non trovato: {DB_PATH}"
        )

    conn = sqlite3.connect(DB_PATH)

    rows = conn.execute(
        """
        SELECT
            id,
            title,
            local_path
        FROM ptof_documents
        ORDER BY id
        """
    ).fetchall()

    print("=" * 100)
    print("PTOF DOCUMENT CLASSIFIER v3")
    print("=" * 100)

    print(
        f"Documenti: {len(rows)}"
    )

    print()

    for (
        document_id,
        title,
        local_path,
    ) in rows:

        (
            document_type,
            relevance,
            score,
        ) = classify(
            title,
            local_path,
        )

        conn.execute(
            """
            UPDATE ptof_documents
            SET
                document_type = ?,
                relevance = ?,
                relevance_score = ?
            WHERE id = ?
            """,
            (
                document_type,
                relevance,
                score,
                document_id,
            ),
        )

        print(
            f"{document_id:3} | "
            f"{document_type:20} | "
            f"{relevance:10} | "
            f"{score:3} | "
            f"{title}"
        )

    conn.commit()

    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)

    summary = conn.execute(
        """
        SELECT
            document_type,
            relevance,
            COUNT(*)
        FROM ptof_documents
        GROUP BY
            document_type,
            relevance
        ORDER BY
            relevance,
            document_type
        """
    ).fetchall()

    for (
        document_type,
        relevance,
        count,
    ) in summary:

        print(
            f"{document_type:20} "
            f"{relevance:10} "
            f"{count:3}"
        )

    conn.close()


if __name__ == "__main__":
    main()
