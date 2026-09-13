from __future__ import annotations

import os

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd

from mlflow import MlflowClient
from mlflow.models import infer_signature

from gridops.config import Settings
from gridops.modeling.data import (
    load_feature_mart,
)
from gridops.modeling.models import (
    FEATURES_BY_HORIZON,
    build_xgboost_model,
)


EXPERIMENT_NAME = (
    "gridops-demand-forecasting"
)

TEST_START = pd.Timestamp(
    "2025-10-01T00:00:00Z"
)


CHAMPION_PARAMS = {
    "n_estimators": 700,
    "learning_rate": 0.05,
    "max_depth": 4,
    "min_child_weight": 5,
    "subsample": 0.9,
    "colsample_bytree": 0.9,
    "reg_lambda": 1.0,
    "reg_alpha": 0.0,
}


REGISTERED_MODEL_NAMES = {
    24: "gridops-demand-24h",
    48: "gridops-demand-48h",
}


def prepare_training_data(
    *,
    dsn: str,
    horizon_hours: int,
) -> tuple[pd.DataFrame, pd.Series]:

    frame = load_feature_mart(
        dsn=dsn,
        horizon_hours=horizon_hours,
    )

    features = FEATURES_BY_HORIZON[
        horizon_hours
    ]

    # Reproduce the exact training period used
    # for the frozen final-test evaluation.
    frame = frame[
        frame["target_at"] < TEST_START
    ].copy()

    frame = frame.dropna(
        subset=[
            "target_demand",
            *features,
        ]
    )

    X = frame[features]

    y = frame[
        "target_demand"
    ].astype(float)

    return X, y


def find_latest_final_run(
    *,
    client: MlflowClient,
    experiment_id: str,
    horizon_hours: int,
):

    run_name = (
        f"xgboost-champion-"
        f"{horizon_hours}h-final"
    )

    runs = client.search_runs(
        experiment_ids=[
            experiment_id
        ],
        filter_string=(
            "tags.mlflow.runName = "
            f"'{run_name}'"
        ),
        order_by=[
            "attributes.start_time DESC"
        ],
        max_results=1,
    )

    if not runs:
        raise RuntimeError(
            f"Could not find MLflow run "
            f"{run_name}"
        )

    return runs[0]


def register_horizon(
    *,
    settings: Settings,
    client: MlflowClient,
    experiment_id: str,
    horizon_hours: int,
) -> None:

    print()
    print("=" * 70)
    print(
        f"REGISTERING {horizon_hours}H CHAMPION"
    )
    print("=" * 70)

    X_train, y_train = (
        prepare_training_data(
            dsn=settings.postgres_dsn,
            horizon_hours=horizon_hours,
        )
    )

    print(
        f"Training rows: "
        f"{len(X_train):,}"
    )

    model = build_xgboost_model(
        horizon_hours=horizon_hours,
        params=CHAMPION_PARAMS,
    )

    model.fit(
        X_train,
        y_train,
    )

    input_example = (
        X_train.head(5).copy()
    )

    example_predictions = (
        model.predict(
            input_example
        )
    )

    signature = infer_signature(
        input_example,
        example_predictions,
    )

    run = find_latest_final_run(
        client=client,
        experiment_id=experiment_id,
        horizon_hours=horizon_hours,
    )

    run_id = run.info.run_id

    print(
        f"Using MLflow run: "
        f"{run_id}"
    )

    with mlflow.start_run(
        run_id=run_id
    ):

        mlflow.sklearn.log_model(
            sk_model=model,
            name="champion_model",
            signature=signature,
            input_example=input_example,
            skops_trusted_types=[
                "xgboost.core.Booster",
                "xgboost.sklearn.XGBRegressor",
            ]
        )

        mlflow.set_tag(
            "registered_model_candidate",
            "true",
        )

    model_uri = (
        f"runs:/{run_id}/champion_model"
    )

    registered_model_name = (
        REGISTERED_MODEL_NAMES[
            horizon_hours
        ]
    )

    model_version = (
        mlflow.register_model(
            model_uri=model_uri,
            name=registered_model_name,
        )
    )

    version = model_version.version

    client.set_registered_model_alias(
        name=registered_model_name,
        alias="champion",
        version=version,
    )

    client.set_model_version_tag(
        name=registered_model_name,
        version=version,
        key="horizon_hours",
        value=str(horizon_hours),
    )

    client.set_model_version_tag(
        name=registered_model_name,
        version=version,
        key="model_status",
        value="frozen_champion",
    )

    client.set_model_version_tag(
        name=registered_model_name,
        version=version,
        key="training_cutoff",
        value="2025-10-01",
    )

    print(
        f"Registered model: "
        f"{registered_model_name}"
    )

    print(
        f"Version: {version}"
    )

    print(
        "Alias: champion"
    )

    # ---------------------------------------
    # Verify registry loading actually works.
    # ---------------------------------------

    registry_uri = (
        f"models:/"
        f"{registered_model_name}"
        f"@champion"
    )

    loaded_model = (
        mlflow.sklearn.load_model(
            registry_uri
        )
    )

    registry_predictions = (
        loaded_model.predict(
            input_example
        )
    )

    maximum_difference = float(
        np.max(
            np.abs(
                example_predictions
                - registry_predictions
            )
        )
    )

    print(
        f"Registry reload max "
        f"prediction difference: "
        f"{maximum_difference:.10f}"
    )

    if not np.allclose(
        example_predictions,
        registry_predictions,
    ):
        raise RuntimeError(
            "Reloaded registry model does "
            "not reproduce predictions."
        )

    print(
        "✅ Registry reload verified."
    )


def main() -> None:

    tracking_uri = os.getenv(
        "MLFLOW_TRACKING_URI",
        "http://127.0.0.1:5000",
    )

    mlflow.set_tracking_uri(
        tracking_uri
    )

    print(
        f"MLflow tracking URI: "
        f"{mlflow.get_tracking_uri()}"
    )

    settings = Settings()

    experiment = (
        mlflow.get_experiment_by_name(
            EXPERIMENT_NAME
        )
    )

    if experiment is None:
        raise RuntimeError(
            f"Experiment "
            f"{EXPERIMENT_NAME} "
            f"does not exist."
        )

    client = MlflowClient()

    for horizon_hours in (
        24,
        48,
    ):
        register_horizon(
            settings=settings,
            client=client,
            experiment_id=(
                experiment.experiment_id
            ),
            horizon_hours=horizon_hours,
        )


if __name__ == "__main__":
    main()