from datetime import datetime, timedelta, timezone

from gridops.config import Settings
from gridops.database.weather_forecast import (
    initialize_weather_forecast_table,
    load_weather_forecast_data,
)
from gridops.ingestion.backfill import (
    build_monthly_windows,
)
from gridops.ingestion.weather import (
    OpenMeteoPreviousRunsClient,
    PJM_WEATHER_LOCATIONS,
)
from gridops.storage.s3 import (
    build_raw_weather_forecast_key,
    upload_weather_forecast_frame,
)
from gridops.quality.weather_forecast import (
    validate_weather_forecast,
)

START_DATE = datetime(
    2024,
    1,
    1,
    tzinfo=timezone.utc,
)

END_DATE = datetime(
    2026,
    2,
    1,
    tzinfo=timezone.utc,
)


def main() -> None:
    settings = Settings()

    client = OpenMeteoPreviousRunsClient()

    initialize_weather_forecast_table(
        settings.postgres_dsn
    )

    windows = build_monthly_windows(
        START_DATE,
        END_DATE,
    )

    total_rows = 0
    total_missing = 0

    for start, end in windows:

        api_end = end - timedelta(days=1)

        print(
            f"\n{start.date()} "
            f"-> {end.date()}"
        )

        for location in (
            PJM_WEATHER_LOCATIONS.values()
        ):

            print(
                f"  Fetching {location.name}..."
            )

            frame = client.fetch_hourly(
                location=location,
                start_date=start.date(),
                end_date=api_end.date(),
            )
            
            validated, report = validate_weather_forecast(
                frame,
                expected_location_id=location.location_id,
            )

            total_missing += report.missing_value_count

            if report.has_warnings:
                for warning in report.warnings:
                    print(
                        f"    ⚠ {warning}"
                    )

            key = (
                build_raw_weather_forecast_key(
                    location_id=(
                        location.location_id
                    ),
                    start=start,
                    end=end,
                )
            )

            upload_weather_forecast_frame(
                validated,
                bucket=settings.s3_raw_bucket,
                key=key,
                profile_name=settings.aws_profile,
                region_name=settings.aws_region,
            )

            loaded = (
                load_weather_forecast_data(
                    validated,
                    dsn=settings.postgres_dsn,
                )
            )

            total_rows += loaded

            print(
                f"    Archived and loaded "
                f"{loaded:,} rows"
            )

    print()
    print(
        "✅ FORECAST WEATHER BACKFILL COMPLETE"
    )

    print(
        f"Rows processed: {total_rows:,}"
    )

    print(
        f"Missing values: {total_missing:,}"
    )


if __name__ == "__main__":
    main()