"""
Corregge la ripetizione del contenuto della home (Hero, "Come nasce
la classifica", KPI, filtri, mappa) ogni volta che si apre la scheda
di una scuola.

Il problema: aprendo una scuola, la pagina nascondeva solo la lista
dei risultati, ma non le sezioni sopra di essa — quindi bisognava
scorrere di nuovo tutto il testo del metodo prima di arrivare alla
scheda vera e propria.

La correzione: racchiude Hero + Metodo + KPI + Filtri + Mappa in un
unico contenitore (#homeIntro) che si nasconde quando si apre una
scheda scuola e riappare quando la si chiude — stesso comportamento
già esistente per la lista dei risultati.

Uso:
    python fix_home_repetition.py

Da eseguire nella cartella radice del repository. È idempotente.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def log(msg):
    print(f"- {msg}")


def patch_html():
    path = BASE_DIR / "docs" / "index.html"
    text = path.read_text(encoding="utf-8")

    if 'id="homeIntro"' in text:
        log("index.html: già corretto, salto.")
        return

    old_start = '<main class="container">\n\n    <section class="hero">'
    new_start = '<main class="container">\n\n    <div id="homeIntro">\n\n    <section class="hero">'

    if old_start not in text:
        log("ATTENZIONE: apertura <main> non trovata come attesa, "
            "controllo manuale necessario in index.html")
        return

    text = text.replace(old_start, new_start)

    old_end = '''        <div id="schoolMap" class="school-map"></div>

    </section>


    <section>

        <div class="section-header">

            <div>
                <span class="eyebrow">
                    RISULTATI
                </span>'''

    new_end = '''        <div id="schoolMap" class="school-map"></div>

    </section>

    </div>


    <section>

        <div class="section-header">

            <div>
                <span class="eyebrow">
                    RISULTATI
                </span>'''

    if old_end not in text:
        log("ATTENZIONE: confine sezione Risultati non trovato come "
            "atteso, controllo manuale necessario in index.html")
        return

    text = text.replace(old_end, new_end)
    path.write_text(text, encoding="utf-8")
    log("index.html: Hero, Metodo, KPI, Filtri e Mappa racchiusi in "
        "#homeIntro.")


def patch_js():
    path = BASE_DIR / "docs" / "js" / "app.js"
    text = path.read_text(encoding="utf-8")

    if 'homeIntro' in text:
        log("app.js: già corretto, salto.")
        return

    old_open = '''    $("schoolList").parentElement.classList.add("hidden");
    $("detail").classList.remove("hidden");

    // URL condivisibile'''

    new_open = '''    $("schoolList").parentElement.classList.add("hidden");
    if ($("homeIntro")) {
        $("homeIntro").classList.add("hidden");
    }
    $("detail").classList.remove("hidden");

    // URL condivisibile'''

    if old_open not in text:
        log("ATTENZIONE: punto di apertura scheda non trovato come "
            "atteso, controllo manuale necessario in app.js")
        return

    text = text.replace(old_open, new_open)

    old_close = '''function closeDetailView() {

    $("detail").classList.add(
        "hidden"
    );

    $("schoolList").parentElement.classList.remove(
        "hidden"
    );

    const shareUrl'''

    new_close = '''function closeDetailView() {

    $("detail").classList.add(
        "hidden"
    );

    $("schoolList").parentElement.classList.remove(
        "hidden"
    );

    if ($("homeIntro")) {
        $("homeIntro").classList.remove("hidden");
    }

    const shareUrl'''

    if old_close not in text:
        log("ATTENZIONE: punto di chiusura scheda non trovato come "
            "atteso, controllo manuale necessario in app.js")
        return

    text = text.replace(old_close, new_close)
    path.write_text(text, encoding="utf-8")
    log("app.js: #homeIntro si nasconde all'apertura di una scheda "
        "scuola e riappare alla chiusura.")


def main():
    print("Rimozione ripetizione contenuto home nella scheda scuola")
    print("=" * 60)
    patch_html()
    patch_js()
    print("=" * 60)
    print("Fatto. Controlla il risultato in locale prima di committare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
