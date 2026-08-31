from pathlib import Path
import subprocess
import sys


ROOT = Path("data/documents/ptof")


def convert_pdf(pdf_path: Path):
    txt_path = pdf_path.with_suffix(".txt")

    print(f"PDF : {pdf_path}")
    print(f"TXT : {txt_path}")

    try:
        result = subprocess.run(
            [
                "pdftotext",
                "-layout",
                str(pdf_path),
                str(txt_path),
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("ERROR:", result.stderr.strip())
            return False

        if not txt_path.exists():
            print("ERROR: TXT non creato")
            return False

        size = txt_path.stat().st_size

        if size == 0:
            print("WARNING: TXT vuoto")
            return False

        print(
            f"OK: {size / 1024:.1f} KB"
        )

        return True

    except FileNotFoundError:
        print(
            "ERROR: pdftotext non installato."
        )
        return False

    except Exception as e:
        print(
            f"ERROR: {type(e).__name__}: {e}"
        )
        return False


def main():

    print("=" * 80)
    print("PDF → TXT CONVERTER")
    print("=" * 80)

    pdfs = sorted(
        ROOT.rglob("*.pdf")
    )

    print(
        f"PDF trovati: {len(pdfs)}"
    )
    print()

    success = 0
    failed = 0

    for pdf in pdfs:

        if convert_pdf(pdf):
            success += 1
        else:
            failed += 1

        print()

    print("=" * 80)
    print("CONVERSIONE COMPLETATA")
    print("=" * 80)

    print(
        f"Convertiti: {success}"
    )

    print(
        f"Falliti:    {failed}"
    )

    print(
        f"TXT totali: "
        f"{len(list(ROOT.rglob('*.txt')))}"
    )


if __name__ == "__main__":
    main()
