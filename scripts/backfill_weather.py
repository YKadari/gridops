from datetime import datetime, timedelta, timezone

from gridops.config import Settings
from gridops.database.weather import (
    initialize_weather_table,
    load_weather_data,
)
from gridops.ingestion.backfill import build_monthly_windows
from gridops.ingestion.weather import (
    OpenMeteoClient,
    PJM_WEATHER_LOCATIONS,
)
from gridops.quality.weather import validate_weather_data
from gridops.storage.s3 import (
    build_raw_weather_key,
    upload_weather_frame,
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


def main() -> None:
    settings = Settings()
    client = OpenMeteoClient()

    initialize_weather_table(
        settings.postgres_dsn
    )

    windows = build_monthly_windows(
        START_DATE,
        END_DATE,
    )

    total_rows = 0
    total_missing_values = 0
    total_gap_warnings = 0

    print(
        f"Backfilling weather from "
        f"{START_DATE.date()} to {END_DATE.date()}"
    )

    print(
        f"Monthly windows: {len(windows)}"
    )

    print(
        f"Locations: {len(PJM_WEATHER_LOCATIONS)}"
    )

    print(
        f"Expected API requests: "
        f"{len(windows) * len(PJM_WEATHER_LOCATIONS)}"
    )

    print()

    for window_number, (start, end) in enumerate(
        windows,
        start=1,
    ):
        print(
            f"[Month {window_number}/{len(windows)}] "
            f"{start.date()} -> {end.date()}"
        )

        # Open-Meteo uses inclusive calendar dates.
        api_end = end - timedelta(days=1)

        for location in PJM_WEATHER_LOCATIONS.values():

            print(
                f"  Fetching {location.name}..."
            )

            frame = client.fetch_hourly(
                location=location,
                start_date=start.date(),
                end_date=api_end.date(),
            )

            # Preserve the original API response in S3.
            key = build_raw_weather_key(
                location_id=location.location_id,
                start=start,
                end=end,
            )

            upload_weather_frame(
                frame,
                bucket=settings.s3_raw_bucket,
                key=key,
                profile_name=settings.aws_profile,
                region_name=settings.aws_region,
            )

            validated, report = validate_weather_data(
                frame,
                expected_location_id=location.location_id,
            )

            loaded = load_weather_data(
                validated,
                dsn=settings.postgres_dsn,
            )

            total_rows += loaded
            total_missing_values += report.missing_value_count
            total_gap_warnings += report.non_hourly_gap_count

            if report.has_warnings:
                print("    ⚠ Data quality warnings:")

                for warning in report.warnings:
                    print(
                        f"      - {warning}"
                    )

            print(
                f"    Archived and loaded "
                f"{loaded:,} rows."
            )

    print()
    print(
        "✅ HISTORICAL WEATHER BACKFILL COMPLETE"
    )

    print(
        f"Rows processed: {total_rows:,}"
    )

    print(
        f"Missing weather values detected: "
        f"{total_missing_values:,}"
    )

    print(
        f"Non-hourly gaps detected: "
        f"{total_gap_warnings:,}"
    )


if __name__ == "__main__":
    main()