from __future__ import annotations

from datetime import timedelta

import psycopg

from gridops.config import Settings
from gridops.storage.dynamodb import (
    get_latest_demand,
    write_demand_rows,
)


BACKFILL_DAYS = 21


def load_recent_postgres_demand(
    *,
    dsn: str,
) -> list[tuple]:

    query = """
        WITH latest AS (
            SELECT MAX(period) AS max_period
            FROM raw.eia_region_data
            WHERE respondent = 'PJM'
              AND data_type = 'D'
              AND value IS NOT NULL
        )
        SELECT
            period,
            value
        FROM raw.eia_region_data
        CROSS JOIN latest
        WHERE respondent = 'PJM'
          AND data_type = 'D'
          AND value IS NOT NULL
          AND period >= (
              latest.max_period
              - INTERVAL '21 days'
          )
        ORDER BY period
    """

    with psycopg.connect(
        dsn
    ) as connection:

        with connection.cursor() as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

    return [
        (
            period,
            float(value),
        )
        for period, value in rows
    ]


def main() -> None:
    settings = Settings()

    rows = load_recent_postgres_demand(
        dsn=settings.postgres_dsn
    )

    print(
        f"Loaded {len(rows)} "
        "recent demand rows from PostgreSQL."
    )

    if not rows:
        raise RuntimeError(
            "No demand rows found."
        )

    print(
        f"First timestamp: {rows[0][0]}"
    )

    print(
        f"Last timestamp:  {rows[-1][0]}"
    )

    written = write_demand_rows(
        rows,
        table_name=(
            settings.dynamodb_demand_table
        ),
        profile_name=settings.aws_profile,
        region_name=settings.aws_region,
    )

    print(
        f"Wrote {written} rows "
        "to DynamoDB."
    )

    latest = get_latest_demand(
        table_name=(
            settings.dynamodb_demand_table
        ),
        profile_name=settings.aws_profile,
        region_name=settings.aws_region,
    )

    print()
    print("LATEST DYNAMODB DEMAND")
    print("=" * 50)
    print(latest)

    print()
    print(
        "✅ DynamoDB demand backfill "
        "completed."
    )


if __name__ == "__main__":
    main()