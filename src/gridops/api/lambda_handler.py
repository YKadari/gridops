from __future__ import annotations

import logging

from fastapi import HTTPException
from mangum import Mangum

from gridops.api.main import (
    app,
    model_service,
    run_live_forecast,
    settings,
)
from gridops.storage.forecast_history import (
    write_forecast,
)


logger = logging.getLogger()
logger.setLevel(logging.INFO)


mangum_handler = Mangum(
    app
)


def _is_scheduled_event(
    event: dict,
) -> bool:
    return (
        event.get("source")
        == "aws.events"
        and event.get("detail-type")
        == "Scheduled Event"
    )


def _run_scheduled_forecasts() -> dict:
    # EventBridge invocations do not pass
    # through FastAPI's lifespan startup,
    # so ensure the champion models exist.
    if not model_service.is_ready():
        model_service.load_models()

    forecasts = []

    for horizon_hours in (
        24,
        48,
    ):
        try:
            forecast = run_live_forecast(
                horizon_hours=horizon_hours
            )

        except HTTPException as exc:
            if exc.status_code == 503:
                logger.warning(
                    "Skipping scheduled forecasts "
                    "because serving data is stale: %s",
                    exc.detail,
                )

                return {
                    "status": "skipped",
                    "reason": "stale_demand_data",
                    "detail": exc.detail,
                }

            raise

        write_forecast(
            table_name=(
                settings.forecast_history_table
            ),
            profile_name=(
                settings.aws_profile
            ),
            region_name=(
                settings.aws_region
            ),
            horizon_hours=(
                forecast.horizon_hours
            ),
            issue_at=(
                forecast.issue_at
            ),
            target_at=(
                forecast.target_at
            ),
            predicted_demand=(
                forecast.predicted_demand
            ),
            units=(
                forecast.units
            ),
            eia_latest_observed_at=(
                forecast.eia_latest_observed_at
            ),
        )

        forecasts.append(
            forecast.model_dump(
                mode="json"
            )
        )

        logger.info(
            "Stored %sh forecast for "
            "issue_at=%s target_at=%s",
            horizon_hours,
            forecast.issue_at,
            forecast.target_at,
        )

    return {
        "status": "ok",
        "forecasts": forecasts,
    }


def handler(
    event,
    context,
):
    if _is_scheduled_event(event):
        return _run_scheduled_forecasts()

    return mangum_handler(
        event,
        context,
    )