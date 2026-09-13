from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


FORECAST_COLUMNS = [
    "temperature_2m_forecast_24h",
    "relative_humidity_2m_forecast_24h",
    "dew_point_2m_forecast_24h",
    "apparent_temperature_forecast_24h",
    "precipitation_forecast_24h",
    "wind_speed_10m_forecast_24h",
    "temperature_2m_forecast_48h",
    "relative_humidity_2m_forecast_48h",
    "dew_point_2m_forecast_48h",
    "apparent_temperature_forecast_48h",
    "precipitation_forecast_48h",
    "wind_speed_10m_forecast_48h",
]


REQUIRED_COLUMNS = {
    "valid_at",
    "location_id",
    "location_name",
    "latitude",
    "longitude",
    *FORECAST_COLUMNS,
}


class WeatherForecastQualityError(ValueError):
    """Raised when forecast weather fails a fatal quality rule."""


@dataclass
class WeatherForecastQualityReport:
    warnings: list[str] = field(default_factory=list)
    missing_value_count: int = 0
    non_hourly_gap_count: int = 0

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)


def validate_weather_forecast(
    frame: pd.DataFrame,
    *,
    expected_location_id: str,
) -> tuple[pd.DataFrame, WeatherForecastQualityReport]:

    if frame.empty:
        raise WeatherForecastQualityError(
            "Forecast weather dataset is empty."
        )

    missing_columns = REQUIRED_COLUMNS - set(frame.columns)

    if missing_columns:
        raise WeatherForecastQualityError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    validated = frame.copy()
    report = WeatherForecastQualityReport()
    errors: list[str] = []

    validated["valid_at"] = pd.to_datetime(
        validated["valid_at"],
        utc=True,
        errors="coerce",
    )

    if validated["valid_at"].isna().any():
        errors.append(
            "One or more forecast timestamps are invalid."
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
        subset=["valid_at", "location_id"],
        keep=False,
    ).sum()

    if duplicate_count:
        errors.append(
            f"Found {duplicate_count} rows involved in duplicate keys."
        )

    for horizon in (24, 48):
        humidity_column = (
            f"relative_humidity_2m_forecast_{horizon}h"
        )
        precipitation_column = (
            f"precipitation_forecast_{horizon}h"
        )
        wind_column = (
            f"wind_speed_10m_forecast_{horizon}h"
        )

        invalid_humidity = (
            (validated[humidity_column] < 0)
            | (validated[humidity_column] > 100)
        ).sum()

        if invalid_humidity:
            errors.append(
                f"Found {invalid_humidity} invalid "
                f"{horizon}h humidity values."
            )

        negative_precipitation = (
            validated[precipitation_column] < 0
        ).sum()

        if negative_precipitation:
            errors.append(
                f"Found {negative_precipitation} negative "
                f"{horizon}h precipitation values."
            )

        negative_wind = (
            validated[wind_column] < 0
        ).sum()

        if negative_wind:
            errors.append(
                f"Found {negative_wind} negative "
                f"{horizon}h wind values."
            )

    report.missing_value_count = int(
        validated[FORECAST_COLUMNS]
        .isna()
        .sum()
        .sum()
    )

    if report.missing_value_count:
        report.warnings.append(
            f"{report.missing_value_count} forecast values are missing."
        )

    periods = (
        validated["valid_at"]
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
        raise WeatherForecastQualityError(
            "Forecast weather failed validation:\n- "
            + "\n- ".join(errors)
        )

    validated = (
        validated
        .sort_values("valid_at")
        .reset_index(drop=True)
    )

    return validated, report