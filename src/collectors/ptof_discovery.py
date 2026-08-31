from pathlib import Path
from urllib.parse import urljoin, urlparse
import sqlite3
import re
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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; SchoolIntelligence/0.1)"
    )
}


KEYWORDS = [
    "ptof",
    "piano triennale",
    "offerta formativa",
    "piano dell'offerta formativa",
    "curricolo",
    "curriculum",
    "documenti",
]


def score(text, url):

    text = f"{text} {url}".lower()

    value = 0

    if "ptof" in text:
        value += 100

    if "piano triennale" in text:
        value += 80

    if "offerta formativa" in text:
        value += 70

    if "piano dell'offerta formativa" in text:
        value += 70

    if "curricolo" in text:
        value += 40

    if "documenti" in text:
        value += 20

    if url.lower().endswith(".pdf"):
        value += 50

    return value


def same_domain(a, b):

    return (
        urlparse(a).netloc.lower()
        ==
        urlparse(b).netloc.lower()
    )


def fetch(session, url):

    try:

        r = session.get(
            url,
            headers=HEADERS,
            timeout=30,
            allow_redirects=True,
        )

        if r.status_code >= 400:
            return None

        return r

    except requests.RequestException as exc:

        print("ERROR:", exc)

        return None


def extract_links(base_url, html):

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    results = []

    for a in soup.find_all("a", href=True):

        href = urljoin(
            base_url,
            a["href"],
        )

        href = href.split("#")[0]

        if not href.startswith(("http://", "https://")):
            continue

        text = a.get_text(
            " ",
            strip=True,
        )

        combined = f"{text} {href}"

        value = score(
            text,
            href,
        )

        # PDF: interessante anche senza keyword
        if href.lower().endswith(".pdf"):
            value += 20

        if value > 0:

            results.append(
                {
                    "url": href,
                    "text": text,
                    "score": value,
                }
            )

    unique = {}

    for item in results:

        url = item["url"]

        if (
            url not in unique
            or item["score"]
            > unique[url]["score"]
        ):
            unique[url] = item

    return sorted(
        unique.values(),
        key=lambda x: x["score"],
        reverse=True,
    )


def save_candidate(
    conn,
    school_id,
    item,
):

    existing = conn.execute(
        """
        SELECT id
        FROM sources
        WHERE school_id = ?
          AND url = ?
        """,
        (
            school_id,
            item["url"],
        ),
    ).fetchone()

    if existing:
        return False

    conn.execute(
        """
        INSERT INTO sources (
            school_id,
            source_type,
            url,
            title,
            retrieved_at,
            status
        )
        VALUES (
            ?,
            'PTOF_CANDIDATE',
            ?,
            ?,
            datetime('now'),
            'DISCOVERED_L2'
        )
        """,
        (
            school_id,
            item["url"],
            item["text"],
        ),
    )

    return True


def process_school(
    conn,
    session,
    school_id,
    codice,
    denominazione,
    website,
):

    print()
    print("=" * 80)
    print(codice, "|", denominazione)
    print("SITE:", website)
    print("=" * 80)

    queue = [
        (
            website,
            0,
        )
    ]

    visited = set()
    candidates = {}

    while queue:

        url, depth = queue.pop(0)

        if url in visited:
            continue

        if depth > 2:
            continue

        visited.add(url)

        print(
            f"[L{depth}] {url}"
        )

        response = fetch(
            session,
            url,
        )

        if response is None:
            continue

        content_type = (
            response.headers
            .get(
                "Content-Type",
                "",
            )
            .lower()
        )

        # PDF trovato
        if (
            "pdf" in content_type
            or url.lower().endswith(".pdf")
        ):

            item = {
                "url": response.url,
                "text": url,
                "score": score(
                    url,
                    url,
                ),
            }

            candidates[
                response.url
            ] = item

            continue

        if "html" not in content_type:
            continue

        links = extract_links(
            response.url,
            response.text,
        )

        for item in links:

            if item["score"] >= 40:

                candidates[
                    item["url"]
                ] = item

            # approfondiamo solo link
            # semanticamente pertinenti
            if (
                depth < 2
                and same_domain(
                    website,
                    item["url"],
                )
                and item["score"] >= 40
            ):

                queue.append(
                    (
                        item["url"],
                        depth + 1,
                    )
                )

    print()
    print(
        "CANDIDATI TROVATI:",
        len(candidates),
    )

    ordered = sorted(
        candidates.values(),
        key=lambda x: x["score"],
        reverse=True,
    )

    for item in ordered[:30]:

        print(
            f"[{item['score']:3}] "
            f"{item['text'][:80]} "
            f"→ {item['url']}"
        )

        save_candidate(
            conn,
            school_id,
            item,
        )

    conn.commit()


def main():

    conn = sqlite3.connect(
        DB_PATH
    )

    session = requests.Session()

    schools = conn.execute(
        """
        SELECT
            id,
            codice_scuola,
            denominazione,
            website
        FROM schools
        WHERE website IS NOT NULL
        ORDER BY comune, denominazione
        """
    ).fetchall()

    print(
        "Scuole da analizzare:",
        len(schools),
    )

    for row in schools:

        process_school(
            conn,
            session,
            *row,
        )

        time.sleep(2)

    conn.close()

    print()
    print("=" * 80)
    print("PTOF DISCOVERY COMPLETATO")
    print("=" * 80)


if __name__ == "__main__":
    main()
