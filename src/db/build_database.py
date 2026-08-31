from pathlib import Path
import sqlite3
import re
import unicodedata
from urllib.parse import urlparse

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "school-intelligence.sqlite"
)

RAW_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "mim"
    / "2025-26"
)


COMUNI_TARGET = {
    "OSIMO",
    "CASTELFIDARDO",
    "RECANATI",
    "POTENZA PICENA",
    "LORETO",
    "CIVITANOVA MARCHE",
    "NUMANA",
}


def clean(value):
    if pd.isna(value):
        return None

    value = str(value).strip()

    if not value:
        return None

    return value


def normalize_text(value):
    value = clean(value)

    if not value:
        return None

    value = unicodedata.normalize(
        "NFKD",
        value
    ).encode(
        "ascii",
        "ignore"
    ).decode()

    value = re.sub(r"\s+", " ", value)

    return value.strip().upper()


def normalize_url(value):
    value = clean(value)

    if not value:
        return None

    value = value.strip()

    if value.lower() in {
        "non disponibile",
        "nd",
        "n.d.",
        "-",
    }:
        return None

    if not re.match(r"^https?://", value, re.I):
        value = "https://" + value

    parsed = urlparse(value)

    if not parsed.netloc:
        return None

    return value


def first_column(df, *names):
    for name in names:
        if name in df.columns:
            return name

    return None


def get_value(row, *names):
    column = first_column(row.to_frame().T, *names)

    if column is None:
        return None

    return clean(row[column])


def create_schema(conn):

    conn.executescript(
        """
        PRAGMA journal_mode = WAL;
        PRAGMA foreign_keys = ON;
        PRAGMA synchronous = NORMAL;

        DROP TABLE IF EXISTS school_features;
        DROP TABLE IF EXISTS ptof_documents;
        DROP TABLE IF EXISTS sources;
        DROP TABLE IF EXISTS schools;

        CREATE TABLE schools (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            school_year TEXT NOT NULL,

            sector TEXT NOT NULL
                CHECK (sector IN ('STATALE', 'PARITARIA')),

            codice_scuola TEXT NOT NULL,
            codice_istituto TEXT,

            denominazione TEXT NOT NULL,
            denominazione_normalized TEXT,

            regione TEXT,
            provincia TEXT,

            comune TEXT NOT NULL,
            comune_normalized TEXT,

            indirizzo TEXT,
            cap TEXT,
            codice_comune TEXT,

            tipologia TEXT,
            caratteristica TEXT,

            email TEXT,
            pec TEXT,
            website TEXT,

            sede_scolastica TEXT,

            source_dataset TEXT NOT NULL,

            created_at TEXT
                DEFAULT CURRENT_TIMESTAMP,

            updated_at TEXT
                DEFAULT CURRENT_TIMESTAMP,

            UNIQUE (
                school_year,
                sector,
                codice_scuola
            )
        );


        CREATE INDEX idx_schools_comune
            ON schools(comune_normalized);

        CREATE INDEX idx_schools_codice
            ON schools(codice_scuola);

        CREATE INDEX idx_schools_istituto
            ON schools(codice_istituto);

        CREATE INDEX idx_schools_sector
            ON schools(sector);

        CREATE INDEX idx_schools_year
            ON schools(school_year);


        CREATE TABLE sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            school_id INTEGER NOT NULL,

            source_type TEXT NOT NULL,

            url TEXT NOT NULL,

            title TEXT,

            retrieved_at TEXT,

            content_hash TEXT,

            local_path TEXT,

            status TEXT,

            notes TEXT,

            FOREIGN KEY (school_id)
                REFERENCES schools(id)
                ON DELETE CASCADE
        );


        CREATE INDEX idx_sources_school
            ON sources(school_id);

        CREATE INDEX idx_sources_type
            ON sources(source_type);


        CREATE TABLE ptof_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            school_id INTEGER NOT NULL,

            school_year TEXT,

            url TEXT,

            title TEXT,

            local_path TEXT,

            sha256 TEXT,

            retrieved_at TEXT,

            status TEXT,

            document_date TEXT,

            pages INTEGER,

            FOREIGN KEY (school_id)
                REFERENCES schools(id)
                ON DELETE CASCADE
        );


        CREATE INDEX idx_ptof_school
            ON ptof_documents(school_id);

        CREATE INDEX idx_ptof_year
            ON ptof_documents(school_year);


        CREATE TABLE school_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            school_id INTEGER NOT NULL,

            feature TEXT NOT NULL,

            value TEXT,

            normalized_value TEXT,

            source_id INTEGER,

            evidence TEXT,

            confidence REAL,

            verified_at TEXT,

            FOREIGN KEY (school_id)
                REFERENCES schools(id)
                ON DELETE CASCADE,

            FOREIGN KEY (source_id)
                REFERENCES sources(id)
                ON DELETE SET NULL
        );


        CREATE INDEX idx_features_school
            ON school_features(school_id);

        CREATE INDEX idx_features_feature
            ON school_features(feature);

        CREATE INDEX idx_features_value
            ON school_features(normalized_value);


        CREATE VIRTUAL TABLE schools_fts
        USING fts5(
            codice_scuola,
            denominazione,
            comune,
            indirizzo,
            content='schools',
            content_rowid='id'
        );


        CREATE TABLE crawl_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            school_id INTEGER NOT NULL,

            url TEXT NOT NULL,

            resource_type TEXT NOT NULL,

            priority INTEGER DEFAULT 100,

            status TEXT DEFAULT 'PENDING',

            attempts INTEGER DEFAULT 0,

            last_attempt TEXT,

            http_status INTEGER,

            error TEXT,

            FOREIGN KEY (school_id)
                REFERENCES schools(id)
                ON DELETE CASCADE
        );


        CREATE INDEX idx_crawl_status
            ON crawl_queue(status);

        CREATE INDEX idx_crawl_school
            ON crawl_queue(school_id);

        CREATE INDEX idx_crawl_priority
            ON crawl_queue(priority);
        """
    )


def import_dataset(conn, filename, sector):

    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(path)

    print()
    print("=" * 70)
    print(f"IMPORT: {sector}")
    print("=" * 70)

    df = pd.read_csv(
        path,
        dtype=str,
        encoding="utf-8",
    )

    print("Record RAW:", len(df))

    # Normalizzazione colonne
    df.columns = [
        str(c).strip().upper()
        for c in df.columns
    ]

    required = [
        "CODICESCUOLA",
        "DENOMINAZIONESCUOLA",
        "DESCRIZIONECOMUNE",
        "DESCRIZIONETIPOLOGIAGRADOISTRUZIONESCUOLA",
    ]

    missing = [
        col
        for col in required
        if col not in df.columns
    ]

    if missing:
        raise RuntimeError(
            f"Colonne mancanti in {filename}: {missing}"
        )

    # Filtro territoriale
    df["COMUNE_NORM"] = (
        df["DESCRIZIONECOMUNE"]
        .map(normalize_text)
    )

    df = df[
        df["COMUNE_NORM"].isin(
            {
                normalize_text(x)
                for x in COMUNI_TARGET
            }
        )
    ].copy()

    # Filtro secondaria I grado
    df["TIPOLOGIA_NORM"] = (
        df[
            "DESCRIZIONETIPOLOGIAGRADOISTRUZIONESCUOLA"
        ]
        .map(normalize_text)
    )

    df = df[
        df["TIPOLOGIA_NORM"].str.contains(
            "PRIMO GRADO",
            na=False,
        )
    ].copy()

    print(
        "Record importati dopo filtro:",
        len(df)
    )

    inserted = 0
    skipped = 0

    for _, row in df.iterrows():

        codice_scuola = get_value(
            row,
            "CODICESCUOLA",
        )

        denominazione = get_value(
            row,
            "DENOMINAZIONESCUOLA",
        )

        if not codice_scuola or not denominazione:
            skipped += 1
            continue

        values = (
            get_value(
                row,
                "ANNOSCOLASTICO",
            ),

            sector,

            codice_scuola,

            get_value(
                row,
                "CODICEISTITUTORIFERIMENTO",
            ),

            denominazione,

            normalize_text(
                denominazione
            ),

            get_value(
                row,
                "REGIONE",
            ),

            get_value(
                row,
                "PROVINCIA",
            ),

            get_value(
                row,
                "DESCRIZIONECOMUNE",
            ),

            normalize_text(
                get_value(
                    row,
                    "DESCRIZIONECOMUNE",
                )
            ),

            get_value(
                row,
                "INDIRIZZOSCUOLA",
            ),

            get_value(
                row,
                "CAPSCUOLA",
            ),

            get_value(
                row,
                "CODICECOMUNESCUOLA",
            ),

            get_value(
                row,
                "DESCRIZIONETIPOLOGIAGRADOISTRUZIONESCUOLA",
            ),

            get_value(
                row,
                "DESCRIZIONECARATTERISTICASCUOLA",
            ),

            get_value(
                row,
                "INDIRIZZOEMAILSCUOLA",
            ),

            get_value(
                row,
                "INDIRIZZOPECSCUOLA",
            ),

            normalize_url(
                get_value(
                    row,
                    "SITOWEBSCUOLA",
                )
            ),

            get_value(
                row,
                "SEDESCOLASTICA",
            ),

            filename.replace(
                ".csv",
                ""
            ),
        )

        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO schools (
                school_year,
                sector,
                codice_scuola,
                codice_istituto,
                denominazione,
                denominazione_normalized,
                regione,
                provincia,
                comune,
                comune_normalized,
                indirizzo,
                cap,
                codice_comune,
                tipologia,
                caratteristica,
                email,
                pec,
                website,
                sede_scolastica,
                source_dataset
            )
            VALUES (
                ?,?,?,?,?,?,?,?,?,?,
                ?,?,?,?,?,?,?,?,?,?
            )
            """,
            values,
        )

        if cursor.rowcount:
            inserted += 1
        else:
            skipped += 1

    print("Inseriti:", inserted)
    print("Saltati:", skipped)


def create_crawl_queue(conn):

    conn.execute(
        """
        INSERT INTO crawl_queue (
            school_id,
            url,
            resource_type,
            priority
        )
        SELECT
            id,
            website,
            'SCHOOL_WEBSITE',
            10
        FROM schools
        WHERE website IS NOT NULL
        """
    )


def rebuild_fts(conn):

    conn.execute(
        """
        INSERT INTO schools_fts(
            rowid,
            codice_scuola,
            denominazione,
            comune,
            indirizzo
        )
        SELECT
            id,
            codice_scuola,
            denominazione,
            comune,
            indirizzo
        FROM schools
        """
    )


def main():

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if DB_PATH.exists():
        print("Database esistente:", DB_PATH)
        print("Verrà ricreato.")

    conn = sqlite3.connect(DB_PATH)

    try:

        create_schema(conn)

        import_dataset(
            conn,
            "statali.csv",
            "STATALE",
        )

        import_dataset(
            conn,
            "paritarie.csv",
            "PARITARIA",
        )

        create_crawl_queue(conn)

        rebuild_fts(conn)

        conn.commit()

        print()
        print("=" * 70)
        print("DATABASE CREATO")
        print("=" * 70)

        total = conn.execute(
            "SELECT COUNT(*) FROM schools"
        ).fetchone()[0]

        statali = conn.execute(
            """
            SELECT COUNT(*)
            FROM schools
            WHERE sector = 'STATALE'
            """
        ).fetchone()[0]

        paritarie = conn.execute(
            """
            SELECT COUNT(*)
            FROM schools
            WHERE sector = 'PARITARIA'
            """
        ).fetchone()[0]

        queue = conn.execute(
            "SELECT COUNT(*) FROM crawl_queue"
        ).fetchone()[0]

        print("Database:", DB_PATH)
        print("Scuole:", total)
        print("Statali:", statali)
        print("Paritarie:", paritarie)
        print("URL in crawl queue:", queue)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
