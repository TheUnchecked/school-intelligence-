#!/usr/bin/env python3

import shutil
import sqlite3
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "database" / "school-intelligence.sqlite"
TEXT_DIR = ROOT / "data" / "documents" / "text"


def convert_pdf(pdf_path: Path, txt_path: Path) -> bool:
    txt_path.parent.mkdir(parents=True, exist_ok=True)

    if shutil.which("pdftotext") is None:
        print("ERRORE: comando 'pdftotext' non trovato.")
        return False

    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        print(f"ERRORE conversione: {pdf_path}")
        if result.stderr:
            print(result.stderr.strip())
        return False

    return txt_path.exists()


def main():
    if not DB_PATH.exists():
        print(f"ERRORE: database non trovato: {DB_PATH}")
        return 1

    TEXT_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT id, local_path
        FROM ptof_documents
        WHERE local_path IS NOT NULL
          AND TRIM(local_path) <> ''
        ORDER BY id
        """
    ).fetchall()

    converted = 0
    skipped = 0
    errors = 0

    for document_id, local_path in rows:
        pdf_path = Path(local_path)

        if not pdf_path.is_absolute():
            pdf_path = ROOT / pdf_path

        if not pdf_path.exists():
            print(f"ERRORE: PDF non trovato per document_id={document_id}: {pdf_path}")
            errors += 1
            continue

        txt_path = TEXT_DIR / f"{document_id}.txt"

        if txt_path.exists() and txt_path.stat().st_size > 0:
            skipped += 1
            continue

        if convert_pdf(pdf_path, txt_path):
            converted += 1
            print(f"OK: {document_id} -> {txt_path}")
        else:
            errors += 1

    conn.close()

    print()
    print("=" * 60)
    print("PDF TO TEXT")
    print("=" * 60)
    print(f"Documenti totali : {len(rows)}")
    print(f"Convertiti       : {converted}")
    print(f"Già presenti     : {skipped}")
    print(f"Errori           : {errors}")
    print("=" * 60)

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
