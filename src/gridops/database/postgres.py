from __future__ import annotations

import pandas as pd
import psycopg


CREATE_SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS raw;
"""


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw.eia_region_data (
    period TIMESTAMPTZ NOT NULL,
    respondent TEXT NOT NULL,
    respondent_name TEXT NOT NULL,
    data_type TEXT NOT NULL,
    type_name TEXT NOT NULL,
    value DOUBLE PRECISION,
    value_units TEXT NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (period, respondent, data_type)
);
"""

ALLOW_NULL_VALUES_SQL = """
ALTER TABLE raw.eia_region_data
ALTER COLUMN value DROP NOT NULL;
"""

UPSERT_SQL = """
INSERT INTO raw.eia_region_data (
    period,
    respondent,
    respondent_name,
    data_type,
    type_name,
    value,
    value_units
)
VALUES (
    %(period)s,
    %(respondent)s,
    %(respondent_name)s,
    %(data_type)s,
    %(type_name)s,
    %(value)s,
    %(value_units)s
)
ON CONFLICT (period, respondent, data_type)
DO UPDATE SET
    respondent_name = EXCLUDED.respondent_name,
    type_name = EXCLUDED.type_name,
    value = EXCLUDED.value,
    value_units = EXCLUDED.value_units,
    ingested_at = NOW();
"""


def initialize_database(dsn: str) -> None:
    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(CREATE_SCHEMA_SQL)
            cursor.execute(CREATE_TABLE_SQL)
            cursor.execute(ALLOW_NULL_VALUES_SQL)

        connection.commit()

def load_eia_data(
    frame: pd.DataFrame,
    *,
    dsn: str,
) -> int:
    database_frame = frame.rename(
        columns={
            "respondent-name": "respondent_name",
            "type": "data_type",
            "type-name": "type_name",
            "value-units": "value_units",
        }
    )

    database_frame["value"] = (
    database_frame["value"]
    .astype(object)
    .where(database_frame["value"].notna(), None)
    )

    records = database_frame[
        [
            "period",
            "respondent",
            "respondent_name",
            "data_type",
            "type_name",
            "value",
            "value_units",
        ]
    ].to_dict(orient="records")

    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                UPSERT_SQL,
                records,
            )

        connection.commit()

    return len(records)