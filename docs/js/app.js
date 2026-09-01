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

    results.forEach((school, index) => {

        const score =
            school.score;

        const card =
            document.createElement("article");

        card.className =
            "school-card";

        card.innerHTML = `
            <div class="school-card-main">

                <div>

                    <div class="school-rank">
                        #${index + 1}
                    </div>

                    <div class="school-name">
                        ${escapeHtml(
                            school.denominazione
                        )}
                    </div>

                    <div class="school-meta">
                        ${escapeHtml(
                            school.comune
                        )}
                        ·
                        ${escapeHtml(
                            school.provincia
                        )}
                        ·
                        ${escapeHtml(
                            school.codice_scuola
                        )}
                    </div>

                </div>

                <div class="score">

                    <div class="score-value">
                        ${formatPercent(
                            score?.score_percent
                        )}
                    </div>

                    <div class="score-label">
                        SCORE
                    </div>

                </div>

            </div>

            <div class="school-stats">

                <span>
                    Coverage
                    <strong>
                        ${formatPercent(
                            score?.coverage_percent
                        )}
                    </strong>
                </span>

                <span>
                    Confidence
                    <strong>
                        ${formatPercent(
                            score?.confidence_percent
                        )}
                    </strong>
                </span>

                <span>
                    Verified
                    <strong>
                        ${score?.verified_count ?? 0}
                    </strong>
                </span>

                <span>
                    Evidence
                    <strong>
                        ${score?.evidence_count ?? 0}
                    </strong>
                </span>

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
                                                Confidence
                                                <strong>
                                                    ${formatPercent(
                                                        evidence.confidence
                                                    )}
                                                </strong>
                                            </span>

                                            <span>
                                                Document
                                                <strong>
                                                    ${evidence.document_id ?? "—"}
                                                </strong>
                                            </span>

                                            <span>
                                                Source
                                                <strong>
                                                    ${evidence.source_id ?? "—"}
                                                </strong>
                                            </span>

                                        </div>

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

                parametersHtml += `

                    <article class="parameter">

                        <div class="parameter-main">

                            <div class="parameter-title">

                                <span class="parameter-name">
                                    ${escapeHtml(
                                        record.parameter_name
                                    )}
                                </span>

                                <span class="
                                    parameter-status
                                    status-${String(
                                        record.status || ""
                                    ).toLowerCase()}
                                ">
                                    ${escapeHtml(
                                        record.status || ""
                                    )}
                                </span>

                            </div>

                            <div class="parameter-value">
                                ${escapeHtml(
                                    String(value)
                                )}
                            </div>

                            <div class="parameter-metrics">

                                <span>
                                    Confidence
                                    <strong>
                                        ${formatPercent(
                                            record.confidence
                                        )}
                                    </strong>
                                </span>

                                <span>
                                    Evidence
                                    <strong>
                                        ${recordEvidences.length}
                                    </strong>
                                </span>

                                <span>
                                    Type
                                    <strong>
                                        ${escapeHtml(
                                            record.value_type || "—"
                                        )}
                                    </strong>
                                </span>

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

            <div class="detail-score-item">
                <span>SCORE</span>
                <strong>
                    ${formatPercent(
                        score?.score_percent
                    )}
                </strong>
            </div>

            <div class="detail-score-item">
                <span>COVERAGE</span>
                <strong>
                    ${formatPercent(
                        score?.coverage_percent
                    )}
                </strong>
            </div>

            <div class="detail-score-item">
                <span>CONFIDENCE</span>
                <strong>
                    ${formatPercent(
                        score?.confidence_percent
                    )}
                </strong>
            </div>

            <div class="detail-score-item">
                <span>PARAMETRI</span>
                <strong>
                    ${records.length}
                </strong>
            </div>

            <div class="detail-score-item">
                <span>EVIDENCE</span>
                <strong>
                    ${schoolEvidence.length}
                </strong>
            </div>

            <div class="detail-score-item">
                <span>DOCUMENTI</span>
                <strong>
                    ${documentIds.length}
                </strong>
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
                    Parametri
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
                    <strong>Parametri ed evidence</strong>
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
