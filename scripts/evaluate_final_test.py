from __future__ import annotations

from pathlib import Path

import pandas as pd

from gridops.config import Settings
from gridops.modeling.data import load_feature_mart
from gridops.modeling.metrics import calculate_forecast_metrics
from gridops.modeling.models import (
    FEATURES_BY_HORIZON,
    build_xgboost_model,
)


TEST_START = pd.Timestamp(
    "2025-10-01T00:00:00Z"
)

TEST_END = pd.Timestamp(
    "2026-01-01T00:00:00Z"
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


BASELINE_COLUMNS = {
    24: "demand_lag_26h",
    48: "demand_lag_50h",
}


def prepare_frame(
    frame: pd.DataFrame,
    *,
    horizon_hours: int,
) -> pd.DataFrame:

    features = FEATURES_BY_HORIZON[
        horizon_hours
    ]

    return frame.dropna(
        subset=[
            "target_demand",
            *features,
        ]
    ).copy()


def evaluate_horizon(
    *,
    horizon_hours: int,
    dsn: str,
) -> dict:

    print()
    print("=" * 72)
    print(
        f"{horizon_hours}H FINAL TEST EVALUATION"
    )
    print("=" * 72)

    frame = load_feature_mart(
        dsn=dsn,
        horizon_hours=horizon_hours,
    )

    train_frame = frame[
        frame["target_at"] < TEST_START
    ].copy()

    test_frame = frame[
        (frame["target_at"] >= TEST_START)
        & (frame["target_at"] < TEST_END)
    ].copy()

    train_frame = prepare_frame(
        train_frame,
        horizon_hours=horizon_hours,
    )

    test_frame = prepare_frame(
        test_frame,
        horizon_hours=horizon_hours,
    )

    features = FEATURES_BY_HORIZON[
        horizon_hours
    ]

    X_train = train_frame[features]

    y_train = train_frame[
        "target_demand"
    ].astype(float)

    X_test = test_frame[features]

    y_test = test_frame[
        "target_demand"
    ].astype(float)

    print(
        f"Training rows: {len(X_train):,}"
    )

    print(
        f"Final test rows: {len(X_test):,}"
    )

    model = build_xgboost_model(
        horizon_hours=horizon_hours,
        params=CHAMPION_PARAMS,
    )

    print()
    print(
        "Training frozen champion model..."
    )

    model.fit(
        X_train,
        y_train,
    )

    predictions = pd.Series(
        model.predict(X_test),
        index=y_test.index,
    )

    champion_metrics = (
        calculate_forecast_metrics(
            y_test,
            predictions,
        )
    )

    baseline_predictions = (
        test_frame[
            BASELINE_COLUMNS[
                horizon_hours
            ]
        ].astype(float)
    )

    baseline_metrics = (
        calculate_forecast_metrics(
            y_test,
            baseline_predictions,
        )
    )

    print()
    print("FINAL TEST PERFORMANCE")
    print()

    print(
        f"MAE:  "
        f"{champion_metrics.mae:,.3f}"
    )

    print(
        f"RMSE: "
        f"{champion_metrics.rmse:,.3f}"
    )

    print(
        f"MAPE: "
        f"{champion_metrics.mape_pct:.3f}%"
    )

    print(
        f"WAPE: "
        f"{champion_metrics.wape_pct:.3f}%"
    )

    print()
    print(
        f"Baseline test WAPE: "
        f"{baseline_metrics.wape_pct:.3f}%"
    )

    relative_improvement = (
        (
            baseline_metrics.wape_pct
            - champion_metrics.wape_pct
        )
        / baseline_metrics.wape_pct
        * 100
    )

    print(
        f"Relative WAPE reduction: "
        f"{relative_improvement:.2f}%"
    )

    # Save predictions for later analysis,
    # dashboard metrics, and MLflow artifacts.
    output_dir = Path(
        "artifacts/final_test"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = pd.DataFrame(
        {
            "target_at":
                test_frame["target_at"],
            "actual_demand":
                y_test,
            "predicted_demand":
                predictions,
        }
    )

    output["absolute_error"] = (
        output["actual_demand"]
        - output["predicted_demand"]
    ).abs()

    output.to_csv(
        output_dir
        / (
            f"predictions_"
            f"{horizon_hours}h.csv"
        ),
        index=False,
    )

    return {
        "horizon_hours":
            horizon_hours,
        "test_rows":
            champion_metrics.n,
        "mae":
            champion_metrics.mae,
        "rmse":
            champion_metrics.rmse,
        "mape_pct":
            champion_metrics.mape_pct,
        "wape_pct":
            champion_metrics.wape_pct,
        "baseline_wape_pct":
            baseline_metrics.wape_pct,
        "relative_wape_reduction_pct":
            relative_improvement,
    }


def main() -> None:

    settings = Settings()

    results = []

    for horizon in (24, 48):
        results.append(
            evaluate_horizon(
                horizon_hours=horizon,
                dsn=settings.postgres_dsn,
            )
        )

    results_frame = pd.DataFrame(
        results
    )

    output_dir = Path(
        "artifacts/final_test"
    )

    results_frame.to_csv(
        output_dir
        / "final_test_metrics.csv",
        index=False,
    )

    print()
    print("=" * 72)
    print("GRIDOPS FINAL TEST SUMMARY")
    print("=" * 72)
    print()

    print(
        results_frame.to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.3f}"
            ),
        )
    )

    print()
    print(
        "FINAL TEST SET HAS NOW BEEN "
        "OPENED. DO NOT TUNE AGAINST "
        "THESE RESULTS."
    )


if __name__ == "__main__":
    main()