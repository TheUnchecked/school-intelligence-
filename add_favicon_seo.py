"""
Aggiunge al sito le tre cose base che oggi mancano per un sito
pubblico serio:

  1. Favicon (SVG, blu coerente con l'accento del sito) — oggi il
     sito non ne ha una, quindi ogni scheda del browser/lista
     preferiti mostra un'icona generica.
  2. robots.txt — dà istruzioni esplicite ai motori di ricerca
     (permetti tutto, ecco la sitemap).
  3. sitemap.xml, generata automaticamente ad ogni esportazione dati
     (non un file statico da tenere aggiornato a mano): un URL per
     la home e uno per ogni scheda scuola (?scuola=CODICE), così
     Google può indicizzare anche le singole schede, non solo la
     home.

Uso:
    python add_favicon_seo.py

Da eseguire nella cartella radice del repository. È idempotente.

IMPORTANTE — passo manuale dopo aver eseguito questo script:
   La sitemap viene scritta quando si rigenerano i dati pubblici:

       python3 -m src.export.export_public_data

   Senza questo passo docs/sitemap.xml non verrà creato.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

FAVICON_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#185fa5"/>
  <path
    d="M32 14 L54 24 L32 34 L10 24 Z"
    fill="#ffffff"
  />
  <path
    d="M20 29 V42 C20 46 26 49 32 49 C38 49 44 46 44 42 V29"
    fill="none"
    stroke="#ffffff"
    stroke-width="3.4"
    stroke-linecap="round"
    stroke-linejoin="round"
  />
  <line
    x1="54" y1="24" x2="54" y2="38"
    stroke="#ffffff"
    stroke-width="3.4"
    stroke-linecap="round"
  />
</svg>
'''

ROBOTS_TXT = '''User-agent: *
Allow: /

Sitemap: https://theunchecked.github.io/school-intelligence-/sitemap.xml
'''


def log(msg):
    print(f"- {msg}")


def add_favicon():
    path = BASE_DIR / "docs" / "favicon.svg"

    if path.exists():
        log("docs/favicon.svg: già presente, salto.")
        return

    path.write_text(FAVICON_SVG, encoding="utf-8")
    log("docs/favicon.svg creato.")


def add_robots():
    path = BASE_DIR / "docs" / "robots.txt"

    if path.exists():
        log("docs/robots.txt: già presente, salto.")
        return

    path.write_text(ROBOTS_TXT, encoding="utf-8")
    log("docs/robots.txt creato.")


def link_favicon_in_html():
    path = BASE_DIR / "docs" / "index.html"
    text = path.read_text(encoding="utf-8")

    if 'rel="icon"' in text:
        log("index.html: favicon già collegato, salto.")
        return

    old = '''    <link rel="stylesheet" href="css/app.css">
    <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"'''

    new = '''    <link rel="icon" type="image/svg+xml" href="favicon.svg">

    <link rel="stylesheet" href="css/app.css">
    <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"'''

    if old not in text:
        log("ATTENZIONE: blocco <head> non trovato come atteso, "
            "controllo manuale necessario in index.html")
        return

    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    log("index.html: favicon collegato.")


def add_sitemap_generation():
    path = BASE_DIR / "src" / "export" / "export_public_data.py"
    text = path.read_text(encoding="utf-8")

    if "write_sitemap" in text:
        log("export_public_data.py: già aggiornato, salto.")
        return

    old_import = ("from pathlib import Path\nimport json\nimport math\n"
                  "import sqlite3\nfrom datetime import datetime, timezone")
    new_import = (old_import +
                  "\nfrom xml.sax.saxutils import escape as xml_escape")

    if old_import not in text:
        log("ATTENZIONE: blocco import non trovato come atteso, "
            "controllo manuale necessario in export_public_data.py")
        return

    text = text.replace(old_import, new_import)

    old_write_json = '''def write_json(filename, data):
    path = OUTPUT_DIR / filename

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return path'''

    new_write_json = '''def write_json(filename, data):
    path = OUTPUT_DIR / filename

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    return path


SITE_BASE_URL = "https://theunchecked.github.io/school-intelligence-/"


def write_sitemap(schools):
    """
    Genera docs/sitemap.xml con la home e un URL per ogni scuola
    (?scuola=CODICE), così i motori di ricerca possono indicizzare
    anche le singole schede, non solo la home.
    """

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    urls = [(SITE_BASE_URL, "1.0")]

    for school in schools:
        codice = school.get("codice_scuola")

        if not codice:
            continue

        url = f"{SITE_BASE_URL}?scuola={xml_escape(codice)}"
        urls.append((url, "0.7"))

    entries = "\\n".join(
        f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{today}</lastmod>
    <priority>{priority}</priority>
  </url>"""
        for loc, priority in urls
    )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\\n'
        f"{entries}\\n"
        "</urlset>\\n"
    )

    path = OUTPUT_DIR.parent / "sitemap.xml"
    path.write_text(xml, encoding="utf-8")

    return path'''

    if old_write_json not in text:
        log("ATTENZIONE: funzione write_json non trovata come attesa, "
            "controllo manuale necessario in export_public_data.py")
        return

    text = text.replace(old_write_json, new_write_json)

    old_call = '''        schools = export_schools(conn)
        write_json(
            "schools.json",
            schools
        )

        print(
            f"  schools.json: {len(schools)}"
        )'''

    new_call = '''        schools = export_schools(conn)
        write_json(
            "schools.json",
            schools
        )

        print(
            f"  schools.json: {len(schools)}"
        )

        sitemap_path = write_sitemap(schools)
        print(
            f"  sitemap.xml: {len(schools) + 1} URL "
            f"({sitemap_path.name})"
        )'''

    if old_call not in text:
        log("ATTENZIONE: punto di chiamata export_schools non trovato "
            "come atteso, controllo manuale necessario in "
            "export_public_data.py")
        return

    text = text.replace(old_call, new_call)
    path.write_text(text, encoding="utf-8")
    log("export_public_data.py: generazione automatica di sitemap.xml "
        "aggiunta.")


def main():
    print("Favicon, robots.txt e sitemap automatica")
    print("=" * 60)
    add_favicon()
    add_robots()
    link_favicon_in_html()
    add_sitemap_generation()
    print("=" * 60)
    print("Fatto.")
    print()
    print("PASSO SUCCESSIVO OBBLIGATORIO — genera la sitemap:")
    print("  python3 -m src.export.export_public_data")
    return 0


if __name__ == "__main__":
    sys.exit(main())
