from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import pandas as pd

from gridops.config import Settings
from gridops.ingestion.backfill import to_eia_inclusive_end
from gridops.ingestion.eia import EIAClient
from gridops.ingestion.incremental import plan_incremental_window
from gridops.quality.eia import validate_eia_demand
from gridops.storage.dynamodb import (
    get_latest_demand,
    write_demand_rows,
)
from gridops.storage.s3 import (
    build_raw_eia_key,
    upload_eia_frame,
)


logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _eia_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H")


def _latest_serving_period(
    settings: Settings,
) -> datetime | None:
    latest = get_latest_demand(
        table_name=settings.dynamodb_demand_table,
        profile_name=settings.aws_profile,
        region_name=settings.aws_region,
        respondent="PJM",
    )

    if latest is None:
        return None

    return datetime.fromisoformat(
        latest["sk"].replace(
            "Z",
            "+00:00",
        )
    )


def _plan_window(
    *,
    settings: Settings,
) -> tuple[datetime, datetime]:
    latest_period = _latest_serving_period(
        settings
    )

    if latest_period is not None:
        return plan_incremental_window(
            latest_period
        )

    # Safety fallback if the serving table
    # is ever empty.
    end = datetime.now(
        timezone.utc
    ).replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    start = end - timedelta(
        hours=24
    )

    return start, end


def handler(
    event,
    context,
) -> dict[str, object]:
    settings = Settings()

    if not settings.eia_api_key:
        raise RuntimeError(
            "EIA_API_KEY is required for "
            "cloud ingestion."
        )

    start, end = _plan_window(
        settings=settings
    )

    logger.info(
        "Starting cloud EIA ingestion: %s -> %s",
        start,
        end,
    )

    client = EIAClient(
        api_key=settings.eia_api_key,
        base_url=settings.eia_base_url,
    )

    api_end = to_eia_inclusive_end(
        end
    )

    raw_frame = client.fetch_region_data(
        respondent="PJM",
        data_type="D",
        start=_eia_timestamp(start),
        end=_eia_timestamp(api_end),
    )

    logger.info(
        "EIA returned %s raw rows",
        len(raw_frame),
    )

    # Preserve source truth in S3 before
    # validation / serving filtering.
    s3_key = build_raw_eia_key(
        respondent="PJM",
        start=start,
        end=end,
    )

    upload_eia_frame(
        raw_frame,
        bucket=settings.s3_raw_bucket,
        key=s3_key,
        profile_name=settings.aws_profile,
        region_name=settings.aws_region,
    )

    validated_frame, report = (
        validate_eia_demand(
            raw_frame,
            expected_respondent="PJM",
        )
    )

    usable = validated_frame[
        validated_frame["value"].notna()
    ].copy()

    rows: list[
        tuple[datetime, float]
    ] = []

    for _, row in usable.iterrows():
        period = row["period"]

        if hasattr(
            period,
            "to_pydatetime",
        ):
            period = (
                period.to_pydatetime()
            )

        rows.append(
            (
                period,
                float(row["value"]),
            )
        )

    written = write_demand_rows(
        rows,
        table_name=(
            settings.dynamodb_demand_table
        ),
        profile_name=settings.aws_profile,
        region_name=settings.aws_region,
        respondent="PJM",
    )

    warnings = list(
        report.warnings
    ) if report.has_warnings else []

    logger.info(
        "Cloud EIA ingestion complete: "
        "%s raw rows, %s DynamoDB rows, "
        "S3 key=%s",
        len(raw_frame),
        written,
        s3_key,
    )

    return {
        "status": "ok",
        "start": start.isoformat(),
        "end": end.isoformat(),
        "raw_rows": len(raw_frame),
        "dynamodb_rows": written,
        "s3_key": s3_key,
        "warnings": warnings,
    }