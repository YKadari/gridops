
from prefect import flow,task
from prefect.logging import get_run_logger

from gridops.flows.eia_pipeline import eia_ingestion_flow
from gridops.tasks.eia import plan_eia_incremental_window_task
from gridops.database.monitoring import (
    record_eia_freshness,
)
from gridops.config import Settings



@task(name="record-eia-source-freshness")
def record_freshness_task(
    *,
    dsn: str,
) -> None:
    result = record_eia_freshness(
        dsn=dsn,
        expected_lag_hours=2.0,
    )

    print(
        "EIA freshness | "
        f"latest={result['latest_observed_at']} | "
        f"lag={result['source_lag_hours']:.2f}h | "
        f"gap={result['freshness_gap_hours']:+.2f}h"
    )

@flow(name="gridops-eia-incremental")
def eia_incremental_flow(
    respondent: str = "PJM",
) -> int:
    logger = get_run_logger()
    settings = Settings()

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

    record_freshness_task(
        dsn=settings.postgres_dsn,
    )

    return loaded