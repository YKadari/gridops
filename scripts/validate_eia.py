from pathlib import Path

import pandas as pd

from gridops.quality.eia import DataQualityError, validate_eia_demand


def main() -> None:
    raw_directory = Path("data/raw/eia")

    files = sorted(
        raw_directory.glob("pjm_demand_*.csv"),
        key=lambda path: path.stat().st_mtime,
    )

    if not files:
        raise FileNotFoundError(
            "No raw PJM files were found. Run scripts/fetch_eia.py first."
        )

    latest_file = files[-1]

    print(f"Validating: {latest_file}")

    frame = pd.read_csv(latest_file)

    try:
        validated, report = validate_eia_demand(frame)
    except DataQualityError as exc:
        print()
        print("❌ DATA QUALITY CHECK FAILED")
        print(exc)
        raise SystemExit(1) from exc

    if report.has_warnings:
        print()
        print("⚠ DATA QUALITY WARNINGS")

        for warning in report.warnings:
            print(f"- {warning}")

    print()
    print("✅ DATA QUALITY CHECK PASSED")
    print(f"Rows validated: {len(validated):,}")
    print(
        f"Time range: {validated['period'].min()} "
        f"-> {validated['period'].max()}"
    )
    print(f"Respondents: {validated['respondent'].unique().tolist()}")
    print(f"Metrics: {validated['type-name'].unique().tolist()}")
    print(f"Units: {validated['value-units'].unique().tolist()}")


if __name__ == "__main__":
    main()