from pathlib import Path
import sqlite3
import json
from datetime import datetime, timezone


BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "school-intelligence.sqlite"
)


# ============================================================
# PARAMETER CATALOG v1
# ============================================================
#
# Il catalogo descrive COME interpretare un parametro.
#
# Non contiene le evidence.
# Non contiene i dati delle singole scuole.
#
# Relazioni:
#
# parameter_definitions
#        ↓
# school_parameters
#        ↓
# parameter_evidence
#        ↓
# school_features
#
# ============================================================

CATALOG = {

    # --------------------------------------------------------
    # LINGUE
    # --------------------------------------------------------

    "INGLESE": {
        "category": "LINGUE",
        "name": "Inglese",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di offerta relativa alla lingua inglese.",
        "evidence_policy": "EXPLICIT_OR_INFERRED",
        "source_priority": "PTOF",
        "scoring_weight": 1.0,
    },

    "FRANCESE": {
        "category": "LINGUE",
        "name": "Francese",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di offerta relativa alla lingua francese.",
        "evidence_policy": "EXPLICIT_OR_INFERRED",
        "source_priority": "PTOF",
        "scoring_weight": 1.0,
    },

    "SPAGNOLO": {
        "category": "LINGUE",
        "name": "Spagnolo",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di offerta relativa alla lingua spagnola.",
        "evidence_policy": "EXPLICIT_OR_INFERRED",
        "source_priority": "PTOF",
        "scoring_weight": 1.0,
    },

    "TEDESCO": {
        "category": "LINGUE",
        "name": "Tedesco",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di offerta relativa alla lingua tedesca.",
        "evidence_policy": "EXPLICIT_OR_INFERRED",
        "source_priority": "PTOF",
        "scoring_weight": 1.0,
    },

    # --------------------------------------------------------
    # DIDATTICA
    # --------------------------------------------------------

    "ARTE": {
        "category": "DIDATTICA",
        "name": "Arte",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di attività o percorsi artistici.",
        "evidence_policy": "EXPLICIT_OR_INFERRED",
        "source_priority": "PTOF",
        "scoring_weight": 1.0,
    },

    "STEM": {
        "category": "DIDATTICA",
        "name": "STEM",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di attività, percorsi o progetti STEM.",
        "evidence_policy": "EXPLICIT_OR_INFERRED",
        "source_priority": "PTOF",
        "scoring_weight": 1.2,
    },

    "TEATRO": {
        "category": "DIDATTICA",
        "name": "Teatro",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di attività teatrali.",
        "evidence_policy": "EXPLICIT_OR_INFERRED",
        "source_priority": "PTOF",
        "scoring_weight": 1.0,
    },

    "SPORT": {
        "category": "DIDATTICA",
        "name": "Sport",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di attività sportive.",
        "evidence_policy": "EXPLICIT_OR_INFERRED",
        "source_priority": "PTOF",
        "scoring_weight": 1.0,
    },

    "PNRR": {
        "category": "DIDATTICA",
        "name": "PNRR",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di attività o interventi collegati al PNRR.",
        "evidence_policy": "EXPLICIT_OR_INFERRED",
        "source_priority": "PTOF",
        "scoring_weight": 0.8,
    },

    "INDIRIZZO_MUSICALE": {
        "category": "DIDATTICA",
        "name": "Indirizzo musicale",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di indirizzo o percorso musicale.",
        "evidence_policy": "EXPLICIT",
        "source_priority": "PTOF",
        "scoring_weight": 1.3,
    },

    "STRUMENTI_MUSICALI": {
        "category": "DIDATTICA",
        "name": "Strumenti musicali",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di strumenti musicali indicati nelle attività o nell'offerta.",
        "evidence_policy": "EXPLICIT",
        "source_priority": "PTOF",
        "scoring_weight": 1.1,
    },

    # --------------------------------------------------------
    # ORGANIZZAZIONE
    # --------------------------------------------------------

    "TEMPO_SCUOLA": {
        "category": "ORGANIZZAZIONE",
        "name": "Tempo scuola",
        "value_type": "TEXT",
        "unit": "ORE_SETTIMANALI",
        "allowed_values": [],
        "description": "Informazioni relative all'orario e al tempo scuola.",
        "evidence_policy": "EXPLICIT",
        "source_priority": "PTOF",
        "scoring_weight": 1.0,
    },

    # --------------------------------------------------------
    # SERVIZI
    # --------------------------------------------------------

    "MENSA": {
        "category": "SERVIZI",
        "name": "Mensa",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di servizio mensa o refezione scolastica.",
        "evidence_policy": "EXPLICIT_OR_INFERRED",
        "source_priority": "PTOF",
        "scoring_weight": 1.3,
    },

    # --------------------------------------------------------
    # STRUTTURE
    # --------------------------------------------------------

    "BIBLIOTECA": {
        "category": "STRUTTURE",
        "name": "Biblioteca",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di biblioteca scolastica.",
        "evidence_policy": "EXPLICIT",
        "source_priority": "PTOF",
        "scoring_weight": 1.0,
    },

    "PALESTRA": {
        "category": "STRUTTURE",
        "name": "Palestra",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di palestra o struttura sportiva.",
        "evidence_policy": "EXPLICIT",
        "source_priority": "PTOF",
        "scoring_weight": 1.2,
    },

    "LABORATORIO_INFORMATICA": {
        "category": "STRUTTURE",
        "name": "Laboratorio informatica",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di laboratorio o aula informatica.",
        "evidence_policy": "EXPLICIT",
        "source_priority": "PTOF",
        "scoring_weight": 1.1,
    },

    "LABORATORIO_SCIENZE": {
        "category": "STRUTTURE",
        "name": "Laboratorio scienze",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di laboratorio scientifico.",
        "evidence_policy": "EXPLICIT",
        "source_priority": "PTOF",
        "scoring_weight": 1.1,
    },

    "LABORATORIO_MUSICALE": {
        "category": "STRUTTURE",
        "name": "Laboratorio musicale",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di laboratorio musicale.",
        "evidence_policy": "EXPLICIT",
        "source_priority": "PTOF",
        "scoring_weight": 1.1,
    },

    "LABORATORIO_ARTISTICO": {
        "category": "STRUTTURE",
        "name": "Laboratorio artistico",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di laboratorio artistico.",
        "evidence_policy": "EXPLICIT",
        "source_priority": "PTOF",
        "scoring_weight": 1.0,
    },

    "ATELIER_DIGITALE": {
        "category": "STRUTTURE",
        "name": "Atelier digitale",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di atelier digitale o ambiente equivalente.",
        "evidence_policy": "EXPLICIT_OR_INFERRED",
        "source_priority": "PTOF",
        "scoring_weight": 1.2,
    },

    "AULE_MULTIMEDIALI": {
        "category": "STRUTTURE",
        "name": "Aule multimediali",
        "value_type": "BOOLEAN",
        "unit": None,
        "allowed_values": ["SI", "NO", "NOT_FOUND"],
        "description": "Presenza di aule o ambienti multimediali.",
        "evidence_policy": "EXPLICIT",
        "source_priority": "PTOF",
        "scoring_weight": 1.1,
    },
}


# ============================================================
# SCHEMA EXTENSION
# ============================================================

def ensure_columns(conn):

    columns = {
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(parameter_definitions)"
        ).fetchall()
    }

    additions = {
        "unit": "TEXT",
        "allowed_values": "TEXT",
        "evidence_policy": "TEXT",
        "source_priority": "TEXT",
        "scoring_weight": "REAL NOT NULL DEFAULT 1.0",
    }

    for name, definition in additions.items():

        if name not in columns:

            conn.execute(
                f"""
                ALTER TABLE parameter_definitions
                ADD COLUMN {name} {definition}
                """
            )

    conn.commit()


# ============================================================
# UPSERT CATALOG
# ============================================================

def populate_catalog(conn):

    now = datetime.now(
        timezone.utc
    ).isoformat()

    updated = 0

    for code, item in CATALOG.items():

        allowed_values = json.dumps(
            item["allowed_values"],
            ensure_ascii=False
        )

        conn.execute(
            """
            INSERT INTO parameter_definitions (
                code,
                category,
                name,
                description,
                value_type,
                active,
                created_at,
                updated_at,
                unit,
                allowed_values,
                evidence_policy,
                source_priority,
                scoring_weight
            )
            VALUES (
                ?, ?, ?, ?, ?, 1, ?, ?,
                ?, ?, ?, ?, ?
            )

            ON CONFLICT(code)
            DO UPDATE SET
                category = excluded.category,
                name = excluded.name,
                description = excluded.description,
                value_type = excluded.value_type,
                active = 1,
                updated_at = excluded.updated_at,
                unit = excluded.unit,
                allowed_values = excluded.allowed_values,
                evidence_policy = excluded.evidence_policy,
                source_priority = excluded.source_priority,
                scoring_weight = excluded.scoring_weight
            """,
            (
                code,
                item["category"],
                item["name"],
                item["description"],
                item["value_type"],
                now,
                now,
                item["unit"],
                allowed_values,
                item["evidence_policy"],
                item["source_priority"],
                item["scoring_weight"],
            )
        )

        updated += 1

    conn.commit()

    return updated


# ============================================================
# REPORT
# ============================================================

def report(conn):

    rows = conn.execute(
        """
        SELECT
            code,
            category,
            value_type,
            unit,
            evidence_policy,
            scoring_weight
        FROM parameter_definitions
        WHERE active = 1
        ORDER BY category, code
        """
    ).fetchall()

    print()
    print("=" * 80)
    print("PARAMETER CATALOG v1")
    print("=" * 80)

    print()

    for row in rows:

        print(
            f"{row['category']:15} | "
            f"{row['code']:25} | "
            f"type={row['value_type']:7} | "
            f"policy={row['evidence_policy']:20} | "
            f"weight={row['scoring_weight']}"
        )

    print()

    count = conn.execute(
        """
        SELECT COUNT(*)
        FROM parameter_definitions
        WHERE active = 1
        """
    ).fetchone()[0]

    print(
        "Parametri attivi:",
        count
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("SCHOOL INTELLIGENCE - PARAMETER CATALOG")
    print("=" * 80)

    if not DB_PATH.exists():

        print(
            "ERRORE: database non trovato:",
            DB_PATH
        )

        return 1

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    try:

        ensure_columns(conn)

        updated = populate_catalog(conn)

        print()
        print(
            "Parametri catalogati:",
            updated
        )

        report(conn)

        print()
        print("=" * 80)
        print("PARAMETER CATALOG COMPLETATO")
        print("=" * 80)

        return 0

    finally:

        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
