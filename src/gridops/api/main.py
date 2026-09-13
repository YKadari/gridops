from __future__ import annotations

from contextlib import asynccontextmanager
import os

import mlflow
from fastapi import FastAPI, HTTPException

from gridops.api.model_service import (
    ModelService,
)
from gridops.api.schemas import (
    PredictionRequest24h,
    PredictionRequest48h,
    PredictionResponse,
)


model_service = ModelService()


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    tracking_uri = os.getenv(
        "MLFLOW_TRACKING_URI",
        "http://127.0.0.1:5000",
    )

    mlflow.set_tracking_uri(
        tracking_uri
    )

    model_service.load_models()

    yield


app = FastAPI(
    title="GridOps Forecasting API",
    description=(
        "PJM electricity-demand forecasting "
        "service backed by MLflow champion models."
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