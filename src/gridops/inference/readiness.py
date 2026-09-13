from __future__ import annotations

from datetime import datetime, timedelta, timezone

from gridops.storage.dynamodb import (
    get_latest_demand,
)


def get_serving_freshness_status(
    *,
    table_name: str,
    profile_name: str | None = None,
    region_name: str | None = None,
    expected_lag_hours: float = 2.0,
    checked_at: datetime | None = None,
) -> dict[str, object]:

    if checked_at is None:
        checked_at = datetime.now(
            timezone.utc
        )

    checked_hour = (
        checked_at
        .astimezone(timezone.utc)
        .replace(
            minute=0,
            second=0,
            microsecond=0,
        )
    )

    latest_item = get_latest_demand(
        table_name=table_name,
        profile_name=profile_name,
        region_name=region_name,
    )

    if latest_item is None:
        raise RuntimeError(
            "No usable PJM demand data "
            "was found in DynamoDB."
        )

    latest_observed_at = (
        datetime.fromisoformat(
            latest_item["sk"].replace(
                "Z",
                "+00:00",
            )
        )
    )

    required_latest_at = (
        checked_hour
        - timedelta(
            hours=expected_lag_hours
        )
    )

    source_lag_hours = (
        checked_hour
        - latest_observed_at
    ).total_seconds() / 3600

    freshness_gap_hours = (
        source_lag_hours
        - expected_lag_hours
    )

    return {
        "checked_at": checked_at,
        "checked_hour": checked_hour,
        "latest_observed_at":
            latest_observed_at,
        "required_latest_at":
            required_latest_at,
        "source_lag_hours":
            source_lag_hours,
        "expected_lag_hours":
            expected_lag_hours,
        "freshness_gap_hours":
            freshness_gap_hours,
        "is_fresh": (
            latest_observed_at
            >= required_latest_at
        ),
    }