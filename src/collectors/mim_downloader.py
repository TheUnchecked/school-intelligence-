from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
import hashlib
import json
import re

import requests
import yaml
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_FILE = BASE_DIR / "config" / "config.yaml"

CATALOG_BASE = (
    "https://dati.istruzione.it/opendata/opendata/catalog/"
)


def load_config():
    with CONFIG_FILE.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise RuntimeError("Configurazione YAML non valida.")

    if "mim" not in config:
        raise RuntimeError("Sezione 'mim' mancante nel config.yaml.")

    return config


def sha256_file(path):
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def discover_json(dataset, school_year, session):
    """
    Cerca nel catalogo MIM il JSON relativo all'anno richiesto.
    """

    year_code = school_year.replace("/", "")

    catalog_url = (
        f"{CATALOG_BASE}"
        f"{dataset}/{dataset}{year_code}"
        f"20250901.rdf"
    )

    response = session.get(
        catalog_url,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    candidates = []

    for a in soup.find_all("a", href=True):

        href = a["href"]

        if not href.lower().endswith(".json"):
            continue

        if year_code not in href:
            continue

        candidates.append(
            urljoin(response.url, href)
        )

    if not candidates:
        raise RuntimeError(
            f"Nessun JSON trovato per {dataset} {school_year}"
        )

    # Preferiamo il primo link JSON trovato.
    return candidates[0]


def download_json(url, destination, session):
    response = session.get(
        url,
        timeout=120,
        stream=True,
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type",
        ""
    ).lower()

    # Non accettiamo HTML mascherato da JSON.
    if "html" in content_type:
        raise RuntimeError(
            f"Download rifiutato: server ha restituito "
            f"{content_type}, non JSON."
        )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with destination.open("wb") as f:
        for chunk in response.iter_content(
            chunk_size=1024 * 1024
        ):
            if chunk:
                f.write(chunk)

    # Validazione effettiva del JSON.
    try:
        with destination.open(
            "r",
            encoding="utf-8-sig",
        ) as f:
            data = json.load(f)
    except Exception as exc:
        destination.unlink(missing_ok=True)

        raise RuntimeError(
            f"Il file scaricato non è JSON valido: {exc}"
        )

    return data, content_type


def process_dataset(
    name,
    dataset,
    school_year,
    session,
):
    print()
    print("=" * 70)
    print(f"DATASET: {name.upper()}")
    print(f"ANNO:    {school_year}")
    print("=" * 70)

    url = discover_json(
        dataset,
        school_year,
        session,
    )

    print("JSON trovato:")
    print(url)
    print()

    year_folder = school_year.replace("/", "-")

    destination = (
        BASE_DIR
        / "data"
        / "raw"
        / "mim"
        / year_folder
        / f"{name}.json"
    )

    data, content_type = download_json(
        url,
        destination,
        session,
    )

    size = destination.stat().st_size
    checksum = sha256_file(destination)

    # Cerchiamo una struttura comune nei JSON.
    records = None

    if isinstance(data, list):
        records = data

    elif isinstance(data, dict):

        for key in (
            "data",
            "results",
            "records",
            "items",
        ):
            if isinstance(data.get(key), list):
                records = data[key]
                break

    print("Download:       OK")
    print("Content-Type:   ", content_type)
    print(f"File:           {destination}")
    print(f"Dimensione:     {size / 1024 / 1024:.2f} MB")
    print("SHA256:         ", checksum)

    if records is not None:
        print("Record stimati: ", len(records))
    else:
        print(
            "Record:          struttura JSON da analizzare"
        )

    return {
        "dataset": dataset,
        "name": name,
        "school_year": school_year,
        "url": url,
        "file": str(destination),
        "content_type": content_type,
        "size_bytes": size,
        "sha256": checksum,
        "downloaded_at": datetime.now().isoformat(),
    }


def main():

    config = load_config()

    school_year = config["mim"]["school_year"]

    session = requests.Session()

    session.headers.update(
        {
            "User-Agent": "SchoolIntelligence/0.1",
            "Accept": "application/json",
        }
    )

    manifest = []

    datasets = {
        "statali": "SCUANAGRAFESTAT",
        "paritarie": "SCUANAGRAFEPAR",
    }

    for name, dataset in datasets.items():

        try:

            result = process_dataset(
                name,
                dataset,
                school_year,
                session,
            )

            manifest.append(result)

        except Exception as exc:

            print()
            print("ERROR:")
            print(exc)

    manifest_file = (
        BASE_DIR
        / "data"
        / "raw"
        / "mim"
        / school_year.replace("/", "-")
        / "manifest.json"
    )

    manifest_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with manifest_file.open(
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            manifest,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print()
    print("=" * 70)
    print("MANIFEST")
    print("=" * 70)
    print(manifest_file)


if __name__ == "__main__":
    main()
