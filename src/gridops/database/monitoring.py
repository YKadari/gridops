from __future__ import annotations

from datetime import datetime, timezone

import psycopg
from datetime import datetime, timedelta, timezone

CREATE_FRESHNESS_TABLE_SQL = """
CREATE SCHEMA IF NOT EXISTS monitoring;

CREATE TABLE IF NOT EXISTS monitoring.eia_source_freshness (
    checked_at TIMESTAMPTZ NOT NULL,
    latest_observed_at TIMESTAMPTZ NOT NULL,
    source_lag_hours DOUBLE PRECISION NOT NULL,
    expected_lag_hours DOUBLE PRECISION NOT NULL,
    freshness_gap_hours DOUBLE PRECISION NOT NULL
);
"""


def initialize_freshness_table(
    dsn: str,
) -> None:
    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                CREATE_FRESHNESS_TABLE_SQL
            )

        connection.commit()



def get_latest_eia_observation(
    *,
    dsn: str,
) -> datetime:

    query = """
        SELECT MAX(period)
        FROM raw.eia_region_data
        WHERE respondent = 'PJM'
          AND data_type = 'D'
          AND value IS NOT NULL
    """
    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()

    if result is None or result[0] is None:
        raise RuntimeError(
            "No usable EIA demand observation found."
        )

    return result[0]


def record_eia_freshness(
    *,
    dsn: str,
    expected_lag_hours: float = 2.0,
    checked_at: datetime | None = None,
) -> dict[str, float | datetime]:

    if checked_at is None:
        checked_at = datetime.now(
            timezone.utc
        )

    latest = get_latest_eia_observation(
        dsn=dsn
    )

    checked_hour = checked_at.replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    source_lag_hours = (
        checked_hour - latest
    ).total_seconds() / 3600

    freshness_gap_hours = (
        source_lag_hours
        - expected_lag_hours
    )

    initialize_freshness_table(
        dsn
    )

    insert_sql = """
        INSERT INTO monitoring.eia_source_freshness (
            checked_at,
            latest_observed_at,
            source_lag_hours,
            expected_lag_hours,
            freshness_gap_hours
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                insert_sql,
                (
                    checked_at,
                    latest,
                    source_lag_hours,
                    expected_lag_hours,
                    freshness_gap_hours,
                ),
            )

        connection.commit()

    return {
        "checked_at": checked_at,
        "latest_observed_at": latest,
        "source_lag_hours": source_lag_hours,
        "expected_lag_hours": expected_lag_hours,
        "freshness_gap_hours": freshness_gap_hours,
    }

def get_eia_freshness_status(
    *,
    dsn: str,
    expected_lag_hours: float = 2.0,
    checked_at: datetime | None = None,
) -> dict[str, object]:

    if checked_at is None:
        checked_at = datetime.now(
            timezone.utc
        )

    checked_hour = checked_at.replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    latest = get_latest_eia_observation(
        dsn=dsn
    )

    required_latest_at = (
        checked_hour
        - timedelta(
            hours=expected_lag_hours
        )
    )

    source_lag_hours = (
        checked_hour - latest
    ).total_seconds() / 3600

    freshness_gap_hours = (
        source_lag_hours
        - expected_lag_hours
    )

    return {
        "checked_at": checked_at,
        "checked_hour": checked_hour,
        "latest_observed_at": latest,
        "required_latest_at": required_latest_at,
        "source_lag_hours": source_lag_hours,
        "expected_lag_hours": expected_lag_hours,
        "freshness_gap_hours": freshness_gap_hours,
        "is_fresh": (
            latest >= required_latest_at
        ),
    }