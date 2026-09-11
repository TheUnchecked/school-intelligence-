"""
Completa l'integrazione dei dati "classi e alunni" del MIM come
funzionalità MANUALE (opzione A), tenendola fuori dalla pipeline
automatica settimanale.

Motivo: mim_class_enrolment.py legge solo un CSV scaricato a mano dal
MIM (i dati cambiano una volta l'anno, il 31 agosto), quindi non ha
senso — e romperebbe l'azione automatica — provare a eseguirlo ogni
lunedì su GitHub Actions, dove quel file non esiste.

Corregge anche un problema più sottile: l'azione automatica ricostruisce
il database da zero ad ogni run (non lo tiene più in Git). Se
l'esportazione scrivesse comunque school_class_enrolment.json ogni
volta, anche a tabella assente, l'azione automatica sovrascriverebbe
ogni lunedì i dati che hai importato tu a mano con un file vuoto.
Con questa correzione, l'esportazione salta il file quando non ci sono
dati, lasciando intatto quello che hai già pubblicato.

Cosa fa questo script:
  1. Rimuove "MIM class enrolment" dalla lista STEPS di run_pipeline.py
     (se presente): resta fuori dalla pipeline automatica.
  2. Rende export_school_class_enrolment() sicura anche quando la
     tabella non esiste ancora (database rigenerato da zero).
  3. Fa scrivere school_class_enrolment.json SOLO se ci sono dati
     reali, così l'azione automatica non lo svuota ogni settimana.

Flusso d'uso dopo questa correzione, quando esce un nuovo CSV MIM
(una volta l'anno, fine agosto):
    1. Scarica il CSV dal MIM sul tuo dispositivo
    2. python3 -m src.collectors.mim_class_enrolment
    3. python3 -m src.export.export_public_data
    4. git add docs/data/school_class_enrolment.json
       git commit -m "chore: aggiorna dati classi/alunni MIM"
       git push

Uso:
    python finalize_class_enrolment.py

Da eseguire nella cartella radice del repository. È idempotente.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def log(msg):
    print(f"- {msg}")


# ---------------------------------------------------------------------
# 1. Rimuove il passo dalla pipeline automatica
# ---------------------------------------------------------------------
def remove_from_automatic_pipeline():
    path = BASE_DIR / "run_pipeline.py"
    if not path.exists():
        log("run_pipeline.py non trovato, salto.")
        return

    text = path.read_text(encoding="utf-8")

    old = '    ("School profile pipeline", "run_school_profile_pipeline"),\n' \
          '    ("MIM class enrolment", "src.collectors.mim_class_enrolment"),\n' \
          '    ("PTOF version comparison", "src.db.compare_ptof_versions"),'

    new = '    ("School profile pipeline", "run_school_profile_pipeline"),\n' \
          '    ("PTOF version comparison", "src.db.compare_ptof_versions"),'

    if old not in text:
        if '"MIM class enrolment"' in text:
            log("ATTENZIONE: la riga 'MIM class enrolment' è presente "
                "ma non nel punto atteso, controllo manuale necessario "
                "in run_pipeline.py")
        else:
            log("run_pipeline.py: 'MIM class enrolment' già assente "
                "dalla pipeline automatica, salto.")
        return

    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    log("run_pipeline.py: 'MIM class enrolment' rimosso dalla pipeline "
        "automatica — resta una funzionalità manuale.")


# ---------------------------------------------------------------------
# 2 e 3. Esportazione sicura: tabella assente = nessun file scritto
# ---------------------------------------------------------------------
def fix_export_function():
    path = BASE_DIR / "src" / "export" / "export_public_data.py"
    if not path.exists():
        log("src/export/export_public_data.py non trovato, salto.")
        return

    text = path.read_text(encoding="utf-8")

    if "def export_school_class_enrolment" not in text:
        log("export_public_data.py: la funzione "
            "export_school_class_enrolment non esiste ancora, "
            "nessuna correzione da applicare.")
        return

    marker_done = "# manteniamo i dati già pubblicati"
    if marker_done in text:
        log("export_public_data.py: correzione già applicata, salto.")
        return

    old_func = '''def export_school_class_enrolment(conn):
    rows = conn.execute(
        """
        SELECT
            e.school_id,
            e.school_code,
            e.school_year,
            e.course_year,
            e.classes,
            e.male,
            e.female,
            e.students,
            e.source_url,
            e.retrieved_at
        FROM school_class_enrolment e
        ORDER BY
            e.school_id,
            e.school_year DESC,
            e.course_year
        """
    ).fetchall()

    return [dict(row) for row in rows]'''

    new_func = '''def export_school_class_enrolment(conn):
    # La tabella esiste solo dopo che qualcuno ha importato a mano un
    # CSV MIM (src.collectors.mim_class_enrolment): non fa parte della
    # pipeline automatica. Sul runner GitHub, dove il database viene
    # ricostruito da zero ad ogni run, la tabella non c'è quasi mai:
    # in quel caso ritorniamo None per dire "non toccare il file
    # pubblicato", invece di sovrascriverlo con dati vuoti.
    table_exists = conn.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type = 'table' AND name = 'school_class_enrolment'
        """
    ).fetchone()

    if not table_exists:
        return None

    rows = conn.execute(
        """
        SELECT
            e.school_id,
            e.school_code,
            e.school_year,
            e.course_year,
            e.classes,
            e.male,
            e.female,
            e.students,
            e.source_url,
            e.retrieved_at
        FROM school_class_enrolment e
        ORDER BY
            e.school_id,
            e.school_year DESC,
            e.course_year
        """
    ).fetchall()

    return [dict(row) for row in rows]'''

    if old_func not in text:
        log("ATTENZIONE: corpo di export_school_class_enrolment diverso "
            "da quello atteso, controllo manuale necessario in "
            "src/export/export_public_data.py")
        return

    text = text.replace(old_func, new_func)

    old_call = '''        class_enrolment = export_school_class_enrolment(conn)

        write_json(
            "school_class_enrolment.json",
            class_enrolment
        )

        print(
            f"  school_class_enrolment.json: "
            f"{len(class_enrolment)}"
        )'''

    new_call = '''        class_enrolment = export_school_class_enrolment(conn)

        if class_enrolment is None:
            # manteniamo i dati già pubblicati: nessuna tabella in
            # questo run, quindi non tocchiamo il file esistente.
            print(
                "  school_class_enrolment.json: tabella assente, "
                "file esistente lasciato invariato"
            )
        else:
            write_json(
                "school_class_enrolment.json",
                class_enrolment
            )

            print(
                f"  school_class_enrolment.json: "
                f"{len(class_enrolment)}"
            )'''

    if old_call not in text:
        log("ATTENZIONE: chiamata a export_school_class_enrolment non "
            "trovata come atteso, controllo manuale necessario in "
            "src/export/export_public_data.py")
        return

    text = text.replace(old_call, new_call)
    path.write_text(text, encoding="utf-8")
    log("export_public_data.py: l'esportazione ora lascia intatto "
        "school_class_enrolment.json quando la tabella non esiste, "
        "invece di svuotarlo ad ogni run automatico.")


def main():
    print("Integrazione dati classi/alunni MIM — modalità manuale")
    print("=" * 60)
    remove_from_automatic_pipeline()
    fix_export_function()
    print("=" * 60)
    print("Fatto. Controlla 'git diff' prima di committare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
