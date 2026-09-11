
import sqlite3
from pathlib import Path


def test_mim_class_enrolment_schema():
    root = Path(__file__).resolve().parents[1]
    db = root / "data/database/school-intelligence.sqlite"

    conn = sqlite3.connect(db)

    try:
        columns = {
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(school_class_enrolment)"
            )
        }

        # Il test è compatibile anche prima del primo import:
        # verifica solo quando la tabella esiste.
        if columns:
            required = {
                "school_id",
                "school_code",
                "school_year",
                "course_year",
                "classes",
                "male",
                "female",
                "students",
            }

            assert required <= columns

    finally:
        conn.close()
