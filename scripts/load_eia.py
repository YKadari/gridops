from pathlib import Path

import pandas as pd

from gridops.config import Settings
from gridops.database.postgres import initialize_database, load_eia_data
from gridops.quality.eia import validate_eia_demand


def main() -> None:
    settings = Settings()

    raw_directory = Path("data/raw/eia")

    files = sorted(
        raw_directory.glob("pjm_demand_*.csv"),
        key=lambda path: path.stat().st_mtime,
    )

    if not files:
        raise FileNotFoundError(
            "No raw PJM data found. Run scripts/fetch_eia.py first."
        )

    latest_file = files[-1]

    print(f"Reading: {latest_file}")

    frame = pd.read_csv(latest_file)

    print("Validating data...")
    validated = validate_eia_demand(frame)

    print(f"Validated {len(validated):,} rows.")

    print("Initializing PostgreSQL...")
    initialize_database(settings.postgres_dsn)

    print("Loading records...")
    loaded = load_eia_data(
        validated,
        dsn=settings.postgres_dsn,
    )

    print()
    print("✅ DATABASE LOAD COMPLETE")
    print(f"Rows processed: {loaded:,}")


if __name__ == "__main__":
    main()