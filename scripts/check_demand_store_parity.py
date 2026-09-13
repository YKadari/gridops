from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import psycopg

from gridops.config import Settings
from gridops.storage.dynamodb import (
    get_latest_demand,
    query_demand_range,
)


HISTORY_HOURS = 336


def load_postgres_history(
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

    index = pd.date_range(
        start=start,
        end=end,
        freq="h",
        tz="UTC",
    )

    return (
        frame
        .set_index("observed_at")
        ["demand_value"]
        .reindex(index)
    )


def load_dynamodb_history(
    *,
    settings: Settings,
    start: datetime,
    end: datetime,
) -> pd.Series:

    items = query_demand_range(
        start=start,
        end=end,
        table_name=settings.dynamodb_demand_table,
        profile_name=settings.aws_profile,
        region_name=settings.aws_region,
    )

    frame = pd.DataFrame(
        [
            {
                "observed_at": item["sk"],
                "demand_value": item["value"],
            }
            for item in items
        ]
    )

    if frame.empty:
        raise RuntimeError(
            "No DynamoDB demand rows found."
        )

    frame["observed_at"] = pd.to_datetime(
        frame["observed_at"],
        utc=True,
    )

    frame["demand_value"] = pd.to_numeric(
        frame["demand_value"],
        errors="coerce",
    )

    index = pd.date_range(
        start=start,
        end=end,
        freq="h",
        tz="UTC",
    )

    return (
        frame
        .set_index("observed_at")
        ["demand_value"]
        .reindex(index)
    )


def main() -> None:
    settings = Settings()

    latest = get_latest_demand(
        table_name=settings.dynamodb_demand_table,
        profile_name=settings.aws_profile,
        region_name=settings.aws_region,
    )

    if latest is None:
        raise RuntimeError(
            "DynamoDB serving table is empty."
        )

    end = pd.Timestamp(
        latest["sk"]
    ).to_pydatetime()

    start = (
        end
        - timedelta(
            hours=HISTORY_HOURS
        )
    )

    postgres = load_postgres_history(
        dsn=settings.postgres_dsn,
        start=start,
        end=end,
    )

    dynamodb = load_dynamodb_history(
        settings=settings,
        start=start,
        end=end,
    )

    comparison = pd.DataFrame(
        {
            "postgres": postgres,
            "dynamodb": dynamodb,
        }
    )

    both_present = comparison.dropna()

    mismatches = both_present[
        (
            both_present["postgres"]
            - both_present["dynamodb"]
        ).abs() > 1e-9
    ]

    missing_pattern_matches = (
        comparison["postgres"].isna()
        == comparison["dynamodb"].isna()
    ).all()

    print()
    print("DEMAND STORE PARITY CHECK")
    print("=" * 60)
    print(f"Start: {start}")
    print(f"End:   {end}")
    print(
        f"Hourly timestamps checked: "
        f"{len(comparison)}"
    )
    print(
        f"Postgres usable values: "
        f"{comparison['postgres'].count()}"
    )
    print(
        f"DynamoDB usable values: "
        f"{comparison['dynamodb'].count()}"
    )
    print(
        f"Value mismatches: "
        f"{len(mismatches)}"
    )
    print(
        f"Missing-value pattern matches: "
        f"{missing_pattern_matches}"
    )

    assert len(mismatches) == 0
    assert missing_pattern_matches

    print()
    print(
        "✅ PostgreSQL and DynamoDB "
        "demand history match."
    )


if __name__ == "__main__":
    main()