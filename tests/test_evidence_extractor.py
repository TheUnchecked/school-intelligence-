from src.db.evidence_extractor import extract_from_text


def features(result):
    return {item["feature"] for item in result}


def get_feature(result, feature):
    return [
        item for item in result
        if item["feature"] == feature
    ]


def test_indirizzo_musicale():
    text = """
    La scuola secondaria di primo grado offre
    un percorso a indirizzo musicale.
    """

    result = extract_from_text(text)

    items = get_feature(result, "INDIRIZZO_MUSICALE")

    assert items
    assert any(
        item["evidence_type"] == "EXPLICIT"
        for item in items
    )


def test_strumenti_musicali_aggregati():
    text = """
    La scuola propone un percorso ad indirizzo musicale.
    Le specialità strumentali sono:
    pianoforte, tromba, sassofono e fisarmonica.
    """

    result = extract_from_text(text)

    items = get_feature(result, "STRUMENTI_MUSICALI")

    assert items

    values = " ".join(
        item["value"].lower()
        for item in items
    )

    assert "pianoforte" in values
    assert "tromba" in values
    assert "sassofono" in values
    assert "fisarmonica" in values


def test_musica_generica_non_diventa_indirizzo():
    text = """
    Gli alunni partecipano ad attività musicali
    e ascolto di brani.
    """

    result = extract_from_text(text)

    assert "INDIRIZZO_MUSICALE" not in features(result)


def test_laboratorio_informatico_esplicito():
    text = """
    Nel plesso sono presenti un laboratorio informatico,
    aule multimediali e strumenti digitali.
    """

    result = extract_from_text(text)

    items = get_feature(
        result,
        "LABORATORIO_INFORMATICA",
    )

    assert items

    assert any(
        item["evidence_type"] == "EXPLICIT"
        for item in items
    )


def test_stem():
    text = """
    Il laboratorio informatico utilizza strumenti digitali
    per sviluppare competenze STEM e attività di problem solving.
    """

    result = extract_from_text(text)

    assert "STEM" in features(result)


def test_inglese():
    text = """
    L'istituto propone attività di potenziamento
    della lingua inglese e certificazioni Cambridge.
    """

    result = extract_from_text(text)

    assert "INGLESE" in features(result)


def test_mensa():
    text = """
    La scuola dispone di un servizio di refezione
    scolastica con sala mensa.
    """

    result = extract_from_text(text)

    items = get_feature(result, "MENSA")

    assert items

    assert any(
        item["evidence_type"] == "EXPLICIT"
        for item in items
    )


def test_palestra():
    text = """
    L'edificio scolastico dispone di una palestra
    per le attività sportive.
    """

    result = extract_from_text(text)

    assert "PALESTRA" in features(result)


def test_biblioteca():
    text = """
    L'istituto dispone di una biblioteca scolastica
    a disposizione degli studenti.
    """

    result = extract_from_text(text)

    assert "BIBLIOTECA" in features(result)


def test_pnrr():
    text = """
    Il progetto è finanziato nell'ambito del PNRR
    e del Piano Scuola 4.0.
    """

    result = extract_from_text(text)

    assert "PNRR" in features(result)


def test_massimo_tre_evidence_per_feature():
    text = """
    La scuola dispone di una palestra.
    La palestra è utilizzata dagli studenti.
    Sono presenti attività sportive.
    La palestra viene utilizzata anche per eventi.
    """

    result = extract_from_text(text)

    for feature in features(result):
        items = get_feature(result, feature)
        assert len(items) <= 3
