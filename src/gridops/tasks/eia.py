from __future__ import annotations

from datetime import datetime

import pandas as pd
from prefect import task
from prefect.logging import get_run_logger

from gridops.config import Settings
from gridops.database.postgres import initialize_database, load_eia_data
from gridops.ingestion.backfill import to_eia_inclusive_end
from gridops.ingestion.eia import EIAClient
from gridops.quality.eia import validate_eia_demand
from gridops.database.postgres import (
    get_latest_eia_period,
    initialize_database,
    load_eia_data,
)
from gridops.ingestion.incremental import plan_incremental_window

def eia_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H")


@task(
    name="extract-eia-demand",
    retries=1,
    retry_delay_seconds=15,
)
def extract_eia_demand(
    start: datetime,
    end: datetime,
    respondent: str = "PJM",
) -> pd.DataFrame:
    logger = get_run_logger()
    settings = Settings()

    logger.info(
        "Extracting %s demand data from %s to %s",
        respondent,
        start,
        end,
    )

    client = EIAClient(
        api_key=settings.eia_api_key,
        base_url=settings.eia_base_url,
    )

    api_end = to_eia_inclusive_end(end)

    frame = client.fetch_region_data(
        respondent=respondent,
        data_type="D",
        start=eia_timestamp(start),
        end=eia_timestamp(api_end),
    )

    logger.info(
        "EIA extraction returned %s rows",
        len(frame),
    )

    return frame


@task(name="validate-eia-demand")
def validate_eia_demand_task(
    frame: pd.DataFrame,
    respondent: str = "PJM",
) -> pd.DataFrame:
    logger = get_run_logger()

    validated, report = validate_eia_demand(
        frame,
        expected_respondent=respondent,
    )

    logger.info(
        "Validated %s EIA records",
        len(validated),
    )

    if report.has_warnings:
        for warning in report.warnings:
            logger.warning(
                "Data quality warning: %s",
                warning,
            )
    else:
        logger.info(
            "No source data quality warnings detected"
        )

    return validated


@task(
    name="load-eia-postgres",
    retries=2,
    retry_delay_seconds=10,
)
def load_eia_postgres(
    frame: pd.DataFrame,
) -> int:
    logger = get_run_logger()
    settings = Settings()

    initialize_database(
        settings.postgres_dsn
    )

    loaded = load_eia_data(
        frame,
        dsn=settings.postgres_dsn,
    )

    logger.info(
        "Loaded %s records into PostgreSQL",
        loaded,
    )

    return loaded

@task(name="plan-eia-incremental-window")
def plan_eia_incremental_window_task(
    respondent: str = "PJM",
) -> tuple[datetime, datetime]:
    logger = get_run_logger()
    settings = Settings()

    latest_period = get_latest_eia_period(
        settings.postgres_dsn,
        respondent=respondent,
        data_type="D",
    )

    start, end = plan_incremental_window(
        latest_period
    )

    logger.info(
        "Latest stored %s observation: %s",
        respondent,
        latest_period,
    )

    logger.info(
        "Planned incremental ingestion window: %s -> %s",
        start,
        end,
    )

    return start, end