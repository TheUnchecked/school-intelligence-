from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import sqlite3
import re


BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "school-intelligence.sqlite"
)


def normalize_url(url):
    """
    Normalizza una URL eliminando:
    - query string
    - fragment
    - slash finali
    """
    if not url:
        return ""

    try:
        parts = urlsplit(url.strip())

        return urlunsplit(
            (
                parts.scheme.lower(),
                parts.netloc.lower(),
                parts.path.rstrip("/"),
                "",
                "",
            )
        )

    except Exception:
        return url.strip().lower()


def url_filename(url):
    """
    Estrae il filename dalla URL.
    """
    if not url:
        return ""

    try:
        path = urlsplit(url).path

        return Path(path).name.strip().lower()

    except Exception:
        return ""


def normalize_filename(name):
    """
    Normalizza filename per confronti robusti.
    """
    if not name:
        return ""

    name = str(name).lower()

    name = re.sub(
        r"\.(pdf|PDF)$",
        "",
        name
    )

    name = re.sub(
        r"[^a-z0-9]+",
        "",
        name
    )

    return name


def load_sources(conn):
    """
    Carica tutte le sources e costruisce indici.
    """

    rows = conn.execute(
        """
        SELECT
            id,
            school_id,
            source_type,
            url,
            title,
            local_path
        FROM sources
        ORDER BY school_id, id
        """
    ).fetchall()

    exact = {}
    normalized = {}
    filename = {}

    for row in rows:

        source_id = row["id"]
        school_id = row["school_id"]
        url = row["url"]

        # -----------------------------------------------------
        # URL ESATTA
        # -----------------------------------------------------

        if url:

            key = (
                school_id,
                url.strip()
            )

            exact.setdefault(
                key,
                []
            ).append(source_id)

        # -----------------------------------------------------
        # URL NORMALIZZATA
        # -----------------------------------------------------

        norm = normalize_url(url)

        if norm:

            key = (
                school_id,
                norm
            )

            normalized.setdefault(
                key,
                []
            ).append(source_id)

        # -----------------------------------------------------
        # FILENAME
        # -----------------------------------------------------

        fname = normalize_filename(
            url_filename(url)
        )

        if fname:

            key = (
                school_id,
                fname
            )

            filename.setdefault(
                key,
                []
            ).append(source_id)

    return {
        "exact": exact,
        "normalized": normalized,
        "filename": filename,
    }


def choose_unique(mapping, key):
    """
    Restituisce un source_id solo quando il match è univoco.
    """
    candidates = mapping.get(key, [])

    if len(candidates) == 1:
        return candidates[0]

    return None


def find_source(document, indexes):
    """
    Cerca la source associata al documento.

    Strategia:

    1. URL esatta
    2. URL normalizzata
    3. filename normalizzato

    Restituisce:

        source_id
        match_type

    oppure:

        None
        None
    """

    school_id = document["school_id"]
    url = document["url"]

    # =========================================================
    # 1. EXACT URL
    # =========================================================

    source_id = choose_unique(
        indexes["exact"],
        (
            school_id,
            url.strip() if url else ""
        )
    )

    if source_id:
        return source_id, "EXACT_URL"

    # =========================================================
    # 2. NORMALIZED URL
    # =========================================================

    norm = normalize_url(url)

    source_id = choose_unique(
        indexes["normalized"],
        (
            school_id,
            norm
        )
    )

    if source_id:
        return source_id, "NORMALIZED_URL"

    # =========================================================
    # 3. FILENAME
    # =========================================================

    fname = normalize_filename(
        url_filename(url)
    )

    source_id = choose_unique(
        indexes["filename"],
        (
            school_id,
            fname
        )
    )

    if source_id:
        return source_id, "FILENAME"

    return None, None


def main():

    print("=" * 80)
    print("SCHOOL INTELLIGENCE - SOURCE PROVENANCE BACKFILL")
    print("=" * 80)

    print()
    print("Database:")
    print(DB_PATH)

    if not DB_PATH.exists():

        print()
        print("ERRORE: database non trovato.")
        sys_exit = 1
        raise SystemExit(sys_exit)

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    try:

        # =====================================================
        # VERIFICA TABELLE
        # =====================================================

        tables = {
            row["name"]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                """
            ).fetchall()
        }

        required = {
            "sources",
            "ptof_documents",
            "school_features",
        }

        missing_tables = required - tables

        if missing_tables:

            print()
            print(
                "ERRORE: tabelle mancanti:",
                ", ".join(
                    sorted(missing_tables)
                )
            )

            return

        # =====================================================
        # CARICA DATI
        # =====================================================

        documents = conn.execute(
            """
            SELECT
                id,
                school_id,
                url,
                title
            FROM ptof_documents
            WHERE url IS NOT NULL
              AND TRIM(url) <> ''
            ORDER BY school_id, id
            """
        ).fetchall()

        indexes = load_sources(conn)

        source_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM sources
            """
        ).fetchone()[0]

        evidence_count = conn.execute(
            """
            SELECT COUNT(*)
            FROM school_features
            """
        ).fetchone()[0]

        already_linked = conn.execute(
            """
            SELECT COUNT(*)
            FROM school_features
            WHERE source_id IS NOT NULL
            """
        ).fetchone()[0]

        print()
        print(
            f"Sources disponibili : {source_count}"
        )

        print(
            f"Documenti PTOF     : {len(documents)}"
        )

        print(
            f"Evidence totali    : {evidence_count}"
        )

        print(
            f"Evidence già linkate: {already_linked}"
        )

        # =====================================================
        # BACKUP LOGICO
        # =====================================================

        print()
        print("Analisi matching...")
        print()

        document_matches = {}

        exact_matches = 0
        normalized_matches = 0
        filename_matches = 0
        missing_matches = 0

        ambiguous = []

        for index, document in enumerate(
            documents,
            start=1
        ):

            source_id, match_type = find_source(
                document,
                indexes
            )

            document_matches[
                document["id"]
            ] = source_id

            if match_type == "EXACT_URL":
                exact_matches += 1

            elif match_type == "NORMALIZED_URL":
                normalized_matches += 1

            elif match_type == "FILENAME":
                filename_matches += 1

            else:
                missing_matches += 1

                ambiguous.append(
                    (
                        document["id"],
                        document["school_id"],
                        document["url"],
                    )
                )

            if index % 10 == 0:

                print(
                    f"Processati: "
                    f"{index}/{len(documents)}"
                )

        # =====================================================
        # REPORT DOCUMENTI
        # =====================================================

        matched_documents = sum(
            1
            for value in document_matches.values()
            if value is not None
        )

        print()
        print("=" * 80)
        print("DOCUMENT MATCHING")
        print("=" * 80)

        print()
        print(
            f"Documenti totali       : {len(documents)}"
        )

        print(
            f"Match totali           : {matched_documents}"
        )

        print(
            f"  Exact URL            : {exact_matches}"
        )

        print(
            f"  Normalized URL       : {normalized_matches}"
        )

        print(
            f"  Filename             : {filename_matches}"
        )

        print(
            f"  Missing              : {missing_matches}"
        )

        # =====================================================
        # PROPAGAZIONE SOURCE_ID
        # =====================================================

        updates = 0

        print()
        print("Aggiornamento school_features...")

        conn.execute(
            "BEGIN"
        )

        try:

            for document_id, source_id in document_matches.items():

                if source_id is None:
                    continue

                cur = conn.execute(
                    """
                    UPDATE school_features
                    SET source_id = ?
                    WHERE document_id = ?
                      AND source_id IS NULL
                    """,
                    (
                        source_id,
                        document_id,
                    )
                )

                updates += cur.rowcount

            conn.commit()

        except Exception:

            conn.rollback()
            raise

        # =====================================================
        # RISULTATO FINALE
        # =====================================================

        final_linked = conn.execute(
            """
            SELECT COUNT(*)
            FROM school_features
            WHERE source_id IS NOT NULL
            """
        ).fetchone()[0]

        final_missing = conn.execute(
            """
            SELECT COUNT(*)
            FROM school_features
            WHERE source_id IS NULL
            """
        ).fetchone()[0]

        print()
        print("=" * 80)
        print("BACKFILL SOURCE PROVENANCE COMPLETATO")
        print("=" * 80)

        print()
        print(
            f"Evidence totali       : {evidence_count}"
        )

        print(
            f"Source ID aggiornati  : {updates}"
        )

        print(
            f"Evidence con source   : {final_linked}"
        )

        print(
            f"Evidence senza source : {final_missing}"
        )

        # =====================================================
        # MATCH PER SCUOLA
        # =====================================================

        print()
        print("=" * 80)
        print("PROVENANCE PER SCUOLA")
        print("=" * 80)

        rows = conn.execute(
            """
            SELECT
                s.id,
                s.denominazione,

                (
                    SELECT COUNT(*)
                    FROM school_features sf
                    WHERE sf.school_id = s.id
                ) AS evidence,

                (
                    SELECT COUNT(*)
                    FROM school_features sf
                    WHERE sf.school_id = s.id
                      AND sf.source_id IS NOT NULL
                ) AS linked_sources

            FROM schools s

            WHERE EXISTS (
                SELECT 1
                FROM school_features sf
                WHERE sf.school_id = s.id
            )

            ORDER BY s.id
            """
        ).fetchall()

        print()

        for row in rows:

            print(
                f"{row['id']:>3} | "
                f"{row['denominazione']:<40} | "
                f"evidence={row['evidence']:>4} | "
                f"linked={row['linked_sources']:>4}"
            )

        # =====================================================
        # DOCUMENTI SENZA SOURCE
        # =====================================================

        if ambiguous:

            print()
            print("=" * 80)
            print("DOCUMENTI SENZA MATCH")
            print("=" * 80)

            print()

            for (
                document_id,
                school_id,
                url,
            ) in ambiguous:

                print(
                    f"document_id={document_id} "
                    f"school_id={school_id}"
                )

                print(
                    f"URL: {url}"
                )

                print()

        else:

            print()
            print(
                "Tutti i documenti hanno un source match univoco."
            )

    finally:

        conn.close()


if __name__ == "__main__":
    main()
