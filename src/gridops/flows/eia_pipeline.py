from __future__ import annotations

from datetime import datetime

from prefect import flow
from prefect.logging import get_run_logger

from gridops.tasks.eia import (
    extract_eia_demand,
    load_eia_postgres,
    validate_eia_demand_task,
)


@flow(
    name="gridops-eia-ingestion",
    flow_run_name="pjm-demand-{start:%Y%m%dT%H}-{end:%Y%m%dT%H}",
)
def eia_ingestion_flow(
    start: datetime,
    end: datetime,
    respondent: str = "PJM",
) -> int:
    logger = get_run_logger()

    logger.info(
        "Starting GridOps EIA ingestion pipeline"
    )

    raw_frame = extract_eia_demand(
        start=start,
        end=end,
        respondent=respondent,
    )

    validated_frame = validate_eia_demand_task(
        raw_frame,
        respondent=respondent,
    )

    loaded = load_eia_postgres(
        validated_frame
    )

    logger.info(
        "GridOps ingestion complete: %s rows processed",
        loaded,
    )

    return loaded