from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


REQUIRED_COLUMNS = {
    "observed_at",
    "location_id",
    "location_name",
    "latitude",
    "longitude",
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation",
    "wind_speed_10m",
}

WEATHER_COLUMNS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation",
    "wind_speed_10m",
]


class WeatherDataQualityError(ValueError):
    """Raised when weather data violates a fatal GridOps rule."""


@dataclass
class WeatherDataQualityReport:
    warnings: list[str] = field(default_factory=list)
    missing_value_count: int = 0
    non_hourly_gap_count: int = 0

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)


def validate_weather_data(
    frame: pd.DataFrame,
    *,
    expected_location_id: str,
) -> tuple[pd.DataFrame, WeatherDataQualityReport]:

    if frame.empty:
        raise WeatherDataQualityError(
            "Weather dataset is empty."
        )

    missing_columns = REQUIRED_COLUMNS - set(frame.columns)

    if missing_columns:
        raise WeatherDataQualityError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    validated = frame.copy()
    report = WeatherDataQualityReport()
    errors: list[str] = []

    validated["observed_at"] = pd.to_datetime(
        validated["observed_at"],
        utc=True,
        errors="coerce",
    )

    if validated["observed_at"].isna().any():
        errors.append(
            "One or more weather timestamps are invalid."
        )

    unexpected_locations = (
        set(validated["location_id"].dropna().unique())
        - {expected_location_id}
    )

    if unexpected_locations:
        errors.append(
            f"Unexpected locations: {sorted(unexpected_locations)}"
        )

    duplicate_count = validated.duplicated(
        subset=["observed_at", "location_id"],
        keep=False,
    ).sum()

    if duplicate_count:
        errors.append(
            f"Found {duplicate_count} rows involved in duplicate keys."
        )

    # Basic physical sanity checks.
    humidity_invalid = (
        (validated["relative_humidity_2m"] < 0)
        | (validated["relative_humidity_2m"] > 100)
    ).sum()

    if humidity_invalid:
        errors.append(
            f"Found {humidity_invalid} invalid humidity values."
        )

    negative_precipitation = (
        validated["precipitation"] < 0
    ).sum()

    if negative_precipitation:
        errors.append(
            f"Found {negative_precipitation} negative precipitation values."
        )

    negative_wind = (
        validated["wind_speed_10m"] < 0
    ).sum()

    if negative_wind:
        errors.append(
            f"Found {negative_wind} negative wind-speed values."
        )

    report.missing_value_count = int(
        validated[WEATHER_COLUMNS]
        .isna()
        .sum()
        .sum()
    )

    if report.missing_value_count:
        report.warnings.append(
            f"{report.missing_value_count} weather values are missing."
        )

    periods = (
        validated["observed_at"]
        .dropna()
        .drop_duplicates()
        .sort_values()
    )

    if len(periods) > 1:
        differences = periods.diff().dropna()

        gaps = differences[
            differences.dt.total_seconds() != 3600
        ]

        report.non_hourly_gap_count = len(gaps)

        if report.non_hourly_gap_count:
            report.warnings.append(
                f"{report.non_hourly_gap_count} non-hourly gaps detected."
            )

    if errors:
        raise WeatherDataQualityError(
            "Weather data failed validation:\n- "
            + "\n- ".join(errors)
        )

    validated = (
        validated
        .sort_values("observed_at")
        .reset_index(drop=True)
    )

    return validated, report