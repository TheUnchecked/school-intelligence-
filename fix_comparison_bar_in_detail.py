"""
Nasconde la barra "Confronta scuole" (e il relativo pannello, se
aperto) quando si visualizza la scheda dettaglio di una singola
scuola — non ha senso lì, appartiene solo alla lista/classifica.

Stesso problema, stessa causa, stessa correzione già applicata per
Hero/Metodo/Filtri/Mappa in fix_home_repetition.py: mancava il
collegamento alla visibilità della scheda dettaglio.

Uso:
    python fix_comparison_bar_in_detail.py

Da eseguire nella cartella radice del repository, DOPO aver già
applicato fix_home_repetition.py. È idempotente.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def log(msg):
    print(f"- {msg}")


def patch_js():
    path = BASE_DIR / "docs" / "js" / "app.js"
    text = path.read_text(encoding="utf-8")

    if 'comparisonToolbar' in text and '$("comparisonToolbar").classList.add("hidden")' in text:
        log("app.js: già corretto, salto.")
        return

    old_open = '''    $("schoolList").parentElement.classList.add("hidden");
    if ($("homeIntro")) {
        $("homeIntro").classList.add("hidden");
    }
    $("detail").classList.remove("hidden");

    // URL condivisibile'''

    new_open = '''    $("schoolList").parentElement.classList.add("hidden");
    if ($("homeIntro")) {
        $("homeIntro").classList.add("hidden");
    }
    if ($("comparisonToolbar")) {
        $("comparisonToolbar").classList.add("hidden");
    }
    if ($("comparisonPanel")) {
        $("comparisonPanel").hidden = true;
    }
    $("detail").classList.remove("hidden");

    // URL condivisibile'''

    if old_open not in text:
        log("ATTENZIONE: punto di apertura scheda non trovato come "
            "atteso (hai già applicato fix_home_repetition.py?), "
            "controllo manuale necessario in app.js")
        return

    text = text.replace(old_open, new_open)

    old_close = '''    if ($("homeIntro")) {
        $("homeIntro").classList.remove("hidden");
    }

    const shareUrl'''

    new_close = '''    if ($("homeIntro")) {
        $("homeIntro").classList.remove("hidden");
    }

    if ($("comparisonToolbar")) {
        $("comparisonToolbar").classList.remove("hidden");
    }

    const shareUrl'''

    if old_close not in text:
        log("ATTENZIONE: punto di chiusura scheda non trovato come "
            "atteso, controllo manuale necessario in app.js")
        return

    text = text.replace(old_close, new_close)
    path.write_text(text, encoding="utf-8")
    log("app.js: barra 'Confronta scuole' nascosta durante la scheda "
        "dettaglio, riappare alla chiusura.")


def main():
    print("Nasconde la barra Confronta scuole nella scheda dettaglio")
    print("=" * 60)
    patch_js()
    print("=" * 60)
    print("Fatto. Controlla il risultato in locale prima di committare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
