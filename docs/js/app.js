const DATA_PATH = "data";

let schools = [];
let scores = [];
let parameters = [];
let schoolParameters = [];
let evidences = [];
let ptofDocuments = [];

const $ = (id) => document.getElementById(id);


async function loadData() {

    const [
        schoolsResponse,
        scoresResponse,
        parametersResponse,
        schoolParametersResponse,
        evidenceResponse,
        ptofDocumentsResponse,
        statisticsResponse
    ] = await Promise.all([
        fetch(`${DATA_PATH}/schools.json`),
        fetch(`${DATA_PATH}/school_scores.json`),
        fetch(`${DATA_PATH}/parameters.json`),
        fetch(`${DATA_PATH}/school_parameters.json`),
        fetch(`${DATA_PATH}/evidence.json`),
        fetch(`${DATA_PATH}/ptof_documents.json`),
        fetch(`${DATA_PATH}/statistics.json`)
    ]);

    schools = await schoolsResponse.json();
    scores = await scoresResponse.json();
    parameters = await parametersResponse.json();
    schoolParameters = await schoolParametersResponse.json();
    evidences = await evidenceResponse.json();
    ptofDocuments = await ptofDocumentsResponse.json();

    const statistics = await statisticsResponse.json();

    $("kpiSchools").textContent =
        statistics.schools;

    $("kpiDocuments").textContent =
        statistics.documents;

    $("kpiEvidence").textContent =
        statistics.evidence.toLocaleString("it-IT");

    $("kpiParameters").textContent =
        statistics.active_parameters;

    $("schoolCount").textContent =
        statistics.schools;

    populateProvinceFilter();

    renderRanking();
}


function populateProvinceFilter() {

    const provinces = [
        ...new Set(
            schools
                .map(s => s.provincia)
                .filter(Boolean)
        )
    ].sort();

    const select = $("provinceFilter");

    for (const province of provinces) {

        const option = document.createElement("option");

        option.value = province;
        option.textContent = province;

        select.appendChild(option);
    }
}


function getMergedSchools() {

    const scoreMap = new Map(
        scores.map(s => [s.school_id, s])
    );

    return schools
        .map(school => ({
            ...school,
            score: scoreMap.get(school.id)
        }))
        .sort(
            (a, b) =>
                (b.score?.score_percent ?? 0) -
                (a.score?.score_percent ?? 0)
        );
}


function renderRanking() {

    const query =
        $("search").value
            .trim()
            .toLowerCase();

    const province =
        $("provinceFilter").value;

    const scoreFilter =
        $("scoreFilter").value;

    let results = getMergedSchools();

    results = results.filter(school => {

        const searchable = [
            school.denominazione,
            school.codice_scuola,
            school.comune,
            school.provincia
        ]
            .filter(Boolean)
            .join(" ")
            .toLowerCase();

        if (
            query &&
            !searchable.includes(query)
        ) {
            return false;
        }

        if (
            province &&
            school.provincia !== province
        ) {
            return false;
        }

        const score =
            school.score?.score_percent ?? 0;

        if (scoreFilter === "0") {
            return score === 0;
        }

        if (scoreFilter) {
            return score >= Number(scoreFilter);
        }

        return true;
    });

    $("resultCount").textContent =
        `${results.length} scuole`;

    const container = $("schoolList");

    container.innerHTML = "";

    let rankedIndex = 0;

    results.forEach((school) => {

        const score =
            school.score;

        const evidenceCount =
            Number(score?.evidence_count ?? 0);

        const hasData =
            evidenceCount > 0;

        const card =
            document.createElement("article");

        card.className =
            hasData
                ? "school-card"
                : "school-card school-card-no-data";

        if (hasData) {
            rankedIndex++;
        }

        const rankLabel =
            hasData
                ? `#${rankedIndex}`
                : "—";

        const scoreValue =
            hasData
                ? formatPercent(score?.score_percent)
                : "Dati insufficienti";

        const scoreLabel =
            hasData
                ? "INDICE COMPLESSIVO"
                : "NON VALUTABILE";

        const statsHtml =
            hasData
                ? `
                    <div class="ranking-stat">
                        <span>Dati disponibili</span>
                        <strong>
                            ${formatPercent(score?.coverage_percent)}
                        </strong>
                    </div>

                    <div class="ranking-stat">
                        <span>Affidabilità dei dati</span>
                        <strong>
                            ${formatPercent(score?.confidence_percent)}
                        </strong>
                    </div>

                    <div class="ranking-stat">
                        <span>Informazioni verificate</span>
                        <strong>
                            ${score?.verified_count ?? 0}
                        </strong>
                    </div>

                    <div class="ranking-stat">
                        <span>Riscontri documentali</span>
                        <strong>
                            ${evidenceCount}
                        </strong>
                    </div>
                `
                : `
                    <div class="ranking-stat ranking-stat-message">
                        <span>Stato della valutazione</span>
                        <strong>
                            Nessun riscontro documentale
                        </strong>
                    </div>

                    <div class="ranking-stat">
                        <span>Parametri da verificare</span>
                        <strong>
                            ${score?.parameter_count ?? 21}
                        </strong>
                    </div>
                `;

        card.innerHTML = `
            <div class="ranking-card">

                <div class="ranking-card-header">

                    <div class="ranking-card-identity">

                        <div class="ranking-rank">
                            ${rankLabel}
                        </div>

                        <div class="ranking-school-name">
                            ${escapeHtml(school.denominazione)}
                        </div>

                        <div class="ranking-school-meta">
                            ${escapeHtml(school.comune)}
                            ·
                            ${escapeHtml(school.provincia)}
                            ·
                            ${escapeHtml(school.codice_scuola)}
                        </div>

                    </div>

                    <div class="ranking-score">

                        <div class="ranking-score-value ${
                            hasData
                                ? ""
                                : "ranking-score-no-data"
                        }">
                            ${scoreValue}
                        </div>

                        <div class="ranking-score-label">
                            ${scoreLabel}
                        </div>

                    </div>

                </div>

                <div class="ranking-stats">
                    ${statsHtml}
                </div>

            </div>
        `;

        card.addEventListener(
            "click",
            () => showDetail(school.id)
        );

        container.appendChild(card);
    });
}





function parameterMeta(code) {

    const meta = {

        INGLESE: {
            label: "Inglese",
            category: "Lingue",
            icon: "🇬🇧"
        },

        FRANCESE: {
            label: "Francese",
            category: "Lingue",
            icon: "🇫🇷"
        },

        SPAGNOLO: {
            label: "Spagnolo",
            category: "Lingue",
            icon: "🇪🇸"
        },

        TEDESCO: {
            label: "Tedesco",
            category: "Lingue",
            icon: "🇩🇪"
        },

        MENSA: {
            label: "Mensa scolastica",
            category: "Servizi",
            icon: "🍽️"
        },

        PALESTRA: {
            label: "Palestra",
            category: "Strutture",
            icon: "🏀"
        },

        BIBLIOTECA: {
            label: "Biblioteca",
            category: "Strutture",
            icon: "📚"
        },

        LABORATORIO_INFORMATICA: {
            label: "Laboratorio di informatica",
            category: "Strutture",
            icon: "💻"
        },

        LABORATORIO_SCIENZE: {
            label: "Laboratorio di scienze",
            category: "Strutture",
            icon: "🧪"
        },

        LABORATORIO_MUSICALE: {
            label: "Laboratorio musicale",
            category: "Strutture",
            icon: "🎵"
        },

        LABORATORIO_ARTISTICO: {
            label: "Laboratorio artistico",
            category: "Strutture",
            icon: "🎨"
        },

        ATELIER_DIGITALE: {
            label: "Atelier digitale",
            category: "Strutture",
            icon: "🖥️"
        },

        AULE_MULTIMEDIALI: {
            label: "Aule multimediali",
            category: "Strutture",
            icon: "📺"
        },

        STEM: {
            label: "STEM",
            category: "Attività e didattica",
            icon: "🔬"
        },

        ARTE: {
            label: "Arte",
            category: "Attività e didattica",
            icon: "🎨"
        },

        TEATRO: {
            label: "Teatro",
            category: "Attività e didattica",
            icon: "🎭"
        },

        SPORT: {
            label: "Sport",
            category: "Attività e didattica",
            icon: "⚽"
        },

        PNRR: {
            label: "Progetti PNRR",
            category: "Attività e didattica",
            icon: "🚀"
        },

        INDIRIZZO_MUSICALE: {
            label: "Indirizzo musicale",
            category: "Attività e didattica",
            icon: "🎼"
        },

        STRUMENTI_MUSICALI: {
            label: "Strumenti musicali",
            category: "Attività e didattica",
            icon: "🎹"
        },

        TEMPO_SCUOLA: {
            label: "Tempo scuola",
            category: "Organizzazione",
            icon: "🕒"
        }
    };

    return meta[code] || {
        label: code,
        category: "Altro",
        icon: "•"
    };
}


function parameterIcon(code) {
    return parameterMeta(code).icon;
}


function parameterLabel(code, fallback) {
    return parameterMeta(code).label || fallback;
}


function parameterCategory(code) {
    return parameterMeta(code).category;
}


function extractHours(evidences) {
    for (const evidence of evidences || []) {
        const text = String(evidence.evidence || "");

        const match = text.match(
            /\b(\d+(?:[.,]\d+)?)\s*ore\s*(settimanali|settimanale|a settimana)\b/i
        );

        if (match) {
            return `${match[1].replace(",", ".")} ore/settimana`;
        }
    }

    return null;
}


function formatParameterValue(record, recordEvidences = []) {

    if (record.value_type === "BOOLEAN") {

        if (record.value === "SI") {
            const languageCodes = [
                "INGLESE",
                "FRANCESE",
                "SPAGNOLO",
                "TEDESCO"
            ];

            if (languageCodes.includes(record.parameter_code)) {
                const hours = extractHours(recordEvidences);

                return hours
                    ? `Sì · ${hours}`
                    : "Sì";
            }

            return "Sì";
        }

        if (record.status === "NOT_FOUND") {
            return "Non rilevato";
        }

        return "No";
    }

    return (
        record.value ??
        record.normalized_value ??
        "Non rilevato"
    );
}


function getRecord(records, code) {
    return records.find(
        record => record.parameter_code === code
    );
}


function getDocumentById(documentId) {
    return ptofDocuments.find(
        document => String(document.id) === String(documentId)
    );
}


function documentLink(documentId, label = "Apri documento") {
    const document = getDocumentById(documentId);

    if (!document || !document.url) {
        return "";
    }

    const title = escapeHtml(
        document.title || "Documento"
    );

    const url = escapeHtml(
        document.url
    );

    return `
        <a
            href="${url}"
            target="_blank"
            rel="noopener noreferrer"
            class="evidence-document-link"
            title="${title}"
        >
            ${label} ↗
        </a>
    `;
}


function showDetail(schoolId) {

    const school =
        schools.find(
            s => s.id === schoolId
        );

    const score =
        scores.find(
            s => s.school_id === schoolId
        );

    if (!school) {
        return;
    }

    const records =
        schoolParameters.filter(
            p => p.school_id === schoolId
        );

    const schoolEvidence =
        evidences.filter(
            e => e.school_id === schoolId
        );

    const documentIds = [
        ...new Set(
            schoolEvidence
                .map(e => e.document_id)
                .filter(v => v !== null && v !== undefined)
        )
    ];

    const sourceIds = [
        ...new Set(
            schoolEvidence
                .map(e => e.source_id)
                .filter(v => v !== null && v !== undefined)
        )
    ];

    $("schoolList").parentElement.classList.add("hidden");
    $("detail").classList.remove("hidden");

    const groups = {};

    records.forEach(record => {

        if (!groups[record.category]) {
            groups[record.category] = [];
        }

        groups[record.category].push(record);
    });

    let parametersHtml = "";

    Object.entries(groups).forEach(
        ([category, categoryRecords]) => {

            parametersHtml += `
                <section class="parameter-group">

                    <div class="parameter-group-header">

                        <div>
                            <h3 class="parameter-category-title">
                                ${escapeHtml(category)}
                            </h3>
                        </div>

                        <span class="parameter-group-count">
                            ${categoryRecords.length}
                        </span>

                    </div>
            `;

            categoryRecords.forEach(record => {

                const recordEvidences =
                    schoolEvidence
                        .filter(
                            e =>
                                e.parameter_code ===
                                record.parameter_code
                        )
                        .sort(
                            (a, b) =>
                                Number(b.confidence || 0) -
                                Number(a.confidence || 0)
                        );

                const explicitCount =
                    recordEvidences.filter(
                        e => e.evidence_type === "EXPLICIT"
                    ).length;

                const inferredCount =
                    recordEvidences.filter(
                        e => e.evidence_type === "INFERRED"
                    ).length;

                let evidenceHtml = "";

                if (recordEvidences.length > 0) {

                    evidenceHtml = `
                        <details class="evidence-details">

                            <summary>
                                <span>
                                    Vedi evidence
                                </span>

                                <strong>
                                    ${recordEvidences.length}
                                </strong>
                            </summary>

                            <div class="evidence-summary">

                                ${
                                    explicitCount
                                        ? `<span>
                                            ${explicitCount} explicit
                                           </span>`
                                        : ""
                                }

                                ${
                                    inferredCount
                                        ? `<span>
                                            ${inferredCount} inferred
                                           </span>`
                                        : ""
                                }

                            </div>

                            <div class="evidence-list">

                                ${recordEvidences.map(evidence => `

                                    <article class="evidence-card">

                                        <div class="evidence-header">

                                            <strong>
                                                Evidence #${evidence.id}
                                            </strong>

                                            <span>
                                                ${escapeHtml(
                                                    evidence.evidence_type || "UNKNOWN"
                                                )}
                                            </span>

                                        </div>

                                        <div class="evidence-text">
                                            ${escapeHtml(
                                                evidence.evidence || ""
                                            )}
                                        </div>

                                        <div class="evidence-meta">

                                            <span>
                                                Affidabilità
                                                <strong>
                                                    ${formatPercent(
                                                        evidence.confidence
                                                    )}
                                                </strong>
                                            </span>

                                            <span>
                                                Documento
                                                <strong>
                                                    ${
                                                        getDocumentById(
                                                            evidence.document_id
                                                        )?.title
                                                            ? escapeHtml(
                                                                getDocumentById(
                                                                    evidence.document_id
                                                                ).title
                                                            )
                                                            : "Non disponibile"
                                                    }
                                                </strong>
                                            </span>

                                            <span>
                                                Sorgente
                                                <strong>
                                                    ${
                                                        evidence.source_id ?? "—"
                                                    }
                                                </strong>
                                            </span>

                                        </div>

                                        ${
                                            documentLink(
                                                evidence.document_id,
                                                "Apri documento"
                                            )
                                        }

                                    </article>

                                `).join("")}

                            </div>

                        </details>
                    `;

                } else {

                    evidenceHtml = `
                        <div class="no-evidence">
                            Nessuna evidence disponibile
                        </div>
                    `;
                }

                const value =
                    formatParameterValue(
                        record,
                        recordEvidences
                    );

                const meta = parameterMeta(
                    record.parameter_code
                );

                const humanStatus = {
                    VERIFIED: "Verificato",
                    PROBABLE: "Probabile",
                    MENTIONED: "Menzionato",
                    NOT_FOUND: "Non rilevato"
                }[record.status] || record.status || "Non rilevato";

                const valueIsUnknown =
                    record.status === "NOT_FOUND";

                const displayValue =
                    valueIsUnknown
                        ? "Non rilevato"
                        : String(value);

                const statusClass =
                    String(record.status || "")
                        .toLowerCase();

                parametersHtml += `

                    <article class="parameter parameter-v4">

                        <div class="parameter-v4-main">

                            <div class="parameter-v4-icon">
                                ${meta.icon}
                            </div>

                            <div class="parameter-v4-content">

                                <div class="parameter-v4-title-row">

                                    <span class="parameter-v4-name">
                                        ${escapeHtml(meta.label)}
                                    </span>

                                    <span class="
                                        parameter-v4-status
                                        status-${statusClass}
                                    ">
                                        ${escapeHtml(humanStatus)}
                                    </span>

                                </div>

                                <div class="
                                    parameter-v4-value
                                    ${valueIsUnknown ? "is-unknown" : ""}
                                ">
                                    ${escapeHtml(displayValue)}
                                </div>

                            </div>

                            <div class="parameter-v4-confidence">

                                <span>
                                    Affidabilità
                                </span>

                                <strong>
                                    ${formatPercent(record.confidence)}
                                </strong>

                            </div>

                        </div>

                        ${evidenceHtml}

                    </article>
                `;
            });

            parametersHtml += `
                </section>
            `;
        }
    );

    const schoolPtofs =
        ptofDocuments
            .filter(
                document =>
                    document.school_id === schoolId
            );

    const currentPtof =
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



    const snapshotCodes = [
        "INGLESE",
        "FRANCESE",
        "SPAGNOLO",
        "TEDESCO",
        "MENSA",
        "PALESTRA",
        "BIBLIOTECA",
        "LABORATORIO_INFORMATICA",
        "LABORATORIO_SCIENZE",
        "LABORATORIO_MUSICALE",
        "LABORATORIO_ARTISTICO",
        "ATELIER_DIGITALE",
        "AULE_MULTIMEDIALI",
        "STEM",
        "ARTE",
        "TEATRO",
        "SPORT",
        "PNRR",
        "INDIRIZZO_MUSICALE",
        "STRUMENTI_MUSICALI"
    ];

    const snapshotGroups = [
        "Lingue",
        "Servizi",
        "Strutture",
        "Attività e didattica"
    ];

    const snapshotHtml = snapshotGroups.map(group => {

        const groupItems = snapshotCodes
            .map(code => getRecord(records, code))
            .filter(Boolean)
            .filter(record =>
                parameterCategory(record.parameter_code) === group
            );

        if (!groupItems.length) {
            return "";
        }

        const cards = groupItems.map(record => {

            const recordEvidences = schoolEvidence
                .filter(
                    e => e.parameter_code === record.parameter_code
                )
                .sort(
                    (a, b) =>
                        Number(b.confidence || 0) -
                        Number(a.confidence || 0)
                );

            const value = formatParameterValue(
                record,
                recordEvidences
            );

            const found =
                record.value === "SI" ||
                record.status === "VERIFIED" ||
                record.status === "PROBABLE" ||
                record.status === "MENTIONED";

            const stateClass = found
                ? "is-present"
                : "is-unknown";

            const stateLabel = found
                ? value
                : "Non rilevato";

            const meta = parameterMeta(
                record.parameter_code
            );

            return `
                <article class="school-feature-card ${stateClass}">

                    <div class="school-feature-icon">
                        ${meta.icon}
                    </div>

                    <div class="school-feature-body">

                        <div class="school-feature-name">
                            ${escapeHtml(meta.label)}
                        </div>

                        <div class="school-feature-state">
                            ${escapeHtml(String(stateLabel))}
                        </div>

                    </div>

                </article>
            `;
        }).join("");

        return `
            <section class="school-feature-group">

                <div class="school-feature-group-title">
                    ${escapeHtml(group)}
                </div>

                <div class="school-feature-grid">
                    ${cards}
                </div>

            </section>
        `;

    }).join("");

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


        <section class="detail-overview">

            <div
                class="detail-score-item"
                title="Valutazione complessiva della scuola sui criteri analizzati."
            >
                <span>INDICE COMPLESSIVO</span>
                <strong>
                    ${formatPercent(
                        score?.score_percent
                    )}
                </strong>
            </div>

            <div
                class="detail-score-item"
                title="Percentuale dei criteri per cui sono state trovate informazioni."
            >
                <span>COMPLETEZZA DEI DATI</span>
                <strong>
                    ${formatPercent(
                        score?.coverage_percent
                    )}
                </strong>
            </div>

            <div
                class="detail-score-item"
                title="Affidabilità complessiva dei riscontri utilizzati."
            >
                <span>AFFIDABILITÀ DELLE INFORMAZIONI</span>
                <strong>
                    ${formatPercent(
                        score?.confidence_percent
                    )}
                </strong>
            </div>

            <div
                class="detail-score-item"
                title="Numero di caratteristiche utilizzate nell'analisi."
            >
                <span>CARATTERISTICHE ANALIZZATE</span>
                <strong>
                    ${records.length}
                </strong>
            </div>

            <div
                class="detail-score-item"
                title="Numero di passaggi dei documenti utilizzati come riscontro."
            >
                <span>RISCONTRI NEI DOCUMENTI</span>
                <strong>
                    ${schoolEvidence.length}
                </strong>
            </div>

            <div
                class="detail-score-item"
                title="Numero di documenti consultati per raccogliere le informazioni."
            >
                <span>DOCUMENTI ANALIZZATI</span>
                <strong>
                    ${documentIds.length}
                </strong>

                ${
                    documentIds.length
                        ? `
                            <details class="detail-documents-list">
                                <summary>
                                    Vedi documenti
                                </summary>

                                <div>
                                    ${
                                        documentIds
                                            .map(documentId => {
                                                const document =
                                                    getDocumentById(
                                                        documentId
                                                    );

                                                if (!document) {
                                                    return "";
                                                }

                                                return `
                                                    <div>
                                                        <strong>
                                                            ${escapeHtml(
                                                                document.title ||
                                                                "Documento"
                                                            )}
                                                        </strong>

                                                        <a
                                                            href="${escapeHtml(
                                                                document.url
                                                            )}"
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                        >
                                                            Apri documento ↗
                                                        </a>
                                                    </div>
                                                `;
                                            })
                                            .join("")
                                    }
                                </div>
                            </details>
                          `
                        : ""
                }
            </div>


        </section>



        <section class="school-snapshot">

            <div class="detail-section-heading">
                <div>
                    <span class="eyebrow">
                        IN SINTESI
                    </span>

                    <h2>
                        Cosa offre la scuola
                    </h2>
                </div>
            </div>

            <div class="school-snapshot-grid">
                ${snapshotHtml}
            </div>

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


        <div class="detail-section-heading">

            <div>
                <span class="eyebrow">
                    ANALISI
                </span>

                <h2>
                    Analisi tecnica
                </h2>
            </div>

            <span>
                ${records.length} disponibili
            </span>

        </div>


        <details class="technical-details">

            <summary class="technical-details-summary">
                <div>
                    <span class="eyebrow">DATI TECNICI</span>
                    <strong>Verifica delle informazioni</strong>
                </div>

                <span class="technical-details-count">
                    ${records.length}
                </span>
            </summary>

            <div class="parameters-container">
                ${parametersHtml}
            </div>

        </details>

    `;

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


$("closeDetail").addEventListener(
    "click",
    () => {

        $("detail").classList.add(
            "hidden"
        );

        $("schoolList").parentElement.classList.remove(
            "hidden"
        );
    }
);


$("search").addEventListener(
    "input",
    renderRanking
);

$("provinceFilter").addEventListener(
    "change",
    renderRanking
);

$("scoreFilter").addEventListener(
    "change",
    renderRanking
);


function formatPercent(value) {

    if (
        value === null ||
        value === undefined ||
        Number.isNaN(Number(value))
    ) {
        return "0.0%";
    }

    return `${Number(value).toFixed(1)}%`;
}


function escapeHtml(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


loadData().catch(error => {

    console.error(error);

    $("schoolList").innerHTML = `
        <div class="school-card">
            Errore nel caricamento dei dati.
        </div>
    `;
});
