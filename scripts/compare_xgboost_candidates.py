from __future__ import annotations

import pandas as pd

from gridops.config import Settings
from gridops.modeling.cross_validation import (
    TIME_FOLDS,
    get_fold_frames,
)
from gridops.modeling.data import load_feature_mart
from gridops.modeling.metrics import calculate_forecast_metrics
from gridops.modeling.models import (
    FEATURES_BY_HORIZON,
    build_xgboost_model,
)


CANDIDATES = {
    "xgboost_v2": {
        "n_estimators": 500,
        "learning_rate": 0.05,
        "max_depth": 6,
        "min_child_weight": 5,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "reg_lambda": 1.0,
        "reg_alpha": 0.0,
    },

    "cv_winner": {
        "n_estimators": 700,
        "learning_rate": 0.05,
        "max_depth": 4,
        "min_child_weight": 5,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "reg_lambda": 1.0,
        "reg_alpha": 0.0,
    },
}


def prepare_xy(
    frame: pd.DataFrame,
    *,
    horizon_hours: int,
) -> tuple[pd.DataFrame, pd.Series]:

    features = FEATURES_BY_HORIZON[
        horizon_hours
    ]

    usable = frame.dropna(
        subset=[
            "target_demand",
            *features,
        ]
    ).copy()

    return (
        usable[features],
        usable["target_demand"].astype(float),
    )


def evaluate_horizon(
    *,
    horizon_hours: int,
    dsn: str,
) -> None:

    print()
    print("=" * 72)
    print(
        f"{horizon_hours}H FINAL CANDIDATE COMPARISON"
    )
    print("=" * 72)

    frame = load_feature_mart(
        dsn=dsn,
        horizon_hours=horizon_hours,
    )

    # Test set stays completely excluded.
    frame = frame[
        frame["target_at"]
        < pd.Timestamp(
            "2025-10-01T00:00:00Z"
        )
    ].copy()

    results = []

    for candidate_name, params in (
        CANDIDATES.items()
    ):

        print()
        print(candidate_name)

        for fold in TIME_FOLDS:

            train, validation = (
                get_fold_frames(
                    frame,
                    fold=fold,
                )
            )

            X_train, y_train = prepare_xy(
                train,
                horizon_hours=horizon_hours,
            )

            X_validation, y_validation = (
                prepare_xy(
                    validation,
                    horizon_hours=horizon_hours,
                )
            )

            model = build_xgboost_model(
                horizon_hours=horizon_hours,
                params=params,
            )

            model.fit(
                X_train,
                y_train,
            )

            predictions = pd.Series(
                model.predict(X_validation),
                index=y_validation.index,
            )

            metrics = calculate_forecast_metrics(
                y_validation,
                predictions,
            )

            results.append(
                {
                    "horizon":
                        horizon_hours,
                    "candidate":
                        candidate_name,
                    "fold":
                        fold.name,
                    "wape_pct":
                        metrics.wape_pct,
                    "mae":
                        metrics.mae,
                    "rmse":
                        metrics.rmse,
                }
            )

            print(
                f"  {fold.name}: "
                f"WAPE={metrics.wape_pct:.3f}%"
            )

    results = pd.DataFrame(results)

    summary = (
        results
        .groupby(
            "candidate",
            as_index=False,
        )
        .agg(
            mean_wape_pct=(
                "wape_pct",
                "mean",
            ),
            std_wape_pct=(
                "wape_pct",
                "std",
            ),
            mean_mae=(
                "mae",
                "mean",
            ),
            mean_rmse=(
                "rmse",
                "mean",
            ),
        )
        .sort_values(
            [
                "mean_wape_pct",
                "std_wape_pct",
            ]
        )
    )

    print()
    print("FINAL CANDIDATE SUMMARY")
    print()

    print(
        summary.to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.4f}"
            ),
        )
    )

    print()
    print(
        "TEST SET REMAINS LOCKED."
    )


def main() -> None:
    settings = Settings()

    for horizon in (24, 48):
        evaluate_horizon(
            horizon_hours=horizon,
            dsn=settings.postgres_dsn,
        )


if __name__ == "__main__":
    main()