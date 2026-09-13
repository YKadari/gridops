from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException

from gridops.api.model_service import (
    ModelService,
)
from gridops.api.schemas import (
    LiveForecastResponse,
    PredictionRequest24h,
    PredictionRequest48h,
    PredictionResponse,
)
from gridops.config import Settings
from gridops.database.monitoring import (
    get_eia_freshness_status,
)
from gridops.inference.features import (
    build_inference_features,
)


settings = Settings()

model_service = ModelService(
    bucket=settings.s3_raw_bucket,
    profile_name=settings.aws_profile,
    region_name=settings.aws_region,
)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    model_service.load_models()

    yield

app = FastAPI(
    title="GridOps Forecasting API",
    description=(
        "PJM electricity-demand forecasting "
        "service backed by production champion models."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
def root() -> dict:
    return {
        "service": "GridOps Forecasting API",
        "status": "running",
    }


@app.get("/health")
def health() -> dict:

    if not model_service.is_ready():
        raise HTTPException(
            status_code=503,
            detail="Forecast models are not ready.",
        )

    return {
        "status": "healthy",
        "models_loaded": [
            "24h",
            "48h",
        ],
    }


@app.post(
    "/predict/24h",
    response_model=PredictionResponse,
)
def predict_24h(
    request: PredictionRequest24h,
) -> PredictionResponse:

    prediction = model_service.predict(
        horizon_hours=24,
        features=request.model_dump(),
    )

    return PredictionResponse(
        horizon_hours=24,
        predicted_demand=prediction,
    )


@app.post(
    "/predict/48h",
    response_model=PredictionResponse,
)
def predict_48h(
    request: PredictionRequest48h,
) -> PredictionResponse:

    prediction = model_service.predict(
        horizon_hours=48,
        features=request.model_dump(),
    )

    return PredictionResponse(
        horizon_hours=48,
        predicted_demand=prediction,
    )

def run_live_forecast(
    *,
    horizon_hours: int,
) -> LiveForecastResponse:

    now = datetime.now(
        timezone.utc
    )

    freshness = (
        get_eia_freshness_status(
            dsn=settings.postgres_dsn,
            expected_lag_hours=2.0,
            checked_at=now,
        )
    )

    if not freshness["is_fresh"]:
        raise HTTPException(
            status_code=503,
            detail={
                "message":
                    "EIA demand data is too stale "
                    "for a safe forecast.",

                "latest_observed_at":
                    freshness[
                        "latest_observed_at"
                    ].isoformat(),

                "required_latest_at":
                    freshness[
                        "required_latest_at"
                    ].isoformat(),

                "source_lag_hours":
                    freshness[
                        "source_lag_hours"
                    ],

                "expected_lag_hours":
                    freshness[
                        "expected_lag_hours"
                    ],
            },
        )

    (
        features,
        issue_at,
        target_at,
    ) = build_inference_features(
        dsn=settings.postgres_dsn,
        horizon_hours=horizon_hours,
        now=now,
    )

    prediction = model_service.predict(
        horizon_hours=horizon_hours,
        features=features,
    )

    return LiveForecastResponse(
        horizon_hours=horizon_hours,
        issue_at=issue_at,
        target_at=target_at,
        predicted_demand=prediction,
        eia_latest_observed_at=(
            freshness[
                "latest_observed_at"
            ]
        ),
    )


@app.post(
    "/forecast/24h",
    response_model=LiveForecastResponse,
)
def forecast_24h() -> LiveForecastResponse:
    return run_live_forecast(
        horizon_hours=24
    )


@app.post(
    "/forecast/48h",
    response_model=LiveForecastResponse,
)
def forecast_48h() -> LiveForecastResponse:
    return run_live_forecast(
        horizon_hours=48
    )