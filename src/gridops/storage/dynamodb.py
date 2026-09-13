from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable

import boto3
from boto3.dynamodb.conditions import Key


def _session(
    *,
    profile_name: str | None,
    region_name: str | None,
) -> boto3.Session:

    kwargs = {}

    if profile_name:
        kwargs["profile_name"] = profile_name

    if region_name:
        kwargs["region_name"] = region_name

    return boto3.Session(**kwargs)


def _as_utc(
    value: datetime,
) -> datetime:

    if value.tzinfo is None:
        value = value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    )


def demand_partition_key(
    respondent: str = "PJM",
) -> str:
    return f"{respondent}#DEMAND"


def demand_sort_key(
    period: datetime,
) -> str:

    period = _as_utc(period)

    return period.strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def write_demand_rows(
    rows: Iterable[tuple[datetime, float]],
    *,
    table_name: str,
    profile_name: str | None = None,
    region_name: str | None = None,
    respondent: str = "PJM",
) -> int:

    session = _session(
        profile_name=profile_name,
        region_name=region_name,
    )

    table = session.resource(
        "dynamodb"
    ).Table(table_name)

    count = 0

    with table.batch_writer(
        overwrite_by_pkeys=["pk", "sk"]
    ) as batch:

        for period, value in rows:

            period = _as_utc(period)

            batch.put_item(
                Item={
                    "pk": (
                        demand_partition_key(
                            respondent
                        )
                    ),
                    "sk": demand_sort_key(
                        period
                    ),
                    "respondent": respondent,
                    "data_type": "D",
                    "value": Decimal(
                        str(value)
                    ),
                    "unit": "megawatthours",
                }
            )

            count += 1

    return count


def get_latest_demand(
    *,
    table_name: str,
    profile_name: str | None = None,
    region_name: str | None = None,
    respondent: str = "PJM",
) -> dict | None:

    session = _session(
        profile_name=profile_name,
        region_name=region_name,
    )

    table = session.resource(
        "dynamodb"
    ).Table(table_name)

    response = table.query(
        KeyConditionExpression=(
            Key("pk").eq(
                demand_partition_key(
                    respondent
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

    item["value"] = float(
        item["value"]
    )

    return item


def query_demand_range(
    *,
    start: datetime,
    end: datetime,
    table_name: str,
    profile_name: str | None = None,
    region_name: str | None = None,
    respondent: str = "PJM",
) -> list[dict]:

    session = _session(
        profile_name=profile_name,
        region_name=region_name,
    )

    table = session.resource(
        "dynamodb"
    ).Table(table_name)

    response = table.query(
        KeyConditionExpression=(
            Key("pk").eq(
                demand_partition_key(
                    respondent
                )
            )
            & Key("sk").between(
                demand_sort_key(start),
                demand_sort_key(end),
            )
        ),
    )

    items = response.get(
        "Items",
        [],
    )

    for item in items:
        item["value"] = float(
            item["value"]
        )

    return items