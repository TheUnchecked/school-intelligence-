from pathlib import Path

p = Path("docs/js/app.js")
text = p.read_text(encoding="utf-8")

start = text.find('    $("detailContent").innerHTML = `')
end = text.find('        <section class="detail-overview">', start)

if start == -1 or end == -1:
    raise SystemExit("ERRORE: blocco detailContent non trovato")

old_header = text[start:end]

new_header = r'''    const schoolPtofs =
        ptofDocuments
            .filter(
                document =>
                    document.school_id === schoolId
            );

    const currentPtof =
        schoolPtofs.find(
            document =>
                String(document.title || "")
                    .toUpperCase()
                    .includes("PTOF 2025-2028")
                &&
                !String(document.title || "")
                    .toUpperCase()
                    .includes("PREDISPOSIZIONE")
        ) ||
        schoolPtofs.find(
            document =>
                String(document.title || "")
                    .toUpperCase()
                    .includes("PTOF")
        );

    $("detailContent").innerHTML = `

        <div class="detail-header">

            <span class="eyebrow">
                ${escapeHtml(
                    school.codice_scuola
                )}
            </span>

            <h1>
                ${escapeHtml(
                    school.denominazione
                )}
            </h1>

            <div class="detail-meta">

                ${escapeHtml(
                    school.comune
                )}

                ·

                ${escapeHtml(
                    school.provincia
                )}

                ${
                    school.indirizzo
                        ? ` · ${escapeHtml(school.indirizzo)}`
                        : ""
                }

            </div>

        </div>


'''

text = text[:start] + new_header + text[end:]

# ------------------------------------------------------------
# PTOF: inseriscilo subito dopo detail-overview
# ------------------------------------------------------------

marker = '''        </section>


        <section class="detail-provenance">'''

if marker not in text:
    raise SystemExit(
        "ERRORE: punto inserimento PTOF non trovato"
    )

ptof_block = r'''
        </section>


        <section class="detail-ptof">

            <div class="detail-ptof-heading">

                <div>
                    <span class="eyebrow">
                        DOCUMENTO PRINCIPALE
                    </span>

                    <h2>
                        PTOF
                    </h2>
                </div>

                ${
                    currentPtof
                        ? `
                            <span class="detail-ptof-year">
                                ${escapeHtml(
                                    currentPtof.school_year || ""
                                )}
                            </span>
                          `
                        : ""
                }

            </div>


            ${
                currentPtof
                    ? `
                        <div class="detail-ptof-card">

                            <div class="detail-ptof-info">

                                <strong>
                                    ${escapeHtml(
                                        currentPtof.title ||
                                        "PTOF"
                                    )}
                                </strong>

                                <span>
                                    Documento principale
                                </span>

                            </div>

                            <a
                                class="detail-ptof-button"
                                href="${escapeHtml(
                                    currentPtof.url
                                )}"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                Apri / scarica PTOF
                                ↗
                            </a>

                        </div>
                      `
                    : `
                        <div class="detail-ptof-empty">
                            Nessun PTOF disponibile per questa scuola.
                        </div>
                      `
            }

        </section>


        <section class="detail-provenance">'''

text = text.replace(
    marker,
    ptof_block,
    1
)

p.write_text(text, encoding="utf-8")

print("OK: header + PTOF aggiornati")
print("Righe app.js:", len(text.splitlines()))
