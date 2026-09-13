from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key


def _session(
    *,
    profile_name: str | None,
    region_name: str | None,
) -> boto3.Session:

    if profile_name:
        return boto3.Session(
            profile_name=profile_name,
            region_name=region_name,
        )

    return boto3.Session(
        region_name=region_name,
    )


def _utc_key(
    value: datetime,
) -> str:
    value = value.astimezone(
        timezone.utc
    )

    return value.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def forecast_partition_key(
    horizon_hours: int,
) -> str:
    return f"FORECAST#{horizon_hours}h"


def write_forecast(
    *,
    table_name: str,
    profile_name: str | None,
    region_name: str | None,
    horizon_hours: int,
    issue_at: datetime,
    target_at: datetime,
    predicted_demand: float,
    units: str,
    eia_latest_observed_at: datetime,
) -> None:

    session = _session(
        profile_name=profile_name,
        region_name=region_name,
    )

    table = session.resource(
        "dynamodb"
    ).Table(
        table_name
    )

    issue_key = _utc_key(
        issue_at
    )

    table.put_item(
        Item={
            "pk": forecast_partition_key(
                horizon_hours
            ),
            "sk": issue_key,
            "horizon_hours": Decimal(
                str(horizon_hours)
            ),
            "issue_at": issue_key,
            "target_at": _utc_key(
                target_at
            ),
            "predicted_demand": Decimal(
                str(predicted_demand)
            ),
            "units": units,
            "eia_latest_observed_at":
                _utc_key(
                    eia_latest_observed_at
                ),
        }
    )


def get_latest_forecast(
    *,
    table_name: str,
    horizon_hours: int,
    profile_name: str | None = None,
    region_name: str | None = None,
) -> dict | None:

    session = _session(
        profile_name=profile_name,
        region_name=region_name,
    )

    table = session.resource(
        "dynamodb"
    ).Table(
        table_name
    )

    response = table.query(
        KeyConditionExpression=(
            Key("pk").eq(
                forecast_partition_key(
                    horizon_hours
                )
            )
        ),
        ScanIndexForward=False,
        Limit=1,
    )

    items = response.get(
        "Items",
        [],
    )

    if not items:
        return None

    item = items[0]

    item["horizon_hours"] = int(
        item["horizon_hours"]
    )

    item["predicted_demand"] = float(
        item["predicted_demand"]
    )

    return item