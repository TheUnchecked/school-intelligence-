from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse
import hashlib
import re
import sqlite3
import time

import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "school-intelligence.sqlite"
)

DOCUMENT_DIR = (
    BASE_DIR
    / "data"
    / "documents"
    / "ptof"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; SchoolIntelligence/0.1)"
    )
}


def clean_url(url):
    """Rimuove querystring e fragment."""

    parsed = urlparse(url)

    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            "",
            "",
            "",
        )
    )


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def filename_from_url(url):
    name = Path(
        urlparse(url).path
    ).name

    if not name:
        name = "document.pdf"

    return name


def document_score(text, url):

    combined = (
        f"{text} {url}"
        .lower()
    )

    score = 0

    # PTOF
    if "ptof" in combined:
        score += 100

    # Piano triennale
    if "piano triennale" in combined:
        score += 80

    # Offerta formativa
    if "offerta formativa" in combined:
        score += 60

    # Anno corrente
    if "2025/2026" in combined:
        score += 80

    if "2025-2026" in combined:
        score += 80

    if "2025_2026" in combined:
        score += 80

    if "2025-2028" in combined:
        score += 80

    if "2025/2028" in combined:
        score += 80

    # PDF
    if url.lower().endswith(".pdf"):
        score += 30

    # Documenti particolarmente utili
    if "aggiornamento" in combined:
        score += 30

    if "presentazione" in combined:
        score += 10

    if "schede" in combined:
        score += 10

    # Documenti storici
    for year in [
        "2022",
        "2023",
        "2024",
        "2019",
        "2020",
        "2021",
    ]:
        if year in combined:
            score -= 20

    return score


def is_pdf(response, url):

    content_type = (
        response.headers
        .get(
            "Content-Type",
            "",
        )
        .lower()
    )

    if "application/pdf" in content_type:
        return True

    if response.content.startswith(
        b"%PDF"
    ):
        return True

    if url.lower().endswith(".pdf"):
        return True

    return False


def extract_pdf_links(
    page_url,
    html,
):

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    candidates = {}

    for a in soup.find_all(
        "a",
        href=True,
    ):

        href = urljoin(
            page_url,
            a["href"],
        )

        href = clean_url(href)

        text = a.get_text(
            " ",
            strip=True,
        )

        score = document_score(
            text,
            href,
        )

        # Consideriamo solo candidati
        # sufficientemente pertinenti.
        if score < 70:
            continue

        candidates[href] = {
            "url": href,
            "title": text,
            "score": score,
        }

    return sorted(
        candidates.values(),
        key=lambda x: x["score"],
        reverse=True,
    )


def download_document(
    session,
    url,
):

    try:

        response = session.get(
            url,
            headers=HEADERS,
            timeout=60,
            allow_redirects=True,
        )

        if response.status_code >= 400:
            return None

        if not is_pdf(
            response,
            response.url,
        ):
            return None

        return response

    except requests.RequestException as exc:

        print(
            "DOWNLOAD ERROR:",
            exc,
        )

        return None


def save_document(
    conn,
    school_id,
    school_year,
    title,
    url,
    response,
):

    content = response.content

    digest = sha256(content)

    filename = filename_from_url(
        response.url
    )

    # Aggiungiamo hash per evitare
    # collisioni tra file omonimi.
    safe_name = re.sub(
        r"[^A-Za-z0-9._-]+",
        "_",
        filename,
    )

    school_dir = (
        DOCUMENT_DIR
        / str(school_id)
    )

    school_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    destination = (
        school_dir
        / f"{digest[:12]}_{safe_name}"
    )

    if not destination.exists():

        destination.write_bytes(
            content
        )

    existing = conn.execute(
        """
        SELECT id
        FROM ptof_documents
        WHERE school_id = ?
          AND sha256 = ?
        """,
        (
            school_id,
            digest,
        ),
    ).fetchone()

    if existing:
        return False

    conn.execute(
        """
        INSERT INTO ptof_documents (
            school_id,
            school_year,
            url,
            title,
            local_path,
            sha256,
            retrieved_at,
            status
        )
        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            datetime('now'),
            'DOWNLOADED'
        )
        """,
        (
            school_id,
            school_year,
            response.url,
            title,
            str(destination),
            digest,
        ),
    )

    return True


def process_source(
    conn,
    session,
    source,
    school,
):

    source_id = source[0]
    source_url = source[1]
    source_title = source[2]

    (
        school_id,
        codice,
        denominazione,
    ) = school

    print()
    print(
        f"[{codice}] "
        f"{source_title}"
    )

    print(
        "PAGE:",
        source_url,
    )

    response = download_document(
        session,
        source_url,
    )

    # La candidate potrebbe essere
    # direttamente un PDF.
    if response:

        score = document_score(
            source_title,
            response.url,
        )

        print(
            "PDF DIRECT:",
            response.url,
        )

        print(
            "SCORE:",
            score,
        )

        if score >= 100:

            saved = save_document(
                conn,
                school_id,
                "2025/26",
                source_title,
                source_url,
                response,
            )

            print(
                "SAVED:",
                saved,
            )

        return

    # Altrimenti è una pagina HTML
    try:

        page = session.get(
            source_url,
            headers=HEADERS,
            timeout=30,
            allow_redirects=True,
        )

    except requests.RequestException as exc:

        print(
            "PAGE ERROR:",
            exc,
        )

        return

    if page.status_code >= 400:
        return

    if "html" not in (
        page.headers
        .get(
            "Content-Type",
            "",
        )
        .lower()
    ):
        return

    pdfs = extract_pdf_links(
        page.url,
        page.text,
    )

    print(
        "PDF CANDIDATES:",
        len(pdfs),
    )

    for item in pdfs[:20]:

        print(
            f"[{item['score']:3}] "
            f"{item['title'][:80]}"
        )

        if item["score"] < 100:
            continue

        response = download_document(
            session,
            item["url"],
        )

        if not response:
            continue

        saved = save_document(
            conn,
            school_id,
            "2025/26",
            item["title"],
            item["url"],
            response,
        )

        print(
            "  SAVED:",
            saved,
        )

        # Non scarichiamo decine di
        # documenti duplicati.
        time.sleep(1)


def main():

    DOCUMENT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    conn = sqlite3.connect(
        DB_PATH
    )

    session = requests.Session()

    schools = conn.execute(
        """
        SELECT
            id,
            codice_scuola,
            denominazione
        FROM schools
        """
    ).fetchall()

    sources = conn.execute(
        """
        SELECT
            id,
            school_id,
            url,
            title
        FROM sources
        WHERE source_type = 'PTOF_CANDIDATE'
        ORDER BY school_id
        """
    ).fetchall()

    print(
        "Candidate sources:",
        len(sources),
    )

    school_map = {
        row[0]: row
        for row in schools
    }

    for (
        source_id,
        school_id,
        url,
        title,
    ) in sources:

        school = school_map.get(
            school_id
        )

        if not school:
            continue

        process_source(
            conn,
            session,
            (
                source_id,
                url,
                title,
            ),
            school,
        )

        conn.commit()

        time.sleep(2)

    conn.close()

    print()
    print("=" * 80)
    print("PTOF HARVEST COMPLETATO")
    print("=" * 80)


if __name__ == "__main__":
    main()
