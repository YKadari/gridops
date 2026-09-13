from datetime import date

from gridops.ingestion.weather import (
    OpenMeteoClient,
    PJM_WEATHER_LOCATIONS,
)


def main() -> None:
    location = PJM_WEATHER_LOCATIONS["philadelphia"]

    client = OpenMeteoClient()

    print(
        f"Fetching historical forecast weather for "
        f"{location.name}..."
    )

    frame = client.fetch_hourly(
        location=location,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 1, 31),
    )

    print()
    print("✅ WEATHER EXTRACTION COMPLETE")
    print(f"Location: {location.name}")
    print(f"Rows: {len(frame):,}")
    print(
        f"Time range: "
        f"{frame['observed_at'].min()} "
        f"-> {frame['observed_at'].max()}"
    )
    print()
    print(frame.head().to_string(index=False))


if __name__ == "__main__":
    main()