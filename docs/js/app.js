const DATA_PATH = "data";

let schools = [];
let scores = [];
let parameters = [];
let schoolParameters = [];
let evidences = [];
let ptofDocuments = [];

const $ = (id) => document.getElementById(id);


async function loadData() {

    const loadJson = async (file) => {

        const response =
            await fetch(
                `${DATA_PATH}/${file}`,
                {
                    cache: "no-store"
                }
            );

        if (!response.ok) {
            throw new Error(
                `${file}: HTTP ${response.status}`
            );
        }

        return response.json();
    };


    const results =
        await Promise.allSettled([

            loadJson("schools.json"),
            loadJson("school_scores.json"),
            loadJson("parameters.json"),
            loadJson("school_parameters.json"),
            loadJson("evidence.json"),
            loadJson("ptof_documents.json"),
            loadJson("statistics.json")

        ]);


    const [
        schoolsResult,
        scoresResult,
        parametersResult,
        schoolParametersResult,
        evidenceResult,
        ptofDocumentsResult,
        statisticsResult
    ] = results;


    schools =
        schoolsResult.status === "fulfilled"
            ? schoolsResult.value
            : [];

    scores =
        scoresResult.status === "fulfilled"
            ? scoresResult.value
            : [];

    parameters =
        parametersResult.status === "fulfilled"
            ? parametersResult.value
            : [];

    schoolParameters =
        schoolParametersResult.status === "fulfilled"
            ? schoolParametersResult.value
            : [];

    evidences =
        evidenceResult.status === "fulfilled"
            ? evidenceResult.value
            : [];

    ptofDocuments =
        ptofDocumentsResult.status === "fulfilled"
            ? ptofDocumentsResult.value
            : [];


    /*
     * statistics.json è un riepilogo.
     * Se non è disponibile, ricaviamo comunque
     * i KPI direttamente dai dataset caricati.
     */

    let statistics;

    if (statisticsResult.status === "fulfilled") {

        statistics =
            statisticsResult.value;

    } else {

        statistics = {

            schools: schools.length,

            documents: ptofDocuments.length,

            evidence: evidences.length,

            active_parameters:
                parameters.filter(
                    parameter =>
                        Number(parameter.active) === 1
                ).length ||
                parameters.length

        };

        console.warn(
            "statistics.json non disponibile:",
            statisticsResult.reason
        );

    }


    /*
     * Verifica minima dei dataset fondamentali.
     */

    if (
        !schools.length ||
        !scores.length ||
        !schoolParameters.length
    ) {

        throw new Error(
            "Dataset principali non disponibili."
        );

    }


    $( "kpiSchools" ).textContent =
        statistics.schools ??
        schools.length;

    $( "kpiDocuments" ).textContent =
        statistics.documents ??
        ptofDocuments.length;

    $( "kpiEvidence" ).textContent =
        Number(
            statistics.evidence ??
            evidences.length
        ).toLocaleString("it-IT");

    $( "kpiParameters" ).textContent =
        statistics.active_parameters ??
        parameters.length;

    $( "schoolCount" ).textContent =
        statistics.schools ??
        schools.length;


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
                title="Numero di documenti utilizzati per costruire l'analisi della scuola."
            >
                <span>DOCUMENTI ANALIZZATI</span>
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
                        DOCUMENTO DI RIFERIMENTO
                    </span>

                    <h2>
                        PTOF
                    </h2>

                    <p>
                        Il documento principale per conoscere
                        l'offerta formativa e il progetto della scuola.
                    </p>
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
                                    PTOF di riferimento
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
                                Apri PTOF ↗
                            </a>

                        </div>
                      `
                    : `
                        <div class="detail-ptof-empty">
                            Nessun PTOF di riferimento disponibile.
                        </div>
                      `
            }


            ${
                (() => {

                    const allOtherDocuments =
                        ptofDocuments
                            .filter(
                                document =>
                                    document.school_id === schoolId &&
                                    String(document.id) !==
                                        String(currentPtof?.id)
                            );


                    const classifyDocument = (document) => {

                        const title =
                            String(
                                document.title || ""
                            ).toUpperCase();


                        /*
                         * PTOF successivi / aggiornamenti
                         */

                        if (
                            title.includes("PTOF") &&
                            (
                                title.includes("AGGIORNAMENTO") ||
                                title.includes("PREDISPOSIZIONE")
                            )
                        ) {
                            return title.includes("PREDISPOSIZIONE") ? "Predisposizione PTOF" : "Aggiornamento PTOF";
                        }


                        /*
                         * PTOF precedenti
                         */

                        if (
                            title.includes("PTOF")
                        ) {
                            return "PTOF precedente";
                        }


                        /*
                         * Atti di indirizzo:
                         * servono a capire il contesto
                         * della progettazione della scuola.
                         */

                        if (
                            title.includes("ATTO D'INDIRIZZO") ||
                            title.includes("ATTO DI INDIRIZZO") ||
                            title.includes("INDIRIZZO DEL DIRIGENTE")
                        ) {
                            return "Documento di contesto";
                        }


                        /*
                         * Tutto il resto è materiale
                         * di supporto all'analisi.
                         */

                        return "Documento di supporto";
                    };


                    const otherDocuments =
                        allOtherDocuments
                            .map(document => ({
                                document,
                                role: classifyDocument(document)
                            }))
                            .sort((a, b) => {

                                const rank = {
                                    "Aggiornamento PTOF": 0,
                                    "Predisposizione PTOF": 1,
                                    "PTOF precedente": 2,
                                    "Documento di supporto": 3,
                                    "Documento di contesto": 4
                                };

                                return (
                                    (rank[a.role] ?? 9) -
                                    (rank[b.role] ?? 9)
                                );

                            });


                    if (!otherDocuments.length) {
                        return "";
                    }


                    return `

                        <div class="detail-source-list">

                            <div class="detail-source-list-heading">

                                <strong>
                                    Altre fonti utilizzate nell'analisi
                                </strong>

                                <span>
                                    ${otherDocuments.length}
                                </span>

                            </div>


                            <div class="detail-source-list-items">

                                ${
                                    otherDocuments
                                        .map(
                                            ({
                                                document,
                                                role
                                            }) => `

                                                <div
                                                    class="detail-source-item"
                                                >

                                                    <div>

                                                        <strong>
                                                            ${escapeHtml(
                                                                document.title ||
                                                                "Documento"
                                                            )}
                                                        </strong>

                                                        <span>
                                                            ${escapeHtml(
                                                                role
                                                            )}
                                                        </span>

                                                    </div>


                                                    ${
                                                        document.url
                                                            ? `
                                                                <a
                                                                    href="${escapeHtml(
                                                                        document.url
                                                                    )}"
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                >
                                                                    Apri ↗
                                                                </a>
                                                              `
                                                            : ""
                                                    }

                                                </div>

                                            `
                                        )
                                        .join("")
                                }

                            </div>

                        </div>

                    `;
                })()
            }

        </section>


        <div class="detail-section-heading">

            <div>
                <span class="eyebrow">
                    INFORMAZIONI
                </span>

                <h2>
                    Informazioni sulla scuola
                </h2>
            </div>

            <span>
                ${records.length} disponibili
            </span>

        </div>






        <!-- =====================================================
             RISCONTRI DOCUMENTALI
             ===================================================== -->

        <section class="school-data-section evidence-section">

            <div class="school-data-section-header">

                <div>
                    <span class="eyebrow">
                        PROVENIENZA DEI DATI
                    </span>

                    <h2>
                        Riscontri documentali
                    </h2>

                    <p>
                        I passaggi dei documenti che supportano
                        le informazioni riportate nella scheda.
                    </p>
                </div>

                <strong class="school-data-count">
                    ${schoolEvidence.length}
                </strong>

            </div>

            <div class="school-data-table-wrap">

                <table class="school-data-table evidence-table">

                    <thead>
                        <tr>
                            <th>Parametro</th>
                            <th>Riscontro</th>
                            <th>Tipo</th>
                            <th>Affidabilità</th>
                            <th>Documento</th>
                        </tr>
                    </thead>

                    <tbody>

                        ${
                            schoolEvidence
                                .slice()
                                .sort(
                                    (a, b) =>
                                        Number(b.confidence || 0) -
                                        Number(a.confidence || 0)
                                )
                                .map(evidence => {

                                    const parameter =
                                        records.find(
                                            record =>
                                                record.parameter_code ===
                                                evidence.parameter_code
                                        );

                                    const parameterName =
                                        parameter?.parameter_name ||
                                        evidence.parameter_code ||
                                        "Parametro";

                                    const document =
                                        getDocumentById(
                                            evidence.document_id
                                        );

                                    const documentTitle =
                                        document?.title ||
                                        "Documento non disponibile";

                                    const documentUrl =
                                        document?.url ||
                                        "";

                                    return `
                                        <tr>

                                            <td data-label="Parametro">
                                                <strong>
                                                    ${escapeHtml(
                                                        parameterName
                                                    )}
                                                </strong>
                                            </td>

                                            <td data-label="Riscontro">

                                                <details
                                                    class="evidence-row-details"
                                                >

                                                    <summary>
                                                        Mostra riscontro
                                                    </summary>

                                                    <div>
                                                        ${escapeHtml(
                                                            evidence.evidence ||
                                                            ""
                                                        )}
                                                    </div>

                                                </details>

                                            </td>

                                            <td data-label="Tipo">
                                                ${escapeHtml(
                                                    ({
                                                        EXPLICIT: "Riscontro diretto",
                                                        INFERRED: "Riscontro indiretto",
                                                        MENTION: "Menzione"
                                                    }[evidence.evidence_type] ||
                                                    "Non specificato")
                                                )}
                                            </td>

                                            <td data-label="Affidabilità">
                                                <strong>
                                                    ${formatPercent(
                                                        evidence.confidence
                                                    )}
                                                </strong>
                                            </td>

                                            <td data-label="Documento">

                                                ${
                                                    documentUrl
                                                        ? `
                                                            <a
                                                                class="school-document-link"
                                                                href="${escapeHtml(documentUrl)}"
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                            >
                                                                ${escapeHtml(
                                                                    documentTitle
                                                                )} ↗
                                                            </a>
                                                          `
                                                        : escapeHtml(
                                                            documentTitle
                                                        )
                                                }

                                            </td>

                                        </tr>
                                    `;
                                })
                                .join("")
                        }

                    </tbody>

                </table>

            </div>

        </section>


        <!-- =====================================================
             DOCUMENTI ANALIZZATI
             ===================================================== -->

        <section class="school-data-section documents-section">

            <div class="school-data-section-header">

                <div>
                    <span class="eyebrow">
                        FONTI DELL'ANALISI
                    </span>

                    <h2>
                        Documenti analizzati
                    </h2>

                    <p>
                        I documenti utilizzati per raccogliere e verificare
                        le informazioni presenti nella scheda.
                    </p>
                </div>

                <strong class="school-data-count">
                    ${documentIds.length}
                </strong>

            </div>

            <div class="school-data-table-wrap">

                <table class="school-data-table">

                    <thead>
                        <tr>
                            <th>Documento</th>
                            <th>Tipologia</th>
                            <th>Utilizzo</th>
                            <th>Apri</th>
                        </tr>
                    </thead>

                    <tbody>

                        ${
                            documentIds
                                .map(documentId => {

                                    const document =
                                        getDocumentById(documentId);

                                    if (!document) {
                                        return "";
                                    }

                                    const title =
                                        document.title ||
                                        "Documento";

                                    const type =
                                        document.document_type ||
                                        document.type ||
                                        "Documento";

                                    const url =
                                        document.url || "";

                                    return `
                                        <tr>

                                            <td data-label="Documento">
                                                <strong>
                                                    ${escapeHtml(title)}
                                                </strong>
                                            </td>

                                            <td data-label="Tipologia">
                                                ${escapeHtml(type)}
                                            </td>

                                            <td data-label="Utilizzo">
                                                Documento utilizzato
                                                nell'analisi
                                            </td>

                                            <td data-label="Apri">

                                                ${
                                                    url
                                                        ? `
                                                            <a
                                                                class="school-document-link"
                                                                href="${escapeHtml(url)}"
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                            >
                                                                Apri ↗
                                                            </a>
                                                          `
                                                        : "Non disponibile"
                                                }

                                            </td>

                                        </tr>
                                    `;
                                })
                                .join("")
                        }

                    </tbody>

                </table>

            </div>

        </section>


        <section class="school-information-section">

            <div class="school-information-header">

                <div>
                    <span class="eyebrow">
                        INFORMAZIONI
                    </span>

                    <h2>
                        Informazioni sulla scuola
                    </h2>

                    <p>
                        Le caratteristiche della scuola rilevate
                        nei documenti analizzati.
                    </p>
                </div>

                <span class="school-information-count">
                    ${records.length}
                </span>

            </div>

            <div class="parameters-container">
                ${parametersHtml}
            </div>

        </section>

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
