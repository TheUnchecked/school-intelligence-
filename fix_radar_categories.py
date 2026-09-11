"""
Corregge il grafico radar della scheda scuola, che mostrava sempre
0% su tutti gli assi.

Causa del bug: RADAR_CATEGORIES usava nomi leggibili ("Lingue",
"Attività e didattica"...) per cercare corrispondenza col campo
record.category — ma nei dati reali quel campo contiene codici
abbreviati in maiuscolo (LINGUE, DIDATTICA, SERVIZI, STRUTTURE,
ORGANIZZAZIONE). Nessuna corrispondenza trovava mai nulla, quindi
ogni categoria restava a 0/0 = 0%.

La correzione separa la chiave di confronto (maiuscola, come nei
dati) dall'etichetta mostrata nel grafico (leggibile).

Uso:
    python fix_radar_categories.py

Da eseguire nella cartella radice del repository. È idempotente.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def log(msg):
    print(f"- {msg}")


def main():
    path = BASE_DIR / "docs" / "js" / "app.js"

    if not path.exists():
        print(f"ERRORE: file non trovato: {path}")
        return 1

    text = path.read_text(encoding="utf-8")

    if '{ key: "LINGUE"' in text:
        log("app.js: correzione già applicata, salto.")
        return 0

    old = '''const RADAR_CATEGORIES = [
    "Lingue",
    "Servizi",
    "Strutture",
    "Attività e didattica",
    "Organizzazione"
];

function computeCategoryScores(records) {

    const totals = {};

    RADAR_CATEGORIES.forEach(category => {
        totals[category] = { total: 0, score: 0 };
    });

    records.forEach(record => {

        const category = record.category;

        if (!totals[category]) return;

        totals[category].total++;

        const weight =
            record.status === "VERIFIED" ? 1 :
            record.status === "PROBABLE" ? 0.7 :
            record.status === "MENTIONED" ? 0.4 :
            0;

        totals[category].score += weight;
    });

    return RADAR_CATEGORIES.map(category => {

        const { total, score } = totals[category];

        return {
            category,
            percent:
                total > 0
                    ? Math.round((score / total) * 100)
                    : 0
        };
    });
}'''

    new = '''const RADAR_CATEGORIES = [
    { key: "LINGUE", label: "Lingue" },
    { key: "SERVIZI", label: "Servizi" },
    { key: "STRUTTURE", label: "Strutture" },
    { key: "DIDATTICA", label: "Attività e didattica" },
    { key: "ORGANIZZAZIONE", label: "Organizzazione" }
];

function computeCategoryScores(records) {

    const totals = {};

    RADAR_CATEGORIES.forEach(({ key }) => {
        totals[key] = { total: 0, score: 0 };
    });

    records.forEach(record => {

        const key = String(record.category || "").toUpperCase();

        if (!totals[key]) return;

        totals[key].total++;

        const weight =
            record.status === "VERIFIED" ? 1 :
            record.status === "PROBABLE" ? 0.7 :
            record.status === "MENTIONED" ? 0.4 :
            0;

        totals[key].score += weight;
    });

    return RADAR_CATEGORIES.map(({ key, label }) => {

        const { total, score } = totals[key];

        return {
            category: label,
            percent:
                total > 0
                    ? Math.round((score / total) * 100)
                    : 0
        };
    });
}'''

    if old not in text:
        log("ATTENZIONE: blocco RADAR_CATEGORIES non trovato come "
            "atteso, controllo manuale necessario in app.js")
        return 1

    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    log("app.js: radar corretto — ora usa le chiavi maiuscole reali "
        "(LINGUE, SERVIZI, STRUTTURE, DIDATTICA, ORGANIZZAZIONE) per "
        "trovare i dati, mostrando comunque le etichette leggibili.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
