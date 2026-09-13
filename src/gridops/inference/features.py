from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from zoneinfo import ZoneInfo

import holidays
import pandas as pd
import psycopg

from gridops.ingestion.weather import (
    LIVE_FORECAST_URL,
    OpenMeteoClient,
    PJM_WEATHER_LOCATIONS,
)
from gridops.modeling.models import (
    FEATURES_BY_HORIZON,
)


EASTERN = ZoneInfo(
    "America/New_York"
)


HORIZON_CONFIG = {
    24: {
        "latest_lag": 26,
        "second_lag": 48,
        "rolling_24_start": 49,
        "rolling_168_start": 193,
    },
    48: {
        "latest_lag": 50,
        "second_lag": 72,
        "rolling_24_start": 73,
        "rolling_168_start": 217,
    },
}


def floor_to_utc_hour(
    value: datetime,
) -> datetime:

    value = value.astimezone(
        timezone.utc
    )

    return value.replace(
        minute=0,
        second=0,
        microsecond=0,
    )


def _load_demand_history(
    *,
    dsn: str,
    start: datetime,
    end: datetime,
) -> pd.Series:

    query = """
        SELECT
            observed_at,
            demand_value
        FROM staging.stg_eia_demand
        WHERE observed_at >= %s
          AND observed_at <= %s
        ORDER BY observed_at
    """

    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (start, end),
            )

            rows = cursor.fetchall()

    if not rows:
        raise RuntimeError(
            "No recent PJM demand data "
            "was found for inference."
        )

    frame = pd.DataFrame(
        rows,
        columns=[
            "observed_at",
            "demand_value",
        ],
    )

    frame["observed_at"] = pd.to_datetime(
        frame["observed_at"],
        utc=True,
    )

    frame["demand_value"] = pd.to_numeric(
        frame["demand_value"],
        errors="coerce",
    )

    # Rebuild an explicit hourly spine.
    # This prevents a missing source row from
    # silently changing the meaning of our lags.
    hourly_index = pd.date_range(
        start=start,
        end=end,
        freq="h",
        tz="UTC",
    )

    demand = (
        frame
        .drop_duplicates(
            subset=["observed_at"],
            keep="last",
        )
        .set_index("observed_at")
        ["demand_value"]
        .reindex(hourly_index)
    )

    return demand


def _require_demand_value(
    demand: pd.Series,
    *,
    timestamp: datetime,
    feature_name: str,
) -> float:

    key = pd.Timestamp(
        timestamp
    )

    value = demand.get(
        key
    )

    if value is None or pd.isna(value):
        raise RuntimeError(
            f"Cannot build {feature_name}: "
            f"demand is unavailable at "
            f"{timestamp.isoformat()}."
        )

    return float(value)


def _build_demand_features(
    *,
    dsn: str,
    target_at: datetime,
    horizon_hours: int,
) -> dict[str, float]:

    config = HORIZON_CONFIG[
        horizon_hours
    ]

    latest_lag = int(
        config["latest_lag"]
    )

    second_lag = int(
        config["second_lag"]
    )

    rolling_24_start = int(
        config["rolling_24_start"]
    )

    rolling_168_start = int(
        config["rolling_168_start"]
    )

    earliest_needed = (
        target_at
        - timedelta(hours=336)
    )

    latest_needed = (
        target_at
        - timedelta(hours=latest_lag)
    )

    demand = _load_demand_history(
        dsn=dsn,
        start=earliest_needed,
        end=latest_needed,
    )

    latest_feature_name = (
        f"demand_lag_{latest_lag}h"
    )

    second_feature_name = (
        f"demand_lag_{second_lag}h"
    )

    features = {
        latest_feature_name:
            _require_demand_value(
                demand,
                timestamp=(
                    target_at
                    - timedelta(
                        hours=latest_lag
                    )
                ),
                feature_name=(
                    latest_feature_name
                ),
            ),

        second_feature_name:
            _require_demand_value(
                demand,
                timestamp=(
                    target_at
                    - timedelta(
                        hours=second_lag
                    )
                ),
                feature_name=(
                    second_feature_name
                ),
            ),

        "demand_lag_168h":
            _require_demand_value(
                demand,
                timestamp=(
                    target_at
                    - timedelta(hours=168)
                ),
                feature_name=(
                    "demand_lag_168h"
                ),
            ),

        "demand_lag_336h":
            _require_demand_value(
                demand,
                timestamp=(
                    target_at
                    - timedelta(hours=336)
                ),
                feature_name=(
                    "demand_lag_336h"
                ),
            ),
    }

    rolling_24 = demand.loc[
        pd.Timestamp(
            target_at
            - timedelta(
                hours=rolling_24_start
            )
        ):
        pd.Timestamp(
            target_at
            - timedelta(
                hours=latest_lag
            )
        )
    ]

    rolling_168 = demand.loc[
        pd.Timestamp(
            target_at
            - timedelta(
                hours=rolling_168_start
            )
        ):
        pd.Timestamp(
            target_at
            - timedelta(
                hours=latest_lag
            )
        )
    ]

    if rolling_24.count() == 0:
        raise RuntimeError(
            "No usable demand values in "
            "the recent 24-hour window."
        )

    if rolling_168.count() == 0:
        raise RuntimeError(
            "No usable demand values in "
            "the recent 168-hour window."
        )

    features[
        "demand_rolling_mean_24h"
    ] = float(
        rolling_24.mean()
    )

    features[
        "demand_rolling_mean_168h"
    ] = float(
        rolling_168.mean()
    )

    features[
        "demand_history_count_24h"
    ] = float(
        rolling_24.count()
    )

    features[
        "demand_history_count_168h"
    ] = float(
        rolling_168.count()
    )

    return features


def _build_weather_features(
    *,
    target_at: datetime,
    horizon_hours: int,
) -> dict[str, float]:

    client = OpenMeteoClient(
        base_url=LIVE_FORECAST_URL
    )

    rows = []

    for location in (
        PJM_WEATHER_LOCATIONS.values()
    ):

        frame = client.fetch_hourly(
            location=location,
            start_date=target_at.date(),
            end_date=target_at.date(),
        )

        matching = frame[
            frame["observed_at"]
            == pd.Timestamp(target_at)
        ]

        if len(matching) != 1:
            raise RuntimeError(
                f"Expected one weather forecast "
                f"for {location.location_id} at "
                f"{target_at.isoformat()}, "
                f"found {len(matching)}."
            )

        rows.append(
            matching.iloc[0]
        )

    regional = pd.DataFrame(
        rows
    )

    if len(regional) != len(
        PJM_WEATHER_LOCATIONS
    ):
        raise RuntimeError(
            "Not all PJM weather locations "
            "were available."
        )

    weather_columns = [
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "apparent_temperature",
        "precipitation",
        "wind_speed_10m",
    ]

    if regional[
        weather_columns
    ].isna().any().any():
        raise RuntimeError(
            "Live weather forecast contains "
            "missing feature values."
        )

    suffix = (
        f"{horizon_hours}h"
    )

    mean_temperature = float(
        regional[
            "temperature_2m"
        ].mean()
    )

    minimum_temperature = float(
        regional[
            "temperature_2m"
        ].min()
    )

    maximum_temperature = float(
        regional[
            "temperature_2m"
        ].max()
    )

    return {
        f"mean_temperature_forecast_{suffix}":
            mean_temperature,

        f"min_temperature_forecast_{suffix}":
            minimum_temperature,

        f"max_temperature_forecast_{suffix}":
            maximum_temperature,

        f"temperature_range_forecast_{suffix}":
            (
                maximum_temperature
                - minimum_temperature
            ),

        f"mean_humidity_forecast_{suffix}":
            float(
                regional[
                    "relative_humidity_2m"
                ].mean()
            ),

        f"mean_dew_point_forecast_{suffix}":
            float(
                regional[
                    "dew_point_2m"
                ].mean()
            ),

        f"mean_apparent_temperature_forecast_{suffix}":
            float(
                regional[
                    "apparent_temperature"
                ].mean()
            ),

        f"mean_precipitation_forecast_{suffix}":
            float(
                regional[
                    "precipitation"
                ].mean()
            ),

        f"mean_wind_speed_forecast_{suffix}":
            float(
                regional[
                    "wind_speed_10m"
                ].mean()
            ),

        "cooling_degree_feature":
            max(
                mean_temperature - 18.0,
                0.0,
            ),

        "heating_degree_feature":
            max(
                18.0 - mean_temperature,
                0.0,
            ),
    }


def _build_calendar_features(
    *,
    target_at: datetime,
) -> dict[str, object]:

    local_target = (
        target_at
        .astimezone(EASTERN)
    )

    local_date = (
        local_target.date()
    )

    calendar = (
        holidays.UnitedStates(
            years=[
                local_date.year,
            ],
            observed=True,
        )
    )

    day_before = (
        local_date
        + timedelta(days=1)
    )

    day_after = (
        local_date
        - timedelta(days=1)
    )

    iso_day = (
        local_target.isoweekday()
    )

    return {
        "target_hour":
            local_target.hour,

        "target_day_of_week":
            iso_day,

        "target_month":
            local_target.month,

        "is_weekend":
            iso_day in (6, 7),

        "is_holiday":
            local_date in calendar,

        "is_day_before_holiday":
            day_before in calendar,

        "is_day_after_holiday":
            day_after in calendar,
    }


def build_inference_features(
    *,
    dsn: str,
    horizon_hours: int,
    now: datetime | None = None,
) -> tuple[
    dict[str, object],
    datetime,
    datetime,
]:

    if horizon_hours not in (
        24,
        48,
    ):
        raise ValueError(
            "horizon_hours must be "
            "24 or 48."
        )

    if now is None:
        now = datetime.now(
            timezone.utc
        )

    issue_at = floor_to_utc_hour(
        now
    )

    target_at = (
        issue_at
        + timedelta(
            hours=horizon_hours
        )
    )

    features: dict[str, object] = {}

    features.update(
        _build_demand_features(
            dsn=dsn,
            target_at=target_at,
            horizon_hours=horizon_hours,
        )
    )

    features.update(
        _build_weather_features(
            target_at=target_at,
            horizon_hours=horizon_hours,
        )
    )

    features.update(
        _build_calendar_features(
            target_at=target_at
        )
    )

    expected = FEATURES_BY_HORIZON[
        horizon_hours
    ]

    missing = [
        feature
        for feature in expected
        if feature not in features
    ]

    if missing:
        raise RuntimeError(
            f"Inference feature builder "
            f"did not create: {missing}"
        )

    # Return exactly the features used
    # by the trained pipeline.
    ordered_features = {
        feature: features[feature]
        for feature in expected
    }

    return (
        ordered_features,
        issue_at,
        target_at,
    )