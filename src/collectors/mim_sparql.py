from pathlib import Path
import requests
import json


BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "mim"
    / "2025-26"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


ENDPOINT = (
    "https://dati.istruzione.it/"
    "opendata/opendata/sparql/endpoint/query/"
)


DATASETS = {
    "statali": "SCUANAGRAFESTAT",
    "paritarie": "SCUANAGRAFEPAR",
}


QUERY = """
SELECT ?s ?p ?o
WHERE {
    ?s ?p ?o .
}
LIMIT 10
"""


def test_dataset(name, dataset):

    print()
    print("=" * 70)
    print(f"DATASET: {name.upper()}")
    print("=" * 70)

    params = {
        "query": QUERY,
        "format": "json",
        "dataset": dataset,
        "area": "Scuole",
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/sparql-results+json, application/json",
    }

    response = requests.get(
        ENDPOINT,
        params=params,
        headers=headers,
        timeout=60,
    )

    print("STATUS:", response.status_code)
    print("CONTENT-TYPE:", response.headers.get("Content-Type"))
    print("FINAL URL:", response.url)

    content_type = response.headers.get(
        "Content-Type",
        ""
    ).lower()

    if "html" in content_type:
        print()
        print("ERROR: il server ha restituito HTML invece di JSON.")
        print()
        print("PRIME 500 CARATTERI:")
        print(response.text[:500])
        return

    response.raise_for_status()

    try:
        data = response.json()
    except ValueError:
        print("ERROR: risposta non JSON")
        print(response.text[:500])
        return

    output = OUTPUT_DIR / f"{name}_sparql_test.json"

    with output.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )

    bindings = (
        data
        .get("results", {})
        .get("bindings", [])
    )

    print()
    print("JSON ricevuto: OK")
    print("Risultati:", len(bindings))
    print("File:", output)


def main():

    print("=" * 70)
    print("MIM SPARQL CONNECTIVITY TEST")
    print("=" * 70)

    for name, dataset in DATASETS.items():
        test_dataset(name, dataset)


if __name__ == "__main__":
    main()
