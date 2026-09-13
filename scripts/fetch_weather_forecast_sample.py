from datetime import date

from gridops.ingestion.weather import (
    FORECAST_WEATHER_VARIABLES,
    OpenMeteoPreviousRunsClient,
    PJM_WEATHER_LOCATIONS,
)


def main() -> None:
    location = PJM_WEATHER_LOCATIONS[
        "philadelphia"
    ]

    client = OpenMeteoPreviousRunsClient()

    print(
        f"Fetching fixed-lead weather forecasts "
        f"for {location.name}..."
    )

    frame = client.fetch_hourly(
        location=location,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 31),
    )

    print()
    print("✅ FORECAST WEATHER EXTRACTION COMPLETE")
    print(f"Location: {location.name}")
    print(f"Rows: {len(frame):,}")

    print(
        f"Time range: "
        f"{frame['valid_at'].min()} "
        f"-> {frame['valid_at'].max()}"
    )

    print()
    print("Missing values:")

    for horizon in (24, 48):
        for variable in FORECAST_WEATHER_VARIABLES:
            column = (
                f"{variable}_forecast_{horizon}h"
            )

            print(
                f"{column}: "
                f"{frame[column].isna().sum()}"
            )

    print()
    print(frame.head().to_string(index=False))


if __name__ == "__main__":
    main()