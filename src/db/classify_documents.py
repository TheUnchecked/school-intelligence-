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
        "’": " ",
        "‘": " ",
        "'": " ",
        ":": " ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

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

    # =========================================================
    # IMPORTANTE
    #
    # La classificazione semantica usa SOLO il titolo.
    # local_path non deve influenzare il document_type.
    # =========================================================

    text = normalize(title)

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
        "progetti di ampliamento",
        "progetti ampliamento",
    ]

    if any(keyword in text for keyword in project_keywords):
        return (
            "PROJECTS",
            "SUPPORT",
            70,
        )

    # =========================================================
    # 3. DOCUMENTI DI SUPPORTO
    #
    # Non sono PTOF, anche quando contengono anni 2025-2028
    # o riferimenti al PTOF.
    # =========================================================

    support_keywords = [
        "piano triennale formazione",
        "piano annuale per l inclusione",
        "piano annuale inclusione",
        "piano d istituto scuola digitale",
        "piano di istituto scuola digitale",
        "protocollo per l inclusione",
        "protocollo inclusione",
    ]

    if any(keyword in text for keyword in support_keywords):
        return (
            "OTHER",
            "SUPPORT",
            50,
        )

    # =========================================================
    # 4. CURRICULUM
    # =========================================================

    if "curricolo" in text:
        return (
            "CURRICULUM",
            "SUPPORT",
            70,
        )

    # =========================================================
    # 5. PTOF SUMMARY
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
    # 6. PTOF PRESENTATION
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
    # 7. PTOF DRAFT / PREDISPOSIZIONE
    #
    # Un PTOF in predisposizione non è il PTOF definitivo.
    # =========================================================

    if (
        "ptof" in text
        and (
            "predisposizione" in text
            or "bozza" in text
            or "draft" in text
        )
    ):
        return (
            "PTOF_DRAFT",
            "SUPPORT",
            80,
        )

    # =========================================================
    # 8. PTOF UPDATE
    #
    # Deve essere PTOF + aggiornamento.
    # Questa regola viene prima dello storico.
    # =========================================================

    if (
        "ptof" in text
        and "aggiornamento" in text
        and (
            has_year(text, "2025", "2026")
            or has_year(text, "2025", "2028")
        )
    ):
        return (
            "PTOF_UPDATE",
            "PRIMARY",
            100,
        )

    # =========================================================
    # 9. DOCUMENTI STORICI
    #
    # Riconosce:
    #
    #   2016-2019
    #   2019-2022
    #   2022-2025
    #   2024-2025
    #   2019/20-2021/22
    #
    # Non considera storico il triennio corrente 2025-2028.
    # =========================================================

    historical = False

    # Intervalli completi: 2016-2019, 2022-2025, ecc.
    full_ranges = re.findall(
        r"\b(20\d{2})\s*(?:-|/)\s*(20\d{2})\b",
        text,
    )

    for start_year, end_year in full_ranges:
        if int(end_year) < 2028:
            historical = True
            break

    # Intervalli scolastici abbreviati:
    # 2019/20-2021/22
    if not historical:
        abbreviated_ranges = re.findall(
            r"\b(20\d{2})\s*/\s*(\d{2})\s*-\s*(20\d{2})\s*/\s*(\d{2})\b",
            text,
        )

        for start_year, start_short, end_year, end_short in abbreviated_ranges:
            if int(end_year) < 2028:
                historical = True
                break

    if historical:
        return (
            "ARCHIVE",
            "ARCHIVE",
            0,
        )

    # =========================================================
    # 10. PTOF PRINCIPALE 2025-2028
    # =========================================================

    if (
        "ptof" in text
        and has_year(text, "2025", "2028")
    ):
        return (
            "PTOF",
            "PRIMARY",
            100,
        )

    # =========================================================
    # 11. PTOF 2025/2026
    # =========================================================

    if (
        "ptof" in text
        and has_year(text, "2025", "2026")
    ):
        return (
            "PTOF",
            "PRIMARY",
            90,
        )

    # =========================================================
    # 12. OTHER
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
