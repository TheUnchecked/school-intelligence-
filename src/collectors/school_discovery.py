from pathlib import Path
from urllib.parse import urljoin, urlparse
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

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(compatible; SchoolIntelligence/0.1; "
        "+https://example.invalid)"
    )
}

KEYWORDS = [
    "ptof",
    "piano triennale",
    "offerta formativa",
    "piano dell'offerta formativa",
    "piano dell offerta formativa",
]


MAX_LINKS = 100


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def normalize_url(url):
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return None

    return url.split("#")[0]


def keyword_score(text):
    text = text.lower()

    score = 0

    if "ptof" in text:
        score += 100

    if "piano triennale" in text:
        score += 80

    if "offerta formativa" in text:
        score += 60

    if "piano dell'offerta formativa" in text:
        score += 70

    if text.endswith(".pdf"):
        score += 30

    return score


def same_domain(base, target):
    return (
        urlparse(base).netloc.lower()
        == urlparse(target).netloc.lower()
    )


def fetch(url, session):

    try:
        response = session.get(
            url,
            headers=HEADERS,
            timeout=30,
            allow_redirects=True,
        )

        return response

    except requests.RequestException as exc:

        print("ERROR:", exc)

        return None


def discover_school(school_id, website, session):

    print()
    print("=" * 80)
    print("SCHOOL ID:", school_id)
    print("WEBSITE:", website)
    print("=" * 80)

    response = fetch(website, session)

    if response is None:
        return []

    print("HTTP:", response.status_code)
    print("FINAL URL:", response.url)
    print(
        "CONTENT-TYPE:",
        response.headers.get("Content-Type"),
    )

    if response.status_code >= 400:
        return []

    content_type = response.headers.get(
        "Content-Type",
        "",
    ).lower()

    if "html" not in content_type:
        return []

    soup = BeautifulSoup(
        response.text,
        "lxml",
    )

    candidates = []

    for a in soup.find_all("a", href=True):

        href = normalize_url(
            urljoin(response.url, a["href"])
        )

        if not href:
            continue

        text = a.get_text(
            " ",
            strip=True,
        )

        combined = f"{text} {href}"

        score = keyword_score(combined)

        if score == 0:
            continue

        candidates.append(
            {
                "url": href,
                "text": text,
                "score": score,
            }
        )

    # Deduplica
    unique = {}

    for item in candidates:

        url = item["url"]

        if (
            url not in unique
            or item["score"] > unique[url]["score"]
        ):
            unique[url] = item

    candidates = sorted(
        unique.values(),
        key=lambda x: x["score"],
        reverse=True,
    )

    print()
    print("CANDIDATI PTOF:", len(candidates))

    for item in candidates[:MAX_LINKS]:

        print(
            f"[{item['score']:3}] "
            f"{item['text'][:70]} "
            f"→ {item['url']}"
        )

    return candidates


def save_source(
    conn,
    school_id,
    url,
    title,
    content_hash,
    status,
):

    conn.execute(
        """
        INSERT INTO sources (
            school_id,
            source_type,
            url,
            title,
            retrieved_at,
            content_hash,
            status
        )
        VALUES (
            ?,
            'PTOF_CANDIDATE',
            ?,
            ?,
            datetime('now'),
            ?,
            ?
        )
        """,
        (
            school_id,
            url,
            title,
            content_hash,
            status,
        ),
    )


def main():

    if not DB_PATH.exists():
        raise RuntimeError(
            f"Database non trovato: {DB_PATH}"
        )

    conn = sqlite3.connect(DB_PATH)

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
        f"Scuole con sito da analizzare: {len(schools)}"
    )

    session = requests.Session()

    for (
        school_id,
        codice_scuola,
        denominazione,
        website,
    ) in schools:

        print()
        print(
            f">>> {codice_scuola} | "
            f"{denominazione}"
        )

        candidates = discover_school(
            school_id,
            website,
            session,
        )

        for candidate in candidates:

            # Non scarichiamo ancora il documento.
            # Registriamo solamente il candidato.

            save_source(
                conn,
                school_id,
                candidate["url"],
                candidate["text"],
                None,
                "DISCOVERED",
            )

        conn.commit()

        # Delay prudenziale tra siti.
        time.sleep(2)

    conn.close()

    print()
    print("=" * 80)
    print("DISCOVERY COMPLETATA")
    print("=" * 80)


if __name__ == "__main__":
    main()
