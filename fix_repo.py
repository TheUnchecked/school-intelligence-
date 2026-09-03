"""
Script di manutenzione una tantum per school-intelligence.

Esegue in un colpo solo le correzioni discusse:

  1. Corregge il bug dello stato iscrizioni hardcoded in
     run_school_profile_pipeline.py (era fisso a "CLOSED", ora viene
     calcolato confrontando la data odierna con la finestra reale).
  2. Archivia scripts/broken/populate_school_profile.py, superato dalla
     pipeline attuale, spostandolo in scripts/archive/ (non lo cancella:
     lo si valuta e rimuove a mano dopo revisione).
  3. Sposta gli script "patch" una tantum (fix_ptof_selection.py,
     patch_school_header.py) in scripts/maintenance/, fuori dalla root.
  4. Crea un README.md che spiega la pipeline e come farla girare.
  5. Aggiorna .gitignore per smettere di versionare il database SQLite
     binario (che il workflow rigenera ad ogni run).
  6. Aggiorna il workflow GitHub Actions per eseguire i test (pytest)
     prima di rigenerare i dati pubblicati.

Uso:
    python fix_repo.py

Da eseguire nella cartella radice del repository (dove si trova questo
file). Lo script è idempotente: rieseguirlo non duplica le modifiche.
Al termine controlla le modifiche con "git diff" prima di committare.
"""

import re
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def log(msg):
    print(f"- {msg}")


# ---------------------------------------------------------------------
# 1. Bug stato iscrizioni: da valore fisso a calcolo dinamico
# ---------------------------------------------------------------------
def fix_enrolment_bug():
    path = BASE_DIR / "run_school_profile_pipeline.py"
    text = path.read_text(encoding="utf-8")

    if "def resolve_enrolment_status" in text:
        log("run_school_profile_pipeline.py: già corretto, salto.")
        return

    old_block = '''ENROLMENT_WINDOW = {
    "status": "CLOSED",
    "school_year": "2026/2027",
    "open_from": "2026-01-13",
    "open_until": "2026-02-14",
}'''

    new_block = '''# Finestra di iscrizione comunicata dal MIM (uguale per tutte le scuole
# statali: la data la fissa una circolare ministeriale nazionale, non la
# singola scuola). Lo STATO invece NON va scritto a mano: prima veniva
# fissato a "CLOSED" indipendentemente dalla data corrente, diventando
# silenziosamente falso ad ogni nuovo anno scolastico. Ora si calcola.
ENROLMENT_WINDOW = {
    "school_year": "2026/2027",
    "open_from": "2026-01-13",
    "open_until": "2026-02-14",
}


def resolve_enrolment_status(open_from, open_until, today=None):
    """Calcola lo stato reale confrontando oggi con la finestra.

    Ritorna "OPEN" se la data odierna è compresa nella finestra,
    "CLOSED" se è già passata, "UPCOMING" se deve ancora iniziare.
    """
    from datetime import date

    today = today or date.today()
    start = date.fromisoformat(open_from)
    end = date.fromisoformat(open_until)

    if today < start:
        return "UPCOMING"
    if today > end:
        return "CLOSED"
    return "OPEN"'''

    if old_block not in text:
        log("ATTENZIONE: blocco ENROLMENT_WINDOW non trovato come atteso, "
            "controllo manuale necessario in run_school_profile_pipeline.py")
        return

    text = text.replace(old_block, new_block)

    old_call = '''        conn.execute("""
            UPDATE school_profile
            SET enrolment_status = ?, enrolment_school_year = ?,
                enrolment_open_from = ?, enrolment_open_until = ?,
                enrolment_source_id = ?
            WHERE school_id = ?
        """, (
            ENROLMENT_WINDOW["status"], ENROLMENT_WINDOW["school_year"],
            ENROLMENT_WINDOW["open_from"], ENROLMENT_WINDOW["open_until"],
            row["id"], row["school_id"],
        ))'''

    new_call = '''        status = resolve_enrolment_status(
            ENROLMENT_WINDOW["open_from"], ENROLMENT_WINDOW["open_until"]
        )
        conn.execute("""
            UPDATE school_profile
            SET enrolment_status = ?, enrolment_school_year = ?,
                enrolment_open_from = ?, enrolment_open_until = ?,
                enrolment_source_id = ?
            WHERE school_id = ?
        """, (
            status, ENROLMENT_WINDOW["school_year"],
            ENROLMENT_WINDOW["open_from"], ENROLMENT_WINDOW["open_until"],
            row["id"], row["school_id"],
        ))'''

    if old_call not in text:
        log("ATTENZIONE: blocco UPDATE school_profile non trovato come "
            "atteso, controllo manuale necessario in "
            "run_school_profile_pipeline.py")
        return

    text = text.replace(old_call, new_call)
    path.write_text(text, encoding="utf-8")
    log("run_school_profile_pipeline.py: stato iscrizioni ora calcolato "
        "dinamicamente (OPEN/CLOSED/UPCOMING) invece che fisso a CLOSED.")


# ---------------------------------------------------------------------
# 2. Archivia lo script rotto/superato
# ---------------------------------------------------------------------
def archive_broken_script():
    src = BASE_DIR / "scripts" / "broken" / "populate_school_profile.py"
    if not src.exists():
        log("scripts/broken/populate_school_profile.py già assente, salto.")
        return

    archive_dir = BASE_DIR / "scripts" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    dest = archive_dir / src.name
    src.rename(dest)

    note = archive_dir / "README.md"
    note.write_text(
        "# Script archiviati\n\n"
        "`populate_school_profile.py` è la versione precedente di "
        "`run_school_profile_pipeline.py`. Fa la stessa cosa in modo meno "
        "completo (niente reset dei campi derivati, niente log di "
        "riepilogo). Tenuto qui solo per riferimento: valutare se "
        "cancellarlo definitivamente.\n",
        encoding="utf-8",
    )

    broken_dir = BASE_DIR / "scripts" / "broken"
    try:
        broken_dir.rmdir()
    except OSError:
        pass

    log("scripts/broken/populate_school_profile.py spostato in "
        "scripts/archive/ (superato da run_school_profile_pipeline.py).")


# ---------------------------------------------------------------------
# 3. Sposta gli script "patch" fuori dalla root
# ---------------------------------------------------------------------
def move_maintenance_scripts():
    names = ["fix_ptof_selection.py", "patch_school_header.py"]
    maint_dir = BASE_DIR / "scripts" / "maintenance"

    moved = []
    for name in names:
        src = BASE_DIR / name
        if not src.exists():
            continue
        maint_dir.mkdir(parents=True, exist_ok=True)
        dest = maint_dir / name
        src.rename(dest)
        moved.append(name)

    if not moved:
        log("Script di manutenzione già spostati, salto.")
        return

    note = maint_dir / "README.md"
    note.write_text(
        "# Script di manutenzione una tantum\n\n"
        "Patch applicate a mano una volta sola su `docs/js/app.js` o sui "
        "dati, non parte della pipeline regolare eseguita dal workflow. "
        "Non vengono eseguiti automaticamente: se servono di nuovo, "
        "vanno lanciati manualmente e poi si verifica il diff prodotto.\n",
        encoding="utf-8",
    )
    log(f"Spostati in scripts/maintenance/: {', '.join(moved)}")


# ---------------------------------------------------------------------
# 4. README.md
# ---------------------------------------------------------------------
def write_readme():
    path = BASE_DIR / "README.md"
    if path.exists():
        log("README.md già presente, non sovrascrivo.")
        return

    content = """# School Intelligence

Analisi parametrica delle scuole secondarie di primo grado delle Marche,
costruita a partire da fonti ufficiali (anagrafe scuole del MIM e PTOF
pubblicati dagli istituti). Il sito pubblicato è statico e vive in
`docs/`, su GitHub Pages.

**Non è una valutazione della scuola.** È una fotografia documentale
della presenza dichiarata di 21 parametri (lingue, laboratori, servizi,
attività), ricavata dai documenti ufficiali disponibili.

## Come funziona la pipeline

```
src/collectors/   ->  scarica anagrafe MIM e PTOF delle scuole
src/db/            -> costruisce il database SQLite, estrae le evidenze
                       dai PDF, le classifica e assegna i punteggi
src/export/        -> genera i JSON pubblici in docs/data/
docs/               -> frontend statico che legge quei JSON
```

Il file `run_school_profile_pipeline.py` collega i dati raccolti
(dirigente scolastico, stato iscrizioni) al profilo di ogni scuola e
rigenera `docs/data/school_profiles.json`.

## Eseguire la pipeline in locale

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# rigenera database e profili scuola
python run_school_profile_pipeline.py

# esporta i dati pubblici (parametri, punteggi, evidenze)
python -m src.export.export_public_data
```

## Aggiornamento automatico

Il workflow `.github/workflows/update-data.yml` esegue la pipeline ogni
lunedì e committa i dati aggiornati in `data/database/` e `docs/data/`.

## Stati delle evidenze

Ogni parametro analizzato per una scuola può trovarsi in uno di questi
stati, in base al riscontro trovato nei documenti:

- `VERIFIED` — riscontro esplicito e chiaro
- `PROBABLE` — riscontro indiretto o parziale
- `MENTIONED` — menzionato ma senza dettagli sufficienti
- `NOT_FOUND` — nessun riscontro nei documenti analizzati

## Test

```bash
pytest tests/
```
"""
    path.write_text(content, encoding="utf-8")
    log("README.md creato.")


# ---------------------------------------------------------------------
# 5. .gitignore: smetti di versionare il database binario
# ---------------------------------------------------------------------
def update_gitignore():
    path = BASE_DIR / ".gitignore"
    text = path.read_text(encoding="utf-8")

    marker = "# Database SQLite generato dalla pipeline (rigenerato ad ogni run)"
    if marker in text:
        log(".gitignore già aggiornato, salto.")
        return

    addition = f"\n{marker}\ndata/database/*.sqlite\n"
    path.write_text(text + addition, encoding="utf-8")
    log(".gitignore aggiornato: data/database/*.sqlite non verrà più "
        "tracciato per i nuovi commit.")

    # Rimuove il file dal tracking Git senza cancellarlo dal disco,
    # se ci troviamo dentro un repository Git e il file era tracciato.
    db_path = "data/database/school-intelligence.sqlite"
    try:
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", db_path],
            cwd=BASE_DIR, capture_output=True, text=True,
        )
        if tracked.returncode == 0:
            subprocess.run(
                ["git", "rm", "--cached", db_path],
                cwd=BASE_DIR, capture_output=True, text=True,
            )
            log(f"{db_path} rimosso dal tracking Git (resta sul disco).")
    except FileNotFoundError:
        pass  # git non disponibile in questo ambiente, va bene lo stesso


# ---------------------------------------------------------------------
# 6. Workflow: esegui i test prima di rigenerare i dati
# ---------------------------------------------------------------------
def update_workflow():
    path = BASE_DIR / ".github" / "workflows" / "update-data.yml"
    text = path.read_text(encoding="utf-8")

    if "pytest" in text:
        log("Workflow già aggiornato con i test, salto.")
        return

    old = '''      - name: Installa dipendenze
        run: pip install -r requirements.txt

      - name: Collega sources e rigenera school_profiles.json'''

    new = '''      - name: Installa dipendenze
        run: |
          pip install -r requirements.txt
          pip install pytest

      - name: Esegui i test
        run: pytest tests/

      - name: Collega sources e rigenera school_profiles.json'''

    if old not in text:
        log("ATTENZIONE: blocco atteso non trovato nel workflow, "
            "controllo manuale necessario in update-data.yml")
        return

    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    log("Workflow aggiornato: i test girano prima di rigenerare i dati "
        "pubblicati (se falliscono, i dati non vengono committati).")


def main():
    print("Sistemazione repository school-intelligence")
    print("=" * 60)
    fix_enrolment_bug()
    archive_broken_script()
    move_maintenance_scripts()
    write_readme()
    update_gitignore()
    update_workflow()
    print("=" * 60)
    print("Fatto. Controlla le modifiche con 'git status' e 'git diff' "
          "prima di committare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
