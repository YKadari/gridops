from __future__ import annotations

import pandas as pd

from gridops.config import Settings

from gridops.modeling.data import (
    add_time_split,
    load_feature_mart,
)

from gridops.modeling.metrics import (
    calculate_forecast_metrics,
)

from gridops.modeling.models import (
    FEATURES_BY_HORIZON,
    build_linear_model,
    build_ridge_model,
)


BASELINE_WAPE = {
    24: 7.581,
    48: 9.181,
}


def prepare_split(
    frame: pd.DataFrame,
    *,
    horizon_hours: int,
    split: str,
) -> tuple[pd.DataFrame, pd.Series]:

    features = FEATURES_BY_HORIZON[
        horizon_hours
    ]

    subset = frame[
        frame["split"] == split
    ].copy()

    required_columns = [
        "target_demand",
        *features,
    ]

    before = len(subset)

    subset = subset.dropna(
        subset=required_columns
    )

    dropped = before - len(subset)

    print(
        f"{split}: "
        f"{len(subset):,} usable rows "
        f"({dropped:,} dropped)"
    )

    X = subset[features]
    y = subset["target_demand"].astype(
        float
    )

    return X, y


def evaluate_horizon(
    *,
    horizon_hours: int,
    dsn: str,
) -> None:

    print()
    print(
        "=" * 70
    )

    print(
        f"{horizon_hours}H FORECAST MODELS"
    )

    print(
        "=" * 70
    )

    frame = load_feature_mart(
        dsn=dsn,
        horizon_hours=horizon_hours,
    )

    frame = add_time_split(
        frame
    )

    X_train, y_train = prepare_split(
        frame,
        horizon_hours=horizon_hours,
        split="train",
    )

    X_validation, y_validation = (
        prepare_split(
            frame,
            horizon_hours=horizon_hours,
            split="validation",
        )
    )

    models = {
        "linear_regression":
            build_linear_model(
                horizon_hours=horizon_hours
            ),

        "ridge_regression":
            build_ridge_model(
                horizon_hours=horizon_hours
            ),
    }

    results = []

    for model_name, model in models.items():

        print()
        print(
            f"Training {model_name}..."
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

        results.append(
            {
                "horizon":
                    horizon_hours,

                "model":
                    model_name,

                "n":
                    metrics.n,

                "mae":
                    metrics.mae,

                "rmse":
                    metrics.rmse,

                "mape_pct":
                    metrics.mape_pct,

                "wape_pct":
                    metrics.wape_pct,

                "baseline_wape_pct":
                    BASELINE_WAPE[
                        horizon_hours
                    ],

                "wape_improvement_pct_points":
                    (
                        BASELINE_WAPE[
                            horizon_hours
                        ]
                        - metrics.wape_pct
                    ),
            }
        )

        if model_name == "ridge_regression":

            alpha = (
                model
                .named_steps["model"]
                .alpha_
            )

            print(
                f"Selected Ridge alpha: "
                f"{alpha:.6f}"
            )

    results_frame = pd.DataFrame(
        results
    )

    print()
    print("Validation performance:")
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
        "TEST SET REMAINS LOCKED."
    )


def main() -> None:

    settings = Settings()

    for horizon in (
        24,
        48,
    ):
        evaluate_horizon(
            horizon_hours=horizon,
            dsn=settings.postgres_dsn,
        )


if __name__ == "__main__":
    main()