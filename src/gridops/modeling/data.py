from __future__ import annotations

import pandas as pd
import psycopg


FEATURE_TABLES = {
    24: "marts.demand_forecast_features_24h",
    48: "marts.demand_forecast_features_48h",
}


VALIDATION_START = pd.Timestamp(
    "2025-07-01T00:00:00Z"
)

TEST_START = pd.Timestamp(
    "2025-10-01T00:00:00Z"
)


def load_feature_mart(
    *,
    dsn: str,
    horizon_hours: int,
) -> pd.DataFrame:

    if horizon_hours not in FEATURE_TABLES:
        raise ValueError(
            "horizon_hours must be 24 or 48."
        )

    table = FEATURE_TABLES[horizon_hours]

    query = f"""
        SELECT *
        FROM {table}
        ORDER BY target_at
    """

    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)

            rows = cursor.fetchall()

            columns = [
                description.name
                for description in cursor.description
            ]

    frame = pd.DataFrame(
        rows,
        columns=columns,
    )

    frame["target_at"] = pd.to_datetime(
        frame["target_at"],
        utc=True,
    )

    return frame


def add_time_split(
    frame: pd.DataFrame,
) -> pd.DataFrame:

    result = frame.copy()

    result["split"] = "train"

    result.loc[
        result["target_at"] >= VALIDATION_START,
        "split",
    ] = "validation"

    result.loc[
        result["target_at"] >= TEST_START,
        "split",
    ] = "test"

    return result