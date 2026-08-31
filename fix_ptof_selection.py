from pathlib import Path

p = Path("docs/js/app.js")
text = p.read_text(encoding="utf-8")

start_marker = """    const currentPtof =
"""

start = text.find(start_marker)

if start == -1:
    raise SystemExit("ERRORE: currentPtof non trovato")

end_marker = """    $("detailContent").innerHTML = `
"""

end = text.find(end_marker, start)

if end == -1:
    raise SystemExit("ERRORE: fine blocco currentPtof non trovata")

new_logic = r'''    const currentPtof =
        schoolPtofs
            .map(document => {

                const title =
                    String(document.title || "")
                        .toUpperCase()
                        .replace(/[–—]/g, "-");

                let score = 0;

                // Documento esplicitamente riferito al triennio 2025-2028
                if (
                    title.includes("2025-2028") ||
                    title.includes("2025 - 2028")
                ) {
                    score += 100;
                }

                // PTOF esplicito
                if (title.includes("PTOF")) {
                    score += 50;
                }

                // Documento aggiornato
                if (title.includes("AGGIORNAT")) {
                    score += 10;
                }

                // Escludiamo documenti secondari
                if (title.includes("PREDISPOSIZIONE")) {
                    score -= 1000;
                }

                if (title.includes("ATTO D'INDIRIZZO")) {
                    score -= 1000;
                }

                if (title.includes("ATTO D’INDIRIZZO")) {
                    score -= 1000;
                }

                if (title.includes("SINTESI")) {
                    score -= 500;
                }

                if (title.includes("PRESENTAZIONE")) {
                    score -= 500;
                }

                if (title.includes("ALLEGATO")) {
                    score -= 300;
                }

                return {
                    document,
                    score
                };

            })
            .sort(
                (a, b) =>
                    b.score - a.score
            )
            .map(
                item => item.document
            )[0];

'''

text = (
    text[:start]
    + new_logic
    + text[end:]
)

p.write_text(text, encoding="utf-8")

print("OK: selezione PTOF principale aggiornata")
print("Righe app.js:", len(text.splitlines()))
