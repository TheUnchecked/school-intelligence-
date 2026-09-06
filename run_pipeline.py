#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent

STEPS = [
    ("School discovery", "src.collectors.school_discovery"),
    ("PTOF discovery", "src.collectors.ptof_discovery"),
    ("PTOF harvesting", "src.collectors.ptof_harvester"),
    ("Document classification", "src.db.classify_documents"),
    ("PDF to text conversion", "src.collectors.pdf_to_text"),
    ("Evidence extraction", "src.db.evidence_extractor"),
    ("Evidence normalization", "src.db.normalize_evidence"),
    ("Feature aggregation", "src.db.feature_aggregator"),
    ("School profile pipeline", "run_school_profile_pipeline"),
    ("PTOF version comparison", "src.db.compare_ptof_versions"),
    ("Public export", "src.export.export_public_data"),
]


def main():
    print("=" * 70)
    print("SCHOOL INTELLIGENCE — FULL PIPELINE")
    print("=" * 70)

    failed = False

    for name, module in STEPS:
        print(f"\n>>> {name}")
        print("-" * 70)

        result = subprocess.run(
            [sys.executable, "-m", module],
            cwd=ROOT,
        )

        if result.returncode != 0:
            print()
            print("=" * 70)
            print(f"PIPELINE FAILED: {name}")
            print(f"Module       : {module}")
            print(f"Exit code    : {result.returncode}")
            print("=" * 70)
            failed = True
            break

    if failed:
        return 1

    print()
    print("=" * 70)
    print("PIPELINE COMPLETATA CON SUCCESSO")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
