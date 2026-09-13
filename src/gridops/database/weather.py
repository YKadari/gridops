from __future__ import annotations

import pandas as pd
import psycopg


CREATE_WEATHER_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw.weather_hourly (
    observed_at TIMESTAMPTZ NOT NULL,
    location_id TEXT NOT NULL,
    location_name TEXT NOT NULL,

    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,

    temperature_2m DOUBLE PRECISION,
    relative_humidity_2m DOUBLE PRECISION,
    dew_point_2m DOUBLE PRECISION,
    apparent_temperature DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    wind_speed_10m DOUBLE PRECISION,

    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (
        observed_at,
        location_id
    )
);
"""


UPSERT_WEATHER_SQL = """
INSERT INTO raw.weather_hourly (
    observed_at,
    location_id,
    location_name,
    latitude,
    longitude,
    temperature_2m,
    relative_humidity_2m,
    dew_point_2m,
    apparent_temperature,
    precipitation,
    wind_speed_10m
)
VALUES (
    %(observed_at)s,
    %(location_id)s,
    %(location_name)s,
    %(latitude)s,
    %(longitude)s,
    %(temperature_2m)s,
    %(relative_humidity_2m)s,
    %(dew_point_2m)s,
    %(apparent_temperature)s,
    %(precipitation)s,
    %(wind_speed_10m)s
)
ON CONFLICT (
    observed_at,
    location_id
)
DO UPDATE SET
    location_name = EXCLUDED.location_name,
    latitude = EXCLUDED.latitude,
    longitude = EXCLUDED.longitude,
    temperature_2m = EXCLUDED.temperature_2m,
    relative_humidity_2m = EXCLUDED.relative_humidity_2m,
    dew_point_2m = EXCLUDED.dew_point_2m,
    apparent_temperature = EXCLUDED.apparent_temperature,
    precipitation = EXCLUDED.precipitation,
    wind_speed_10m = EXCLUDED.wind_speed_10m,
    ingested_at = NOW();
"""


def initialize_weather_table(
    dsn: str,
) -> None:
    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "CREATE SCHEMA IF NOT EXISTS raw;"
            )

            cursor.execute(
                CREATE_WEATHER_TABLE_SQL
            )

        connection.commit()


def load_weather_data(
    frame: pd.DataFrame,
    *,
    dsn: str,
) -> int:
    database_frame = frame.copy()

    nullable_columns = [
        "temperature_2m",
        "relative_humidity_2m",
        "dew_point_2m",
        "apparent_temperature",
        "precipitation",
        "wind_speed_10m",
    ]

    for column in nullable_columns:
        database_frame[column] = (
            database_frame[column]
            .astype(object)
            .where(
                database_frame[column].notna(),
                None,
            )
        )

    records = database_frame[
        [
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
        ]
    ].to_dict(
        orient="records"
    )

    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                UPSERT_WEATHER_SQL,
                records,
            )

        connection.commit()

    return len(records)