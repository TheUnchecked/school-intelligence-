from pathlib import Path
from urllib.parse import urlparse
import sqlite3
import requests
import re
import time


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


def normalize_url(url):
    """
    Corregge gli errori più comuni presenti
    negli URL provenienti dal dataset MIM.
    """

    if not url:
        return None

    url = url.strip()

    # Errori tipo:
    # https://https//www.example.it
    url = re.sub(
        r"^https?://https?//",
        "https://",
        url,
        flags=re.IGNORECASE,
    )

    # Errori tipo:
    # https//www.example.it
    if url.startswith("https//"):
        url = "https://" + url[6:]

    if url.startswith("http//"):
        url = "http://" + url[5:]

    # Corregge www senza schema
    if url.startswith("www."):
        url = "https://" + url

    # Alcuni dataset possono contenere
    # spazi o caratteri residui.
    url = url.replace(" ", "")

    return url


def test_url(session, url):

    candidates = []

    normalized = normalize_url(url)

    if not normalized:
        return None

    parsed = urlparse(normalized)

    if not parsed.netloc:
        return None

    # Prima HTTPS
    candidates.append(
        normalized.replace(
            "http://",
            "https://",
            1,
        )
    )

    # Poi HTTP come fallback
    if normalized.startswith("https://"):
        candidates.append(
            normalized.replace(
                "https://",
                "http://",
                1,
            )
        )

    tested = set()

    for candidate in candidates:

        if candidate in tested:
            continue

        tested.add(candidate)

        try:

            r = session.get(
                candidate,
                headers=HEADERS,
                timeout=15,
                allow_redirects=True,
            )

            print(
                f"  {candidate} -> "
                f"{r.status_code} "
                f"{r.url}"
            )

            if r.status_code < 500:

                return {
                    "original": url,
                    "normalized": candidate,
                    "final": r.url,
                    "status": r.status_code,
                }

        except requests.RequestException as exc:

            print(
                f"  {candidate} -> ERROR "
                f"{exc.__class__.__name__}"
            )

    return None


def main():

    conn = sqlite3.connect(
        DB_PATH
    )

    schools = conn.execute(
        """
        SELECT
            id,
            codice_scuola,
            denominazione,
            website
        FROM schools
        ORDER BY comune, denominazione
        """
    ).fetchall()

    session = requests.Session()

    print("=" * 80)
    print("SCHOOL WEBSITE RECOVERY")
    print("=" * 80)

    recovered = 0
    failed = 0

    for (
        school_id,
        codice,
        denominazione,
        website,
    ) in schools:

        print()
        print(
            f"[{codice}] {denominazione}"
        )

        print(
            "  MIM:",
            website,
        )

        result = test_url(
            session,
            website,
        )

        if result:

            recovered += 1

            print(
                "  OK:",
                result["final"],
            )

            conn.execute(
                """
                UPDATE schools
                SET website = ?
                WHERE id = ?
                """,
                (
                    result["final"],
                    school_id,
                ),
            )

        else:

            failed += 1

            print(
                "  FALLITA"
            )

        conn.commit()

        time.sleep(1)

    conn.close()

    print()
    print("=" * 80)
    print("RECOVERY COMPLETATA")
    print("=" * 80)

    print(
        "Siti recuperati:",
        recovered,
    )

    print(
        "Siti non raggiungibili:",
        failed,
    )


if __name__ == "__main__":
    main()
