from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd
import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)


HISTORICAL_FORECAST_URL = (
    "https://historical-forecast-api.open-meteo.com/v1/forecast"
)

HOURLY_VARIABLES = (
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation",
    "wind_speed_10m",
)

PREVIOUS_RUNS_URL = (
    "https://previous-runs-api.open-meteo.com/v1/forecast"
)

FORECAST_WEATHER_VARIABLES = (
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation",
    "wind_speed_10m",
)

FORECAST_HORIZONS = {
    1: 24,
    2: 48,
}


class WeatherAPIError(RuntimeError):
    """Raised when Open-Meteo returns an invalid or unusable response."""


@dataclass(frozen=True)
class WeatherLocation:
    location_id: str
    name: str
    latitude: float
    longitude: float


PJM_WEATHER_LOCATIONS = {
    "philadelphia": WeatherLocation(
        location_id="philadelphia",
        name="Philadelphia, PA",
        latitude=39.9526,
        longitude=-75.1652,
    ),
    "pittsburgh": WeatherLocation(
        location_id="pittsburgh",
        name="Pittsburgh, PA",
        latitude=40.4406,
        longitude=-79.9959,
    ),
    "washington_dc": WeatherLocation(
        location_id="washington_dc",
        name="Washington, DC",
        latitude=38.9072,
        longitude=-77.0369,
    ),
    "columbus": WeatherLocation(
        location_id="columbus",
        name="Columbus, OH",
        latitude=39.9612,
        longitude=-82.9988,
    ),
    "baltimore": WeatherLocation(
        location_id="baltimore",
        name="Baltimore, MD",
        latitude=39.2904,
        longitude=-76.6122,
    ),
    "richmond": WeatherLocation(
        location_id="richmond",
        name="Richmond, VA",
        latitude=37.5407,
        longitude=-77.4360,
    ),
}




def parse_hourly_weather_response(
    payload: dict[str, Any],
    *,
    location: WeatherLocation,
) -> pd.DataFrame:
    hourly = payload.get("hourly")

    if not isinstance(hourly, dict):
        raise WeatherAPIError(
            "Open-Meteo response did not contain hourly weather data."
        )

    times = hourly.get("time")

    if not isinstance(times, list):
        raise WeatherAPIError(
            "Open-Meteo response did not contain hourly timestamps."
        )

    frame = pd.DataFrame(
        {
            "observed_at": pd.to_datetime(
                times,
                utc=True,
                errors="coerce",
            )
        }
    )

    for variable in HOURLY_VARIABLES:
        values = hourly.get(variable)

        if not isinstance(values, list):
            raise WeatherAPIError(
                f"Missing hourly variable: {variable}"
            )

        if len(values) != len(frame):
            raise WeatherAPIError(
                f"{variable} has {len(values)} values "
                f"but expected {len(frame)}."
            )

        frame[variable] = pd.to_numeric(
            values,
            errors="coerce",
        )

    frame.insert(
        1,
        "location_id",
        location.location_id,
    )

    frame.insert(
        2,
        "location_name",
        location.name,
    )

    frame["latitude"] = location.latitude
    frame["longitude"] = location.longitude

    return frame


class OpenMeteoClient:
    def __init__(
        self,
        base_url: str = HISTORICAL_FORECAST_URL,
        timeout_seconds: int = 60,
    ) -> None:
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    @retry(
        retry=retry_if_exception_type(
            (
                requests.RequestException,
                WeatherAPIError,
            )
        ),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=10,
        ),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def fetch_hourly(
        self,
        *,
        location: WeatherLocation,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": ",".join(HOURLY_VARIABLES),
            "timezone": "UTC",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
        }

        response = requests.get(
            self.base_url,
            params=params,
            timeout=self.timeout_seconds,
        )

        response.raise_for_status()

        payload = response.json()

        if payload.get("error"):
            raise WeatherAPIError(
                payload.get(
                    "reason",
                    "Open-Meteo returned an error.",
                )
            )

        return parse_hourly_weather_response(
            payload,
            location=location,
        )


class OpenMeteoPreviousRunsClient:
    def __init__(
        self,
        base_url: str = PREVIOUS_RUNS_URL,
        timeout_seconds: int = 60,
    ) -> None:
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    @retry(
        retry=retry_if_exception_type(
            (
                requests.RequestException,
                WeatherAPIError,
            )
        ),
        wait=wait_exponential(
            multiplier=1,
            min=1,
            max=10,
        ),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def fetch_hourly(
        self,
        *,
        location: WeatherLocation,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:

        requested_variables = []

        for previous_day in FORECAST_HORIZONS:
            for variable in FORECAST_WEATHER_VARIABLES:
                requested_variables.append(
                    f"{variable}_previous_day{previous_day}"
                )

        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "hourly": ",".join(requested_variables),
            "timezone": "UTC",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm",
        }

        response = requests.get(
            self.base_url,
            params=params,
            timeout=self.timeout_seconds,
        )

        response.raise_for_status()

        payload = response.json()

        if payload.get("error"):
            raise WeatherAPIError(
                payload.get(
                    "reason",
                    "Open-Meteo Previous Runs API returned an error.",
                )
            )

        hourly = payload.get("hourly")

        if not isinstance(hourly, dict):
            raise WeatherAPIError(
                "Previous Runs response did not contain hourly data."
            )

        times = hourly.get("time")

        if not isinstance(times, list):
            raise WeatherAPIError(
                "Previous Runs response did not contain timestamps."
            )

        frame = pd.DataFrame(
            {
                "valid_at": pd.to_datetime(
                    times,
                    utc=True,
                    errors="coerce",
                )
            }
        )

        frame.insert(
            1,
            "location_id",
            location.location_id,
        )

        frame.insert(
            2,
            "location_name",
            location.name,
        )

        frame["latitude"] = location.latitude
        frame["longitude"] = location.longitude

        for previous_day, horizon_hours in (
            FORECAST_HORIZONS.items()
        ):
            for variable in FORECAST_WEATHER_VARIABLES:

                source_column = (
                    f"{variable}_previous_day"
                    f"{previous_day}"
                )

                output_column = (
                    f"{variable}_forecast_"
                    f"{horizon_hours}h"
                )

                values = hourly.get(source_column)

                if not isinstance(values, list):
                    raise WeatherAPIError(
                        f"Missing forecast variable: "
                        f"{source_column}"
                    )

                if len(values) != len(frame):
                    raise WeatherAPIError(
                        f"{source_column} returned "
                        f"{len(values)} values; "
                        f"expected {len(frame)}."
                    )

                frame[output_column] = pd.to_numeric(
                    values,
                    errors="coerce",
                )

        return frame