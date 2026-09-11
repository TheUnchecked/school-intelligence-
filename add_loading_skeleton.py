"""
Aggiunge uno "skeleton" di caricamento: blocchi grigi che pulsano al
posto della schermata vuota mentre i dati arrivano.

Non serve nessuna modifica JavaScript: lo skeleton è semplicemente il
contenuto HTML iniziale di #schoolList, e renderRanking() già svuota
il contenitore (container.innerHTML = "") prima di popolarlo con le
card reali — quindi lo skeleton sparisce da solo appena i dati sono
pronti.

Rispetta prefers-reduced-motion (niente animazione per chi ha
disattivato le animazioni nel sistema).

Uso:
    python add_loading_skeleton.py

Da eseguire nella cartella radice del repository. È idempotente.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SKELETON_CARD = '''
            <div class="ranking-card skeleton-card" aria-hidden="true">
                <div class="ranking-card-header">
                    <div class="ranking-card-identity">
                        <div class="skeleton-block skeleton-rank"></div>
                        <div class="skeleton-block skeleton-title"></div>
                        <div class="skeleton-block skeleton-meta"></div>
                    </div>
                    <div class="ranking-score">
                        <div class="skeleton-block skeleton-score"></div>
                    </div>
                </div>
                <div class="skeleton-block skeleton-progress"></div>
            </div>'''

SKELETON_CSS = '''

/* ============================================================
   SKELETON DI CARICAMENTO
   ============================================================ */

.skeleton-block {
    border-radius: 6px;
    background: var(--line);
    animation: skeleton-pulse 1.4s ease-in-out infinite;
}

.skeleton-rank {
    width: 28px;
    height: 14px;
    margin-bottom: 10px;
}

.skeleton-title {
    width: 70%;
    height: 22px;
    margin-bottom: 10px;
}

.skeleton-meta {
    width: 50%;
    height: 13px;
}

.skeleton-score {
    width: 64px;
    height: 32px;
    margin-left: auto;
}

.skeleton-progress {
    width: 100%;
    height: 6px;
    margin-top: 20px;
}

.skeleton-card {
    cursor: default;
    pointer-events: none;
}

@keyframes skeleton-pulse {
    0%, 100% {
        opacity: .55;
    }
    50% {
        opacity: 1;
    }
}

@media (prefers-reduced-motion: reduce) {
    .skeleton-block {
        animation: none;
        opacity: .7;
    }
}
'''


def log(msg):
    print(f"- {msg}")


def patch_html():
    path = BASE_DIR / "docs" / "index.html"
    text = path.read_text(encoding="utf-8")

    if "skeleton-card" in text:
        log("index.html: skeleton già presente, salto.")
        return

    old = '        <div id="schoolList" class="school-list"></div>'

    if old not in text:
        log("ATTENZIONE: contenitore #schoolList non trovato come "
            "atteso, controllo manuale necessario in index.html")
        return

    new = (
        '        <div id="schoolList" class="school-list">'
        + SKELETON_CARD * 3 +
        '\n        </div>'
    )

    text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    log("index.html: skeleton di caricamento aggiunto (3 card "
        "segnaposto).")


def patch_css():
    path = BASE_DIR / "docs" / "css" / "app.css"
    text = path.read_text(encoding="utf-8")

    if "SKELETON DI CARICAMENTO" in text:
        log("app.css: stile skeleton già presente, salto.")
        return

    with path.open("a", encoding="utf-8") as f:
        f.write(SKELETON_CSS)

    log("app.css: animazione di pulsazione aggiunta (rispetta "
        "prefers-reduced-motion).")


def main():
    print("Skeleton di caricamento")
    print("=" * 60)
    patch_html()
    patch_css()
    print("=" * 60)
    print("Fatto. Controlla il risultato in locale prima di committare.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
