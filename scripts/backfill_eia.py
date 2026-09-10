from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from tracemalloc import start

from gridops.config import Settings
from gridops.database.postgres import initialize_database, load_eia_data
from gridops.ingestion.backfill import build_monthly_windows
from gridops.ingestion.eia import EIAClient
from gridops.quality.eia import validate_eia_demand
from gridops.ingestion.backfill import (
    build_monthly_windows,
    to_eia_inclusive_end,
)

START_DATE = datetime(
    2023,
    1,
    1,
    tzinfo=timezone.utc,
)

END_DATE = datetime(
    2026,
    1,
    1,
    tzinfo=timezone.utc,
)

def eia_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H")


def main() -> None:
    settings = Settings()

    client = EIAClient(
        api_key=settings.eia_api_key,
        base_url=settings.eia_base_url,
    )

    initialize_database(settings.postgres_dsn)

    windows = build_monthly_windows(
        START_DATE,
        END_DATE,
    )

    print(
        f"Backfilling PJM demand from "
        f"{START_DATE.date()} to {END_DATE.date()}"
    )
    print(f"Windows to process: {len(windows)}")
    print()

    total_loaded = 0
    total_missing_values = 0
    total_gap_warnings = 0

    for number, (start, end) in enumerate(
        windows,
        start=1,
    ):
        print(
            f"[{number}/{len(windows)}] "
            f"{start.date()} -> {end.date()}"
        )

        api_end = to_eia_inclusive_end(end)

        frame = client.fetch_region_data(
            respondent="PJM",
            data_type="D",
            start=eia_timestamp(start),
            end=eia_timestamp(api_end),
        )

        if frame.empty:
            print("  No data returned.")
            continue

        validated, report = validate_eia_demand(
            frame,
            expected_respondent="PJM",
        )

        if report.has_warnings:
            print("  ⚠ Data quality warnings:")

            for warning in report.warnings:
                print(f"    - {warning}")

        loaded = load_eia_data(
            validated,
            dsn=settings.postgres_dsn,
        )

        total_loaded += loaded
        total_missing_values += report.missing_value_count
        total_gap_warnings += report.non_hourly_gap_count

        print(
            f"  Validated and loaded {loaded:,} rows."
        )
    print()
    print("✅ HISTORICAL BACKFILL COMPLETE")
    print(f"Rows processed: {total_loaded:,}")
    print(f"Missing demand values detected: {total_missing_values:,}")
    print(f"Non-hourly gaps detected: {total_gap_warnings:,}")


if __name__ == "__main__":
    main()