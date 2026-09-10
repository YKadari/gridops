from __future__ import annotations

from prefect import flow
from prefect.logging import get_run_logger

from gridops.flows.eia_pipeline import eia_ingestion_flow
from gridops.tasks.eia import plan_eia_incremental_window_task


@flow(name="gridops-eia-incremental")
def eia_incremental_flow(
    respondent: str = "PJM",
) -> int:
    logger = get_run_logger()

    logger.info(
        "Planning incremental GridOps ingestion"
    )

    start, end = plan_eia_incremental_window_task(
        respondent=respondent
    )

    loaded = eia_ingestion_flow(
        start=start,
        end=end,
        respondent=respondent,
    )

    logger.info(
        "Incremental GridOps pipeline processed %s rows",
        loaded,
    )

    return loaded