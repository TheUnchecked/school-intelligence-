from pathlib import Path
import sqlite3
import re
from datetime import datetime, timezone


# =============================================================================
# CONFIG
# =============================================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = (
    BASE_DIR
    / "data"
    / "database"
    / "school-intelligence.sqlite"
)

PTOF_DIR = (
    BASE_DIR
    / "data"
    / "documents"
    / "ptof"
)

SNIPPET_RADIUS = 220
MAX_EVIDENCE_PER_FEATURE_DOCUMENT = 3


# =============================================================================
# FEATURE PATTERNS
# =============================================================================
#
# IMPORTANT:
# I pattern sono intenzionalmente abbastanza specifici.
# Una semplice presenza della parola non deve automaticamente diventare
# una forte evidence.
#

FEATURE_PATTERNS = {

    "TEMPO_SCUOLA": [
        r"\b\d{2}\s*ore\s*(settimanali|settimanale)\b",
        r"\btempo\s+(normale|ordinario|prolungato)\b",
        r"\bsettimana\s+corta\b",
        r"\btempo\s+scuola\b",
        r"\bquadro\s+orario\b",
        r"\borario\s+settimanale\b",
    ],

    "INDIRIZZO_MUSICALE": [
        r"indirizzo\s+musicale",
        r"percorso\s+a\s+indirizzo\s+musicale",
        r"scuola\s+secondaria.*indirizzo\s+musicale",
        r"corso\s+.*musicale",
    ],

    "STRUMENTI_MUSICALI": [
        r"strumenti?\s*:\s*[^.\n]{5,150}",
        r"specialità\s+(strumentali|che\s+proponiamo)",
        r"pianoforte",
        r"violino",
        r"violoncello",
        r"chitarra",
        r"flauto",
        r"clarinetto",
        r"sassofono",
        r"tromba",
        r"fisarmonica",
    ],

    "INGLESE": [
        r"\blinglese\b",
        r"lingua\s+inglese",
        r"certificazioni\s+linguistiche.*inglese",
        r"potenziamento.*inglese",
        r"english\s+lab",
        r"cambridge",
    ],

    "FRANCESE": [
        r"\bfrancese\b",
        r"lingua\s+francese",
        r"potenziamento.*francese",
    ],

    "SPAGNOLO": [
        r"\bspagnolo\b",
        r"lingua\s+spagnola",
        r"potenziamento.*spagnolo",
    ],

    "TEDESCO": [
        r"\btedesco\b",
        r"lingua\s+tedesca",
        r"potenziamento.*tedesco",
    ],

    "MENSA": [
        r"\bmensa\b",
        r"servizio\s+di\s+refezione",
        r"refezione\s+scolastica",
        r"sala\s+mensa",
    ],

    "PALESTRA": [
        r"\bpalestra\b",
        r"strutture\s+sportive.*palestra",
        r"spazi\s+sportivi",
    ],

    "BIBLIOTECA": [
        r"\bbiblioteca\b",
        r"biblioteche\s+scolastiche",
        r"biblioteca\s+scolastica",
    ],

    "LABORATORIO_INFORMATICA": [
        r"laboratorio\s+di\s+informatica",
        r"laboratori[io]*\s+informatica",
        r"\baula\s+informatica\b",
        r"laboratorio\s+informatico",
    ],

    "LABORATORIO_SCIENZE": [
        r"laboratorio\s+di\s+scienze",
        r"laboratorio\s+scientifico",
        r"\baula\s+di\s+scienze\b",
        r"\baula\s+scienze\b",
    ],

    "LABORATORIO_ARTISTICO": [
        r"laboratorio\s+artistico",
        r"laboratorio\s+d['’]arte",
        r"\baula\s+d['’]arte\b",
    ],

    "LABORATORIO_MUSICALE": [
        r"laboratorio\s+musicale",
        r"\baula\s+musica\b",
        r"laboratorio\s+di\s+musica",
    ],

    "AULE_MULTIMEDIALI": [
        r"aula\s+multimediale",
        r"aule\s+multimediali",
        r"spazio\s+multimediale",
        r"laboratorio\s+multimediale",
    ],

    "ATELIER_DIGITALE": [
        r"atelier\s+digitale",
        r"atelier\s+digitale\s+creativo",
        r"ambienti\s+.*digitali",
    ],

    "STEM": [
        r"\bstem\b",
        r"scienza,\s*tecnologia,\s*ingegneria,\s*matematica",
        r"spazi\s+e\s+strumenti\s+digitali\s+per\s+le\s+stem",
    ],

    "SPORT": [
        r"pratica\s+sportiva",
        r"attività\s+sportive",
        r"laboratori\s+sportivi",
        r"discipline\s+sportive",
        r"avviamento\s+alla\s+pratica\s+sportiva",
    ],

    "TEATRO": [
        r"\bteatro\b",
        r"attività\s+teatrali",
        r"progetto\s+teatrale",
        r"rassegna\s+teatrale",
    ],

    "ARTE": [
        r"\barte\b",
        r"educazione\s+artistica",
        r"linguaggi\s+dell['’]arte",
        r"attività\s+artistiche",
    ],

    "PNRR": [
        r"\bpnrr\b",
        r"piano\s+nazionale\s+di\s+ripresa\s+e\s+resilienza",
        r"scuola\s+4\.0",
    ],
}


# =============================================================================
# NORMALIZATION
# =============================================================================

def normalize_text(text: str) -> str:
    """
    Normalizzazione leggera:
    - lowercase
    - normalizza apostrofi
    - comprime gli spazi
    """
    text = text.replace("’", "'")
    text = text.replace("\r", "\n")

    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.lower()


def clean_snippet(text: str) -> str:
    """
    Ripulisce il frammento mantenendo il contenuto utile.
    """
    text = text.replace("\r", " ")
    text = text.replace("\n", " ")

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =============================================================================
# CONTEXT QUALITY
# =============================================================================


def context_quality(feature: str, snippet: str) -> int:
    """
    Valuta la qualità semantica del contesto.

    La presenza della keyword non è sufficiente:
    distinguiamo contesto curricolare da reale offerta/struttura.
    """

    s = snippet.lower()

    school_terms = [
        "istituto",
        "scuola",
        "plesso",
        "alunni",
        "studenti",
        "offerta formativa",
        "progetto",
        "percorso",
        "attività",
        "laboratorio",
        "aule",
        "spazi",
        "strutture",
    ]

    quality = sum(1 for term in school_terms if term in s)

    # Contesto esplicitamente curricolare.
    curriculum_terms = [
        "curricolo",
        "curricolo verticale",
        "obiettivi di apprendimento",
        "traguardi per lo sviluppo",
        "disciplina di riferimento",
        "discipline coinvolte",
        "contenuti annuali",
        "competenze chiave",
        "insegnamenti e quadri orario",
        "arte e immagine",
        "lingua inglese",
        "seconda lingua comunitaria",
    ]

    if any(term in s for term in curriculum_terms):
        quality -= 2

    # Contesto fortemente indicativo di offerta/struttura.
    offer_terms = [
        "dispone di",
        "dispongono di",
        "è presente",
        "sono presenti",
        "dotato di",
        "dotate di",
        "offre",
        "offrono",
        "propone",
        "proponiamo",
        "attiva",
        "attivazione",
        "prevede",
        "prevedono",
        "potenziamento",
        "extracurricolare",
        "lettorato",
        "corso",
        "corsi",
    ]

    if any(term in s for term in offer_terms):
        quality += 3

    return max(0, quality)


def classify_evidence(feature: str, snippet: str, matched_text: str):
    """
    Classificazione semantica dell'evidence.

    EXPLICIT:
        la feature è direttamente dichiarata nel contesto.

    INFERRED:
        il contesto supporta fortemente la feature, ma non contiene
        una dichiarazione sufficientemente diretta.

    MENTION:
        semplice presenza della keyword o riferimento debole.

    PRINCIPIO:
        un marker generico come "sono presenti" NON rende automaticamente
        esplicita qualsiasi feature presente nello stesso snippet.
    """

    s = snippet.lower()
    m = matched_text.lower()

    quality = context_quality(feature, s)

    # -----------------------------------------------------------------
    # 1. FEATURE DIRETTAMENTE DICHIARATA
    # -----------------------------------------------------------------

    direct_patterns = {

        "INDIRIZZO_MUSICALE": [
            r"\bindirizzo\s+musicale\b",
            r"\bpercorso\s+(?:a|ad)\s+indirizzo\s+musicale\b",
        ],

        "STRUMENTI_MUSICALI": [
            r"\bspecialit[aà]\s+strumentali\b",
            r"\bstrumenti?\s*:",
            r"\bstrumento\s*:",
        ],

        "TEMPO_SCUOLA": [
            r"\btempo\s+(?:normale|prolungato|ordinario)\b",
            r"\b\d{2}\s*ore\s+settimanali\b",
            r"\bore\s+settimanali\b",
            r"\borario\s+settimanale\b",
            r"\bquadro\s+orario\b",
        ],

        "MENSA": [
            r"\bservizio\s+di\s+refezione\b",
            r"\brefezione\s+scolastica\b",
            r"\bservizio\s+mensa\b",
            r"\bmensa\s+scolastica\b",
        ],

        "PALESTRA": [
            r"\bpalestra\b",
            r"\bstrutture\s+sportive\b",
        ],

        "BIBLIOTECA": [
            r"\bbiblioteca(?:\s+scolastica)?\b",
            r"\bbiblioteche\s+scolastiche\b",
        ],

        "LABORATORIO_INFORMATICA": [
            r"\blaboratorio\s+(?:di\s+)?informatica\b",
            r"\blaboratori\s+(?:di\s+)?informatica\b",
            r"\baula\s+informatica\b",
        ],

        "LABORATORIO_SCIENZE": [
            r"\blaboratorio\s+(?:di\s+)?scienze\b",
            r"\blaboratorio\s+scientifico\b",
            r"\baula\s+(?:di\s+)?scienze\b",
        ],

        "LABORATORIO_ARTISTICO": [
            r"\blaboratorio\s+artistico\b",
            r"\blaboratorio\s+d['’]arte\b",
            r"\baula\s+d['’]arte\b",
        ],

        "LABORATORIO_MUSICALE": [
            r"\blaboratorio\s+musicale\b",
            r"\blaboratorio\s+di\s+musica\b",
            r"\baula\s+musica\b",
        ],

        "AULE_MULTIMEDIALI": [
            r"\baula\s+multimediale\b",
            r"\baule\s+multimediali\b",
            r"\bspazio\s+multimediale\b",
            r"\bspazi\s+multimediali\b",
        ],

        "ATELIER_DIGITALE": [
            r"\batelier\s+digitale\b",
            r"\batelier\s+digitale\s+creativo\b",
        ],

        "STEM": [
            r"\bprogetti?\s+stem\b",
            r"\battività\s+stem\b",
            r"\bcompetenze\s+stem\b",
            r"\bpercorsi?\s+stem\b",
            r"\bazioni\s+.*\bstem\b",
        ],

        "SPORT": [
            r"\battivit[aà]\s+sportive\b",
            r"\bpratica\s+sportiva\b",
            r"\bdiscipline\s+sportive\b",
            r"\blaboratori\s+sportivi\b",
        ],

        "TEATRO": [
            r"\battivit[aà]\s+teatrali\b",
            r"\bprogetto\s+teatrale\b",
            r"\brassegna\s+teatrale\b",
            r"\blaboratorio\s+di\s+teatro\b",
        ],

        "ARTE": [
            r"\beducazione\s+artistica\b",
            r"\blinguaggi\s+dell['’]arte\b",
            r"\battivit[aà]\s+artistiche\b",
            r"\bprogetti?\s+.*\barte\b",
        ],

        "PNRR": [
            r"\bpiano\s+nazionale\s+di\s+ripresa\s+e\s+resilienza\b",
            r"\bscuola\s+4\.0\b",
            r"\bpnrr\s+(?:dm|19|65)\b",
        ],
    }

    # -----------------------------------------------------------------
    # Lingue: dichiarazione esplicita quando compare in un contesto
    # didattico/offerta, non semplicemente in un testo curricolare.
    # -----------------------------------------------------------------

    language_terms = {
        "INGLESE": [
            r"\blingua\s+inglese\b",
            r"\bpotenziamento\s+.*inglese\b",
            r"\bcertificazioni\s+.*inglese\b",
            r"\bcorsi\s+.*inglese\b",
            r"\blettorat[oi]\s+.*inglese\b",
            r"\benglish\s+lab\b",
            r"\bcambridge\b",
        ],

        "FRANCESE": [
            r"\blingua\s+francese\b",
            r"\bpotenziamento\s+.*francese\b",
            r"\bcorsi\s+.*francese\b",
            r"\blettorat[oi]\s+.*francese\b",
        ],

        "SPAGNOLO": [
            r"\blingua\s+spagnola\b",
            r"\bpotenziamento\s+.*spagnolo\b",
            r"\bcorsi\s+.*spagnolo\b",
            r"\blettorat[oi]\s+.*spagnolo\b",
        ],

        "TEDESCO": [
            r"\blingua\s+tedesca\b",
            r"\bpotenziamento\s+.*tedesco\b",
            r"\bcorsi\s+.*tedesco\b",
        ],
    }

    patterns = direct_patterns.get(feature, [])

    if feature in language_terms:
        patterns = language_terms[feature]

    # -----------------------------------------------------------------
    # Match diretto della feature.
    # -----------------------------------------------------------------

    if any(re.search(pattern, s, flags=re.IGNORECASE) for pattern in patterns):

        # Una dichiarazione che corrisponde a un pattern specifico
        # della feature è già un'indicazione sufficiente.
        #
        # Il contesto scolastico resta richiesto solo quando la feature
        # è identificata esclusivamente da una keyword generica.
        #
        # In questo modo un riferimento valido presente in una sezione
        # curricolare non viene perso solo perché il testo non contiene
        # marker come "offre", "propone" o "dispone di".
        specific_patterns = (
            direct_patterns.get(feature, [])
            or language_terms.get(feature, [])
        )

        is_specific = any(
            re.search(
                pattern,
                s,
                flags=re.IGNORECASE,
            )
            for pattern in specific_patterns
        )

        if quality >= 1 or is_specific:
            return "EXPLICIT", 100

    # -----------------------------------------------------------------
    # Strumenti musicali:
    # se troviamo strumenti concreti vicino a un contesto musicale,
    # l'elenco è una evidence esplicita.
    # -----------------------------------------------------------------

    if feature == "STRUMENTI_MUSICALI":

        instruments = [
            "pianoforte",
            "violino",
            "violoncello",
            "chitarra",
            "flauto",
            "clarinetto",
            "sassofono",
            "tromba",
            "fisarmonica",
            "percussioni",
        ]

        found = [
            instrument
            for instrument in instruments
            if re.search(
                rf"\b{re.escape(instrument)}\b",
                s,
                flags=re.IGNORECASE,
            )
        ]

        if found and any(
            x in s
            for x in [
                "indirizzo musicale",
                "specialità strumentali",
                "specialita strumentali",
                "strumenti:",
                "strumento:",
            ]
        ):
            return "EXPLICIT", 100

    # -----------------------------------------------------------------
    # Dichiarazioni strutturali feature-specifiche.
    #
    # Esempio:
    #   "Nel plesso sono presenti un laboratorio informatico..."
    #
    # Qui il marker strutturale è valido perché è riferito direttamente
    # alla feature, non semplicemente presente nello stesso snippet.
    # -----------------------------------------------------------------

    structural_patterns = {
        "LABORATORIO_INFORMATICA": [
            r"(?:sono|è)\s+presenti?\s+(?:un\s+)?laboratorio\s+informatico",
            r"dispone\s+di\s+(?:un\s+)?laboratorio\s+informatico",
            r"(?:sono|è)\s+dotati?\s+di\s+(?:un\s+)?laboratorio\s+informatico",
        ],

        "LABORATORIO_SCIENZE": [
            r"(?:sono|è)\s+presenti?\s+(?:un\s+)?laboratorio\s+(?:di\s+)?scienze",
            r"dispone\s+di\s+(?:un\s+)?laboratorio\s+(?:di\s+)?scienze",
        ],

        "LABORATORIO_ARTISTICO": [
            r"(?:sono|è)\s+presenti?\s+(?:un\s+)?laboratorio\s+artistico",
            r"dispone\s+di\s+(?:un\s+)?laboratorio\s+artistico",
        ],

        "LABORATORIO_MUSICALE": [
            r"(?:sono|è)\s+presenti?\s+(?:un\s+)?laboratorio\s+musicale",
            r"dispone\s+di\s+(?:un\s+)?laboratorio\s+musicale",
        ],

        "AULE_MULTIMEDIALI": [
            r"(?:sono|è)\s+presenti?\s+(?:un[ae]?\s+)?aule?\s+multimediali?",
            r"dispone\s+di\s+(?:un[ae]?\s+)?aule?\s+multimediali?",
        ],

        "ATELIER_DIGITALE": [
            r"(?:sono|è)\s+presenti?.{0,80}\batelier\s+digitale",
            r"dispone\s+di.{0,80}\batelier\s+digitale",
        ],
    }

    for pattern in structural_patterns.get(feature, []):
        if re.search(pattern, s, flags=re.IGNORECASE):
            return "EXPLICIT", 100

    # -----------------------------------------------------------------
    # Inferenza forte.
    # -----------------------------------------------------------------

    inference_markers = [
        "offerta formativa",
        "ampliamento dell'offerta",
        "percorso",
        "attività",
        "progetto",
        "progetti",
        "potenziamento",
        "insegnamento",
        "curricolo",
        "laboratori",
        "laboratorio",
        "spazi e attrezzature",
        "ricognizione attrezzature",
        "attrezzature e infrastrutture",
    ]

    if quality >= 2 and any(
        marker in s
        for marker in inference_markers
    ):
        return "INFERRED", 70

    # -----------------------------------------------------------------
    # Fallback.
    # -----------------------------------------------------------------

    if quality >= 1:
        return "MENTION", 40

    return "MENTION", 40


# =============================================================================
# SNIPPET EXTRACTION
# =============================================================================

def build_snippet(text: str, start: int, end: int) -> str:
    """
    Costruisce un contesto intorno al match.

    Preferiamo mantenere una finestra abbastanza piccola per evitare che
    una keyword venga attribuita a frasi completamente scollegate.
    """

    left = max(0, start - SNIPPET_RADIUS)
    right = min(len(text), end + SNIPPET_RADIUS)

    snippet = text[left:right]

    return clean_snippet(snippet)


# =============================================================================
# DEDUPLICATION
# =============================================================================

def evidence_key(feature: str, evidence_type: str, snippet: str):
    """
    Chiave di deduplicazione robusta.
    """

    normalized = re.sub(
        r"\s+",
        " ",
        snippet.lower(),
    ).strip()

    # Evitiamo differenze minime di punteggiatura/spazi.
    normalized = re.sub(
        r"[^\w\sàèéìòù']",
        "",
        normalized,
    )

    return (
        feature,
        evidence_type,
        normalized[:500],
    )


# =============================================================================
# EXTRACT
# =============================================================================

def extract_from_text(text: str):

    evidence = []

    text_lower = normalize_text(text)

    # =========================================================================
    # STRUMENTI MUSICALI
    # =========================================================================
    #
    # Gli strumenti musicali sono una feature aggregata.
    #
    # Esempio:
    #
    #   Le specialità strumentali sono:
    #   pianoforte, tromba, sassofono e fisarmonica.
    #
    # deve produrre:
    #
    #   STRUMENTI_MUSICALI
    #   value = pianoforte, tromba, sassofono, fisarmonica
    #
    # Non una evidence separata per ogni strumento.
    # =========================================================================

    instrument_names = [
        "pianoforte",
        "violino",
        "violoncello",
        "chitarra",
        "flauto",
        "clarinetto",
        "sassofono",
        "tromba",
        "fisarmonica",
        "percussioni",
    ]

    musical_context_patterns = [
        r"specialità\s+strumentali",
        r"specialita\s+strumentali",
        r"strumenti\s*:",
        r"strumento\s*:",
        r"indirizzo\s+musicale",
        r"percorso\s+a\s+indirizzo\s+musicale",
        r"percorso\s+ad\s+indirizzo\s+musicale",
        r"corso\s+ad\s+indirizzo\s+musicale",
    ]

    context_match = None

    for pattern in musical_context_patterns:

        match = re.search(
            pattern,
            text_lower,
            flags=re.IGNORECASE,
        )

        if match:
            context_match = match
            break

    if context_match:

        # ---------------------------------------------------------------------
        # Finestra abbastanza ampia da comprendere un elenco multilinea.
        # ---------------------------------------------------------------------

        left = max(
            0,
            context_match.start() - 100,
        )

        right = min(
            len(text_lower),
            context_match.end() + 500,
        )

        musical_snippet = clean_snippet(
            text_lower[left:right]
        )

        found_instruments = []

        for instrument in instrument_names:

            if re.search(
                rf"\b{re.escape(instrument)}\b",
                musical_snippet,
                flags=re.IGNORECASE,
            ):

                if instrument not in found_instruments:
                    found_instruments.append(instrument)

        if found_instruments:

            evidence.append(
                {
                    "feature": "STRUMENTI_MUSICALI",
                    "value": ", ".join(found_instruments),
                    "normalized_value": "STRUMENTI_MUSICALI",
                    "evidence": musical_snippet,
                    "evidence_type": "EXPLICIT",
                    "confidence": 100,
                    "position": context_match.start(),
                }
            )

    # =========================================================================
    # ALTRE FEATURE
    # =========================================================================

    for feature, patterns in FEATURE_PATTERNS.items():

        # Già gestita sopra.
        if feature == "STRUMENTI_MUSICALI":
            continue

        candidates = []

        for pattern in patterns:

            try:

                matches = re.finditer(
                    pattern,
                    text_lower,
                    flags=re.IGNORECASE,
                )

            except re.error:

                continue

            for match in matches:

                start = match.start()
                end = match.end()

                snippet = build_snippet(
                    text_lower,
                    start,
                    end,
                )

                matched_text = match.group(0)

                evidence_type, confidence = classify_evidence(
                    feature,
                    snippet,
                    matched_text,
                )

                if confidence < 40:
                    continue

                candidates.append(
                    {
                        "feature": feature,
                        "value": matched_text.strip(),
                        "normalized_value": feature,
                        "evidence": snippet,
                        "evidence_type": evidence_type,
                        "confidence": confidence,
                        "position": start,
                    }
                )

        # ---------------------------------------------------------------------
        # DEDUPLICAZIONE
        # ---------------------------------------------------------------------

        unique = []
        seen = set()

        for item in candidates:

            key = evidence_key(
                item["feature"],
                item["evidence_type"],
                item["evidence"],
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(item)

        # ---------------------------------------------------------------------
        # PRIORITÀ
        # ---------------------------------------------------------------------

        priority = {
            "EXPLICIT": 3,
            "INFERRED": 2,
            "MENTION": 1,
        }

        unique.sort(
            key=lambda x: (
                priority.get(
                    x["evidence_type"],
                    0,
                ),
                x["confidence"],
                -x["position"],
            ),
            reverse=True,
        )

        unique = unique[
            :MAX_EVIDENCE_PER_FEATURE_DOCUMENT
        ]

        evidence.extend(unique)

    return evidence


# =============================================================================
# DATABASE
# =============================================================================

def get_connection():

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    return conn


def clear_features(conn):

    print("Pulizia school_features...")

    conn.execute(
        "DELETE FROM school_features"
    )

    conn.commit()


def get_documents(conn):

    query = """
        SELECT
            id,
            school_id,
            title,
            local_path
        FROM ptof_documents
        WHERE local_path IS NOT NULL
          AND local_path != ''
        ORDER BY id
    """

    return conn.execute(query).fetchall()


# =============================================================================
# SAVE
# =============================================================================

def save_evidence(
    conn,
    document,
    evidence,
):

    if not evidence:
        return 0

    saved = 0

    retrieved_at = datetime.now(
        timezone.utc
    ).isoformat()

    # Recuperiamo source_id se esiste.
    source_id = None

    row = conn.execute(
        """
        SELECT id
        FROM sources
        WHERE school_id = ?
          AND url = (
              SELECT url
              FROM ptof_documents
              WHERE id = ?
          )
        LIMIT 1
        """,
        (
            document["school_id"],
            document["id"],
        ),
    ).fetchone()

    if row:
        source_id = row["id"]

    for item in evidence:

        conn.execute(
            """
            INSERT INTO school_features (
                school_id,
                feature,
                value,
                normalized_value,
                document_id,
                source_id,
                evidence,
                confidence,
                verified_at,
                evidence_type
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document["school_id"],
                item["feature"],
                item["value"],
                item["normalized_value"],
                document["id"],
                source_id,
                item["evidence"],
                float(item["confidence"]),
                retrieved_at,
                item["evidence_type"],
            ),
        )

        saved += 1

    return saved


# =============================================================================
# PRINT
# =============================================================================

def print_document_summary(
    document,
    evidence,
):

    print("-" * 80)
    print(
        Path(
            document["local_path"]
        ).name
    )
    print("-" * 80)

    print(
        f"Document ID: {document['id']}"
    )

    print(
        f"School ID: {document['school_id']}"
    )

    print(
        f"Titolo: {document['title']}"
    )

    print(
        f"Evidence trovate: {len(evidence)}"
    )

    for item in evidence:

        print(
            f"  [{item['feature']}] "
            f"{item['evidence_type']} "
            f"confidence={item['confidence']}"
        )

        print(
            f"    → {item['evidence'][:220]}"
        )


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("=" * 80)
    print(
        "SCHOOL INTELLIGENCE - "
        "EVIDENCE EXTRACTOR v4"
    )
    print("=" * 80)

    print()
    print(
        f"Database:\n{DB_PATH}"
    )

    if not DB_PATH.exists():

        print(
            "\nERRORE: database non trovato."
        )

        return 1

    if not PTOF_DIR.exists():

        print(
            "\nERRORE: directory PTOF non trovata."
        )

        return 1

    conn = get_connection()

    try:

        # -------------------------------------------------------------
        # CHECK TABLE
        # -------------------------------------------------------------

        table = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
              AND name='school_features'
            """
        ).fetchone()

        if not table:

            print(
                "\nERRORE: tabella school_features "
                "non trovata."
            )

            return 1

        # -------------------------------------------------------------
        # DOCUMENTS
        # -------------------------------------------------------------

        documents = get_documents(conn)

        print()
        print(
            f"Documenti TXT/PTOF: "
            f"{len(documents)}"
        )

        # -------------------------------------------------------------
        # CLEAR
        # -------------------------------------------------------------

        clear_features(conn)

        total_documents = 0
        total_evidence = 0

        # -------------------------------------------------------------
        # PROCESS
        # -------------------------------------------------------------

        for document in documents:

            path = Path(
                document["local_path"]
            )

            # ptof_documents contiene il PDF.
            # Cerchiamo automaticamente il TXT associato.
            txt_path = path.with_suffix(".txt")

            if not txt_path.exists():

                print()
                print(
                    f"SKIP TXT mancante: "
                    f"{txt_path}"
                )

                continue

            try:

                text = txt_path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

            except Exception as exc:

                print()
                print(
                    f"ERRORE lettura "
                    f"{txt_path}: {exc}"
                )

                continue

            evidence = extract_from_text(
                text
            )

            print()

            print_document_summary(
                document,
                evidence,
            )

            saved = save_evidence(
                conn,
                document,
                evidence,
            )

            conn.commit()

            print(
                f"Evidence salvate: {saved}"
            )

            total_documents += 1
            total_evidence += saved

        # -------------------------------------------------------------
        # FINAL
        # -------------------------------------------------------------

        print()
        print("=" * 80)
        print("ESTRAZIONE COMPLETATA")
        print("=" * 80)

        print(
            f"Documenti analizzati : "
            f"{total_documents}"
        )

        print(
            f"Evidence salvate     : "
            f"{total_evidence}"
        )

        return 0

    finally:

        conn.close()


if __name__ == "__main__":

    raise SystemExit(
        main()
    )
