from datetime import datetime, timezone

from gridops.config import Settings
from gridops.ingestion.backfill import (
    build_monthly_windows,
    to_eia_inclusive_end,
)
from gridops.ingestion.eia import EIAClient
from gridops.quality.eia import validate_eia_demand
from gridops.storage.s3 import (
    build_raw_eia_key,
    upload_eia_frame,
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

    windows = build_monthly_windows(
        START_DATE,
        END_DATE,
    )

    print(
        f"Archiving historical PJM demand to S3 from "
        f"{START_DATE.date()} to {END_DATE.date()}"
    )

    print(f"Windows to process: {len(windows)}")
    print()

    total_rows = 0
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

        # Archive the exact upstream response before downstream processing.
        key = build_raw_eia_key(
            respondent="PJM",
            start=start,
            end=end,
        )

        upload_eia_frame(
            frame,
            bucket=settings.s3_raw_bucket,
            key=key,
            profile_name=settings.aws_profile,
            region_name=settings.aws_region,
        )

        print(
            f"  Archived {len(frame):,} raw rows to "
            f"s3://{settings.s3_raw_bucket}/{key}"
        )

        # Inspect source quality after preserving the raw extract.
        _, report = validate_eia_demand(
            frame,
            expected_respondent="PJM",
        )

        if report.has_warnings:
            print("  ⚠ Data quality warnings:")

            for warning in report.warnings:
                print(f"    - {warning}")

        total_rows += len(frame)
        total_missing_values += report.missing_value_count
        total_gap_warnings += report.non_hourly_gap_count

    print()
    print("✅ HISTORICAL S3 BACKFILL COMPLETE")
    print(f"Rows archived: {total_rows:,}")
    print(
        f"Missing demand values detected: "
        f"{total_missing_values:,}"
    )
    print(
        f"Non-hourly gaps detected: "
        f"{total_gap_warnings:,}"
    )


if __name__ == "__main__":
    main()