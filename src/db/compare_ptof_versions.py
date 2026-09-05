from pathlib import Path
import difflib
import json
import re
import sqlite3
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "school-intelligence.sqlite"
)

OUTPUT_PATH = (
    BASE_DIR
    / "docs"
    / "data"
    / "ptof_comparisons.json"
)


def extract_text(pdf_path):
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    result = subprocess.run(
        [
            "pdftotext",
            "-layout",
            str(pdf_path),
            "-",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or "pdftotext failed"
        )

    return result.stdout


def normalize_lines(text):
    lines = []

    for line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()

        if not line:
            continue

        lines.append(line)

    return lines


def compare_text(old_text, new_text):
    old_lines = normalize_lines(old_text)
    new_lines = normalize_lines(new_text)

    matcher = difflib.SequenceMatcher(
        None,
        old_lines,
        new_lines,
    )

    added = []
    removed = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():

        if tag in ("delete", "replace"):
            removed.extend(old_lines[i1:i2])

        if tag in ("insert", "replace"):
            added.extend(new_lines[j1:j2])

    return {
        "old_lines": len(old_lines),
        "new_lines": len(new_lines),
        "added_lines": len(added),
        "removed_lines": len(removed),
        "added": added,
        "removed": removed,
    }


def load_versions(conn):
    rows = conn.execute(
        """
        SELECT
            id,
            school_id,
            school_year,
            url,
            title,
            local_path,
            sha256,
            retrieved_at,
            document_date,
            document_type,
            relevance,
            relevance_score,
            source_key,
            version_number,
            is_current
        FROM ptof_documents
        WHERE source_key IS NOT NULL
          AND version_number IS NOT NULL
        ORDER BY
            source_key,
            version_number
        """
    ).fetchall()

    groups = {}

    for row in rows:
        groups.setdefault(row["source_key"], []).append(row)

    return groups


def build_comparisons(conn):
    groups = load_versions(conn)
    comparisons = []

    for source_key, versions in groups.items():

        if len(versions) < 2:
            continue

        for old, new in zip(versions, versions[1:]):

            old_path = BASE_DIR / old["local_path"]
            new_path = BASE_DIR / new["local_path"]

            try:
                old_text = extract_text(old_path)
                new_text = extract_text(new_path)

                diff = compare_text(
                    old_text,
                    new_text,
                )

                error = None

            except Exception as exc:
                diff = {
                    "old_lines": 0,
                    "new_lines": 0,
                    "added_lines": 0,
                    "removed_lines": 0,
                    "added": [],
                    "removed": [],
                }

                error = (
                    f"{type(exc).__name__}: {exc}"
                )

            comparisons.append(
                {
                    "source_key": source_key,
                    "school_id": old["school_id"],
                    "document_id_old": old["id"],
                    "document_id_new": new["id"],
                    "version_old": old["version_number"],
                    "version_new": new["version_number"],
                    "sha256_old": old["sha256"],
                    "sha256_new": new["sha256"],
                    "title_old": old["title"],
                    "title_new": new["title"],
                    "retrieved_at_old": old["retrieved_at"],
                    "retrieved_at_new": new["retrieved_at"],
                    "document_date_old": old["document_date"],
                    "document_date_new": new["document_date"],
                    "diff": diff,
                    "error": error,
                }
            )

    return comparisons


def main():
    print("=" * 80)
    print("SCHOOL INTELLIGENCE - PTOF VERSION COMPARISON")
    print("=" * 80)

    if not DB_PATH.exists():
        print("ERRORE: database non trovato.")
        return 1

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        comparisons = build_comparisons(conn)

    finally:
        conn.close()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            comparisons,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("Confronti generati:", len(comparisons))
    print("Output:", OUTPUT_PATH)

    for item in comparisons:
        diff = item["diff"]

        print(
            f"  school={item['school_id']} "
            f"v{item['version_old']} -> "
            f"v{item['version_new']} "
            f"+{diff['added_lines']} "
            f"-{diff['removed_lines']}"
        )

        if item["error"]:
            print("    ERROR:", item["error"])

    print()
    print(
        "RESULT:",
        "PASS" if OUTPUT_PATH.exists() else "FAIL"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
