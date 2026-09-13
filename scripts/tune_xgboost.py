from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import ParameterGrid

from gridops.config import Settings
from gridops.modeling.cross_validation import (
    TIME_FOLDS,
    get_fold_frames,
)
from gridops.modeling.data import (
    load_feature_mart,
)
from gridops.modeling.metrics import (
    calculate_forecast_metrics,
)
from gridops.modeling.models import (
    FEATURES_BY_HORIZON,
    build_xgboost_model,
)


PARAMETER_GRID = {
    "n_estimators": [
        400,
        700,
    ],
    "learning_rate": [
        0.03,
        0.05,
    ],
    "max_depth": [
        4,
        6,
    ],
    "min_child_weight": [
        5,
    ],
    "subsample": [
        0.9,
    ],
    "colsample_bytree": [
        0.9,
    ],
    "reg_lambda": [
        1.0,
    ],
    "reg_alpha": [
        0.0,
    ],
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

    X = usable[features]

    y = usable[
        "target_demand"
    ].astype(float)

    return X, y


def tune_horizon(
    *,
    horizon_hours: int,
    dsn: str,
) -> None:

    print()
    print("=" * 75)
    print(
        f"{horizon_hours}H XGBOOST "
        f"TIME-SERIES TUNING"
    )
    print("=" * 75)

    frame = load_feature_mart(
        dsn=dsn,
        horizon_hours=horizon_hours,
    )

    # Absolutely exclude the locked test period.
    frame = frame[
        frame["target_at"]
        < pd.Timestamp(
            "2025-10-01T00:00:00Z"
        )
    ].copy()

    parameter_sets = list(
        ParameterGrid(
            PARAMETER_GRID
        )
    )

    print(
        f"Parameter configurations: "
        f"{len(parameter_sets)}"
    )

    print(
        f"Time folds: "
        f"{len(TIME_FOLDS)}"
    )

    print(
        f"Total model fits: "
        f"{len(parameter_sets) * len(TIME_FOLDS)}"
    )

    all_results = []

    for config_number, params in enumerate(
        parameter_sets,
        start=1,
    ):

        print()
        print(
            f"Configuration "
            f"{config_number}/"
            f"{len(parameter_sets)}"
        )

        print(params)

        fold_wapes = []

        for fold in TIME_FOLDS:

            train_frame, validation_frame = (
                get_fold_frames(
                    frame,
                    fold=fold,
                )
            )

            X_train, y_train = prepare_xy(
                train_frame,
                horizon_hours=horizon_hours,
            )

            X_validation, y_validation = (
                prepare_xy(
                    validation_frame,
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

            predictions = model.predict(
                X_validation
            )

            predictions = pd.Series(
                predictions,
                index=y_validation.index,
            )

            metrics = (
                calculate_forecast_metrics(
                    y_validation,
                    predictions,
                )
            )

            fold_wapes.append(
                metrics.wape_pct
            )

            all_results.append(
                {
                    "horizon":
                        horizon_hours,
                    "config_number":
                        config_number,
                    "fold":
                        fold.name,

                    **params,

                    "train_rows":
                        len(X_train),
                    "validation_rows":
                        len(X_validation),

                    "mae":
                        metrics.mae,
                    "rmse":
                        metrics.rmse,
                    "mape_pct":
                        metrics.mape_pct,
                    "wape_pct":
                        metrics.wape_pct,
                }
            )

            print(
                f"  {fold.name}: "
                f"WAPE="
                f"{metrics.wape_pct:.3f}%"
            )

        print(
            f"  Average WAPE: "
            f"{sum(fold_wapes) / len(fold_wapes):.3f}%"
        )

    results = pd.DataFrame(
        all_results
    )

    parameter_columns = [
        "n_estimators",
        "learning_rate",
        "max_depth",
        "min_child_weight",
        "subsample",
        "colsample_bytree",
        "reg_lambda",
        "reg_alpha",
    ]

    summary = (
        results
        .groupby(
            [
                "config_number",
                *parameter_columns,
            ],
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
        .reset_index(
            drop=True
        )
    )

    print()
    print(
        "TOP CONFIGURATIONS"
    )
    print()

    print(
        summary.head(10).to_string(
            index=False,
            float_format=lambda x: (
                f"{x:,.4f}"
            ),
        )
    )

    output_dir = Path(
        "artifacts/tuning"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(
        output_dir
        / (
            f"xgboost_cv_folds_"
            f"{horizon_hours}h.csv"
        ),
        index=False,
    )

    summary.to_csv(
        output_dir
        / (
            f"xgboost_cv_summary_"
            f"{horizon_hours}h.csv"
        ),
        index=False,
    )

    print()
    print(
        f"Saved tuning results to "
        f"{output_dir}"
    )

    print()
    print(
        "TEST SET REMAINS LOCKED."
    )


def main() -> None:

    settings = Settings()

    for horizon in (
        24,
        48,
    ):
        tune_horizon(
            horizon_hours=horizon,
            dsn=settings.postgres_dsn,
        )


if __name__ == "__main__":
    main()