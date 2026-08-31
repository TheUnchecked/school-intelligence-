const DATA_PATH = "data";

let schools = [];
let scores = [];
let parameters = [];
let schoolParameters = [];
let evidences = [];

const $ = (id) => document.getElementById(id);


async function loadData() {

    const [
        schoolsResponse,
        scoresResponse,
        parametersResponse,
        schoolParametersResponse,
        evidenceResponse,
        statisticsResponse
    ] = await Promise.all([
        fetch(`${DATA_PATH}/schools.json`),
        fetch(`${DATA_PATH}/school_scores.json`),
        fetch(`${DATA_PATH}/parameters.json`),
        fetch(`${DATA_PATH}/school_parameters.json`),
        fetch(`${DATA_PATH}/evidence.json`),
        fetch(`${DATA_PATH}/statistics.json`)
    ]);

    schools = await schoolsResponse.json();
    scores = await scoresResponse.json();
    parameters = await parametersResponse.json();
    schoolParameters = await schoolParametersResponse.json();
    evidences = await evidenceResponse.json();

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

    const records =
        schoolParameters
            .filter(
                p => p.school_id === schoolId
            );

    $("schoolList").parentElement.classList.add(
        "hidden"
    );

    $("detail").classList.remove(
        "hidden"
    );

    const groups = {};

    records.forEach(record => {

        if (!groups[record.category]) {
            groups[record.category] = [];
        }

        groups[record.category].push(record);
    });

    let parametersHtml = "";

    Object.entries(groups).forEach(
        ([category, records]) => {

            parametersHtml += `
                <section class="parameter-group">

                    <h3>
                        ${escapeHtml(category)}
                    </h3>
            `;

            records.forEach(record => {

                const parameterEvidence =
                    evidences.filter(
                        evidence =>
                            evidence.school_id === schoolId &&
                            evidence.parameter_code === record.parameter_code
                    );

                let evidenceHtml = "";

                if (parameterEvidence.length > 0) {

                    evidenceHtml = `
                        <div class="parameter-evidence">

                            ${parameterEvidence
                                .map(evidence => `
                                    <div class="evidence-item">

                                        <div class="evidence-text">
                                            ${escapeHtml(
                                                evidence.evidence
                                            )}
                                        </div>

                                        <div class="evidence-meta">

                                            <span>
                                                ${escapeHtml(
                                                    evidence.evidence_type || ""
                                                )}
                                            </span>

                                            <span>
                                                Confidence
                                                ${formatPercent(
                                                    evidence.confidence
                                                )}
                                            </span>

                                            <span>
                                                Evidence #${evidence.id}
                                            </span>

                                        </div>

                                    </div>
                                `)
                                .join("")}

                        </div>
                    `;

                } else {

                    evidenceHtml = `
                        <div class="parameter-evidence empty">
                            Nessuna evidence disponibile.
                        </div>
                    `;
                }

                parametersHtml += `
                    <div class="parameter">

                        <div class="parameter-main">

                            <span>
                                ${escapeHtml(
                                    record.parameter_name
                                )}
                            </span>

                            <span class="
                                parameter-status
                                status-${record.status.toLowerCase()}
                            ">
                                ${record.status}
                            </span>

                            <span class="
                                parameter-confidence
                            ">
                                ${formatPercent(
                                    record.confidence
                                )}
                            </span>

                        </div>

                        ${evidenceHtml}

                    </div>
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
                ·
                ${escapeHtml(
                    school.indirizzo || ""
                )}
            </div>

        </div>


        <div class="detail-score">

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

        </div>

        ${parametersHtml}
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
