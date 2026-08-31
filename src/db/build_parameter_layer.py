from pathlib import Path
import sqlite3
from datetime import datetime, timezone


BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "school-intelligence.sqlite"
)


# ============================================================
# PARAMETER CATALOG
# ============================================================

PARAMETERS = [

    # --------------------------------------------------------
    # LINGUE
    # --------------------------------------------------------

    {
        "code": "INGLESE",
        "category": "LINGUE",
        "name": "Inglese",
        "description": "Presenza di offerta o evidenza relativa alla lingua inglese.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "FRANCESE",
        "category": "LINGUE",
        "name": "Francese",
        "description": "Presenza di offerta o evidenza relativa alla lingua francese.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "SPAGNOLO",
        "category": "LINGUE",
        "name": "Spagnolo",
        "description": "Presenza di offerta o evidenza relativa alla lingua spagnola.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "TEDESCO",
        "category": "LINGUE",
        "name": "Tedesco",
        "description": "Presenza di offerta o evidenza relativa alla lingua tedesca.",
        "value_type": "BOOLEAN",
    },

    # --------------------------------------------------------
    # DIDATTICA
    # --------------------------------------------------------

    {
        "code": "ARTE",
        "category": "DIDATTICA",
        "name": "Arte",
        "description": "Evidenze relative ad arte e attività artistiche.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "STEM",
        "category": "DIDATTICA",
        "name": "STEM",
        "description": "Attività, percorsi o iniziative STEM.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "TEATRO",
        "category": "DIDATTICA",
        "name": "Teatro",
        "description": "Attività, laboratori o percorsi teatrali.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "SPORT",
        "category": "DIDATTICA",
        "name": "Sport",
        "description": "Attività sportive o percorsi motori.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "PNRR",
        "category": "DIDATTICA",
        "name": "PNRR",
        "description": "Evidenze di interventi o attività finanziate/collegate al PNRR.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "TEMPO_SCUOLA",
        "category": "ORGANIZZAZIONE",
        "name": "Tempo scuola",
        "description": "Informazioni relative all'orario e al tempo scuola.",
        "value_type": "TEXT",
    },

    {
        "code": "INDIRIZZO_MUSICALE",
        "category": "DIDATTICA",
        "name": "Indirizzo musicale",
        "description": "Presenza di un indirizzo o percorso musicale.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "STRUMENTI_MUSICALI",
        "category": "DIDATTICA",
        "name": "Strumenti musicali",
        "description": "Evidenze relative agli strumenti musicali disponibili o insegnati.",
        "value_type": "BOOLEAN",
    },

    # --------------------------------------------------------
    # STRUTTURE
    # --------------------------------------------------------

    {
        "code": "BIBLIOTECA",
        "category": "STRUTTURE",
        "name": "Biblioteca",
        "description": "Presenza di biblioteca scolastica.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "PALESTRA",
        "category": "STRUTTURE",
        "name": "Palestra",
        "description": "Presenza di palestra o struttura sportiva.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "MENSA",
        "category": "SERVIZI",
        "name": "Mensa",
        "description": "Presenza di servizio mensa/refezione.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "LABORATORIO_INFORMATICA",
        "category": "STRUTTURE",
        "name": "Laboratorio informatica",
        "description": "Presenza di laboratorio o aula informatica.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "LABORATORIO_SCIENZE",
        "category": "STRUTTURE",
        "name": "Laboratorio scienze",
        "description": "Presenza di laboratorio scientifico.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "LABORATORIO_MUSICALE",
        "category": "STRUTTURE",
        "name": "Laboratorio musicale",
        "description": "Presenza di laboratorio musicale.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "LABORATORIO_ARTISTICO",
        "category": "STRUTTURE",
        "name": "Laboratorio artistico",
        "description": "Presenza di laboratorio artistico.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "ATELIER_DIGITALE",
        "category": "STRUTTURE",
        "name": "Atelier digitale",
        "description": "Presenza di atelier digitale o spazio equivalente.",
        "value_type": "BOOLEAN",
    },

    {
        "code": "AULE_MULTIMEDIALI",
        "category": "STRUTTURE",
        "name": "Aule multimediali",
        "description": "Presenza di aule o spazi multimediali.",
        "value_type": "BOOLEAN",
    },
]


LEVEL_PRIORITY = {
    "EXPLICIT": 3,
    "INFERRED": 2,
    "MENTION": 1,
}


# ============================================================
# HELPERS
# ============================================================

def normalize(value):
    if value is None:
        return ""

    return str(value).strip()


def status_from_evidence(evidence_type, confidence):
    evidence_type = normalize(evidence_type).upper()

    try:
        confidence = float(confidence or 0)
    except (TypeError, ValueError):
        confidence = 0

    if evidence_type == "EXPLICIT" and confidence >= 70:
        return "VERIFIED"

    if evidence_type == "EXPLICIT":
        return "PROBABLE"

    if evidence_type == "INFERRED" and confidence >= 70:
        return "PROBABLE"

    if evidence_type == "INFERRED":
        return "MENTIONED"

    return "MENTIONED"


def rank_evidence(row):
    evidence_type = normalize(
        row["evidence_type"]
    ).upper()

    try:
        confidence = float(
            row["confidence"] or 0
        )
    except (TypeError, ValueError):
        confidence = 0

    return (
        LEVEL_PRIORITY.get(
            evidence_type,
            0
        ),
        confidence,
        len(
            normalize(row["evidence"])
        ),
        row["id"],
    )


# ============================================================
# SCHEMA
# ============================================================

def create_schema(conn):

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS parameter_definitions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            code TEXT NOT NULL UNIQUE,

            category TEXT NOT NULL,

            name TEXT NOT NULL,

            description TEXT,

            value_type TEXT NOT NULL,

            active INTEGER NOT NULL DEFAULT 1,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS school_parameters (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            school_id INTEGER NOT NULL,

            parameter_id INTEGER NOT NULL,

            value TEXT,

            normalized_value TEXT,

            value_type TEXT NOT NULL,

            confidence REAL NOT NULL DEFAULT 0,

            status TEXT NOT NULL,

            evidence_count INTEGER NOT NULL DEFAULT 0,

            primary_evidence_id INTEGER,

            primary_document_id INTEGER,

            updated_at TEXT NOT NULL,

            FOREIGN KEY (school_id)
                REFERENCES schools(id)
                ON DELETE CASCADE,

            FOREIGN KEY (parameter_id)
                REFERENCES parameter_definitions(id)
                ON DELETE CASCADE,

            UNIQUE (
                school_id,
                parameter_id
            )
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS parameter_evidence (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            school_parameter_id INTEGER NOT NULL,

            evidence_id INTEGER NOT NULL,

            role TEXT NOT NULL DEFAULT 'SUPPORTING',

            created_at TEXT NOT NULL,

            FOREIGN KEY (school_parameter_id)
                REFERENCES school_parameters(id)
                ON DELETE CASCADE,

            FOREIGN KEY (evidence_id)
                REFERENCES school_features(id)
                ON DELETE CASCADE,

            UNIQUE (
                school_parameter_id,
                evidence_id
            )
        )
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_parameter_definitions_category
        ON parameter_definitions(category)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_school_parameters_school
        ON school_parameters(school_id)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_school_parameters_parameter
        ON school_parameters(parameter_id)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_school_parameters_status
        ON school_parameters(status)
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_parameter_evidence_parameter
        ON parameter_evidence(school_parameter_id)
        """
    )

    conn.commit()


# ============================================================
# PARAMETER DEFINITIONS
# ============================================================

def populate_definitions(conn):

    now = datetime.now(
        timezone.utc
    ).isoformat()

    for parameter in PARAMETERS:

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
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, 1, ?, ?)

            ON CONFLICT(code)
            DO UPDATE SET
                category = excluded.category,
                name = excluded.name,
                description = excluded.description,
                value_type = excluded.value_type,
                active = 1,
                updated_at = excluded.updated_at
            """,
            (
                parameter["code"],
                parameter["category"],
                parameter["name"],
                parameter["description"],
                parameter["value_type"],
                now,
                now,
            ),
        )

    conn.commit()


# ============================================================
# BUILD PARAMETER MATRIX
# ============================================================

def build_parameters(conn):

    print()
    print("Costruzione school_parameters...")

    # --------------------------------------------------------
    # Pulizia del solo parameter layer.
    #
    # NON TOCCA school_features.
    # --------------------------------------------------------

    conn.execute(
        "DELETE FROM parameter_evidence"
    )

    conn.execute(
        "DELETE FROM school_parameters"
    )

    conn.commit()

    schools = conn.execute(
        """
        SELECT id
        FROM schools
        ORDER BY id
        """
    ).fetchall()

    definitions = conn.execute(
        """
        SELECT
            id,
            code,
            value_type
        FROM parameter_definitions
        WHERE active = 1
        ORDER BY id
        """
    ).fetchall()

    evidence_rows = conn.execute(
        """
        SELECT
            id,
            school_id,
            feature,
            value,
            normalized_value,
            confidence,
            evidence_type,
            document_id,
            evidence
        FROM school_features
        ORDER BY school_id, id
        """
    ).fetchall()

    evidence_by_key = {}

    for row in evidence_rows:

        key = (
            row["school_id"],
            normalize(
                row["feature"]
            ).upper(),
        )

        evidence_by_key.setdefault(
            key,
            []
        ).append(row)

    now = datetime.now(
        timezone.utc
    ).isoformat()

    created = 0
    linked = 0

    # --------------------------------------------------------
    # CREA UNA RIGA PER OGNI SCUOLA × PARAMETRO
    #
    # Questo rende il dataset completo.
    #
    # NOT_FOUND = nessuna evidenza trovata.
    # NON significa "la scuola non possiede la feature".
    # --------------------------------------------------------

    for school in schools:

        school_id = school["id"]

        for definition in definitions:

            parameter_id = definition["id"]
            code = definition["code"]
            value_type = definition["value_type"]

            rows = evidence_by_key.get(
                (
                    school_id,
                    code,
                ),
                []
            )

            rows = sorted(
                rows,
                key=rank_evidence,
                reverse=True
            )

            evidence_count = len(rows)

            if not rows:

                status = "NOT_FOUND"
                value = None
                normalized_value = None
                confidence = 0
                primary_evidence_id = None
                primary_document_id = None

            else:

                best = rows[0]

                status = status_from_evidence(
                    best["evidence_type"],
                    best["confidence"]
                )

                if value_type == "BOOLEAN":

                    value = "SI"
                    normalized_value = "SI"

                else:

                    value = normalize(
                        best["value"]
                    )

                    if not value:
                        value = normalize(
                            best["evidence"]
                        )

                    normalized_value = normalize(
                        best["normalized_value"]
                    )

                    if not normalized_value:
                        normalized_value = value.lower()

                confidence = float(
                    best["confidence"] or 0
                )

                primary_evidence_id = best["id"]
                primary_document_id = best["document_id"]

            cursor = conn.execute(
                """
                INSERT INTO school_parameters (
                    school_id,
                    parameter_id,
                    value,
                    normalized_value,
                    value_type,
                    confidence,
                    status,
                    evidence_count,
                    primary_evidence_id,
                    primary_document_id,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    school_id,
                    parameter_id,
                    value,
                    normalized_value,
                    value_type,
                    confidence,
                    status,
                    evidence_count,
                    primary_evidence_id,
                    primary_document_id,
                    now,
                ),
            )

            school_parameter_id = cursor.lastrowid

            created += 1

            for index, evidence in enumerate(rows):

                role = (
                    "PRIMARY"
                    if index == 0
                    else "SUPPORTING"
                )

                conn.execute(
                    """
                    INSERT INTO parameter_evidence (
                        school_parameter_id,
                        evidence_id,
                        role,
                        created_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        school_parameter_id,
                        evidence["id"],
                        role,
                        now,
                    ),
                )

                linked += 1

    conn.commit()

    print(
        "Righe school_parameters:",
        created
    )

    print(
        "Link parameter_evidence:",
        linked
    )


# ============================================================
# REPORT
# ============================================================

def report(conn):

    print()
    print("=" * 80)
    print("PARAMETER LAYER")
    print("=" * 80)

    parameters = conn.execute(
        """
        SELECT
            pd.code,
            pd.category,
            COUNT(sp.id) AS schools,
            SUM(
                CASE
                    WHEN sp.status = 'VERIFIED'
                    THEN 1 ELSE 0
                END
            ) AS verified,
            SUM(
                CASE
                    WHEN sp.status = 'PROBABLE'
                    THEN 1 ELSE 0
                END
            ) AS probable,
            SUM(
                CASE
                    WHEN sp.status = 'MENTIONED'
                    THEN 1 ELSE 0
                END
            ) AS mentioned,
            SUM(
                CASE
                    WHEN sp.status = 'NOT_FOUND'
                    THEN 1 ELSE 0
                END
            ) AS not_found
        FROM parameter_definitions pd
        LEFT JOIN school_parameters sp
            ON sp.parameter_id = pd.id
        WHERE pd.active = 1
        GROUP BY
            pd.id,
            pd.code,
            pd.category
        ORDER BY
            pd.category,
            pd.code
        """
    ).fetchall()

    print()

    for row in parameters:

        print(
            f"{row['category']:15} | "
            f"{row['code']:25} | "
            f"verified={row['verified']:2} "
            f"probable={row['probable']:2} "
            f"mentioned={row['mentioned']:2} "
            f"not_found={row['not_found']:2}"
        )

    print()

    totals = conn.execute(
        """
        SELECT
            COUNT(*) AS total,
            SUM(
                CASE
                    WHEN status = 'VERIFIED'
                    THEN 1 ELSE 0
                END
            ) AS verified,
            SUM(
                CASE
                    WHEN status = 'PROBABLE'
                    THEN 1 ELSE 0
                END
            ) AS probable,
            SUM(
                CASE
                    WHEN status = 'MENTIONED'
                    THEN 1 ELSE 0
                END
            ) AS mentioned,
            SUM(
                CASE
                    WHEN status = 'NOT_FOUND'
                    THEN 1 ELSE 0
                END
            ) AS not_found
        FROM school_parameters
        """
    ).fetchone()

    print(
        "Righe totali       :",
        totals["total"]
    )

    print(
        "VERIFIED           :",
        totals["verified"]
    )

    print(
        "PROBABLE           :",
        totals["probable"]
    )

    print(
        "MENTIONED          :",
        totals["mentioned"]
    )

    print(
        "NOT_FOUND          :",
        totals["not_found"]
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("SCHOOL INTELLIGENCE - PARAMETER LAYER")
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

        create_schema(conn)

        populate_definitions(conn)

        build_parameters(conn)

        report(conn)

        print()
        print("=" * 80)
        print("PARAMETER LAYER COMPLETATO")
        print("=" * 80)
        print()
        print("Le 1.032 evidence originali NON sono state modificate.")
        print("Layer parametrico creato correttamente.")

        return 0

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
