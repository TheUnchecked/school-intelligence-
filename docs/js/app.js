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
                            <span class="eyebrow">
                                ${escapeHtml(category)}
                            </span>

                            <h3>
                                Parametri
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
                    record.value ??
                    record.normalized_value ??
                    "—";

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



        <section class="detail-ptof">

            <div class="detail-ptof-header">

                <div>

                    <span class="eyebrow">
                        DOCUMENTO PRINCIPALE
                    </span>

                    <h2>
                        PTOF
                    </h2>

                </div>

            </div>

            ${(() => {

                const schoolPtofs =
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

                if (!currentPtof) {

                    return `
                        <div class="detail-ptof-empty">
                            Nessun PTOF disponibile.
                        </div>
                    `;

                }

                return `

                    <div class="detail-ptof-card">

                        <div>

                            <strong>
                                ${escapeHtml(
                                    currentPtof.title || "PTOF"
                                )}
                            </strong>

                            <span>
                                ${escapeHtml(
                                    currentPtof.school_year || ""
                                )}
                            </span>

                        </div>

                        <a
                            class="detail-ptof-button"
                            href="${escapeHtml(currentPtof.url)}"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Apri / scarica PTOF
                            ↗
                        </a>

                    </div>

                `;

            })()}

        </section>

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


        <section class="detail-provenance">

            <div class="provenance-item">
                <span>Evidence</span>
                <strong>
                    ${schoolEvidence.length}
                </strong>
            </div>

            <div class="provenance-item">
                <span>Documenti</span>
                <strong>
                    ${documentIds.length}
                </strong>
            </div>

            <div class="provenance-item">
                <span>Sources</span>
                <strong>
                    ${sourceIds.length}
                </strong>
            </div>

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


        <div class="parameters-container">
            ${parametersHtml}
        </div>

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
