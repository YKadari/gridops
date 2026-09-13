from __future__ import annotations

import pandas as pd
import psycopg


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw.weather_forecast_hourly (
    valid_at TIMESTAMPTZ NOT NULL,
    location_id TEXT NOT NULL,
    location_name TEXT NOT NULL,

    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,

    temperature_2m_forecast_24h DOUBLE PRECISION,
    relative_humidity_2m_forecast_24h DOUBLE PRECISION,
    dew_point_2m_forecast_24h DOUBLE PRECISION,
    apparent_temperature_forecast_24h DOUBLE PRECISION,
    precipitation_forecast_24h DOUBLE PRECISION,
    wind_speed_10m_forecast_24h DOUBLE PRECISION,

    temperature_2m_forecast_48h DOUBLE PRECISION,
    relative_humidity_2m_forecast_48h DOUBLE PRECISION,
    dew_point_2m_forecast_48h DOUBLE PRECISION,
    apparent_temperature_forecast_48h DOUBLE PRECISION,
    precipitation_forecast_48h DOUBLE PRECISION,
    wind_speed_10m_forecast_48h DOUBLE PRECISION,

    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (
        valid_at,
        location_id
    )
);
"""


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


UPSERT_SQL = """
INSERT INTO raw.weather_forecast_hourly (
    valid_at,
    location_id,
    location_name,
    latitude,
    longitude,

    temperature_2m_forecast_24h,
    relative_humidity_2m_forecast_24h,
    dew_point_2m_forecast_24h,
    apparent_temperature_forecast_24h,
    precipitation_forecast_24h,
    wind_speed_10m_forecast_24h,

    temperature_2m_forecast_48h,
    relative_humidity_2m_forecast_48h,
    dew_point_2m_forecast_48h,
    apparent_temperature_forecast_48h,
    precipitation_forecast_48h,
    wind_speed_10m_forecast_48h
)
VALUES (
    %(valid_at)s,
    %(location_id)s,
    %(location_name)s,
    %(latitude)s,
    %(longitude)s,

    %(temperature_2m_forecast_24h)s,
    %(relative_humidity_2m_forecast_24h)s,
    %(dew_point_2m_forecast_24h)s,
    %(apparent_temperature_forecast_24h)s,
    %(precipitation_forecast_24h)s,
    %(wind_speed_10m_forecast_24h)s,

    %(temperature_2m_forecast_48h)s,
    %(relative_humidity_2m_forecast_48h)s,
    %(dew_point_2m_forecast_48h)s,
    %(apparent_temperature_forecast_48h)s,
    %(precipitation_forecast_48h)s,
    %(wind_speed_10m_forecast_48h)s
)
ON CONFLICT (
    valid_at,
    location_id
)
DO UPDATE SET
    location_name = EXCLUDED.location_name,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,

    temperature_2m_forecast_24h =
        EXCLUDED.temperature_2m_forecast_24h,
    relative_humidity_2m_forecast_24h =
        EXCLUDED.relative_humidity_2m_forecast_24h,
    dew_point_2m_forecast_24h =
        EXCLUDED.dew_point_2m_forecast_24h,
    apparent_temperature_forecast_24h =
        EXCLUDED.apparent_temperature_forecast_24h,
    precipitation_forecast_24h =
        EXCLUDED.precipitation_forecast_24h,
    wind_speed_10m_forecast_24h =
        EXCLUDED.wind_speed_10m_forecast_24h,

    temperature_2m_forecast_48h =
        EXCLUDED.temperature_2m_forecast_48h,
    relative_humidity_2m_forecast_48h =
        EXCLUDED.relative_humidity_2m_forecast_48h,
    dew_point_2m_forecast_48h =
        EXCLUDED.dew_point_2m_forecast_48h,
    apparent_temperature_forecast_48h =
        EXCLUDED.apparent_temperature_forecast_48h,
    precipitation_forecast_48h =
        EXCLUDED.precipitation_forecast_48h,
    wind_speed_10m_forecast_48h =
        EXCLUDED.wind_speed_10m_forecast_48h,

    ingested_at = NOW();
"""


def initialize_weather_forecast_table(
    dsn: str,
) -> None:
    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE SCHEMA IF NOT EXISTS raw;"
            )

            cursor.execute(
                CREATE_TABLE_SQL
            )

        connection.commit()


def load_weather_forecast_data(
    frame: pd.DataFrame,
    *,
    dsn: str,
) -> int:

    database_frame = frame.copy()

    for column in FORECAST_COLUMNS:
        database_frame[column] = (
            database_frame[column]
            .astype(object)
            .where(
                database_frame[column].notna(),
                None,
            )
        )

    columns = [
        "valid_at",
        "location_id",
        "location_name",
        "latitude",
        "longitude",
        *FORECAST_COLUMNS,
    ]

    records = database_frame[
        columns
    ].to_dict(
        orient="records"
    )

    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                UPSERT_SQL,
                records,
            )

        connection.commit()

    return len(records)