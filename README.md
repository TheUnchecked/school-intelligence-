# School Intelligence

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
