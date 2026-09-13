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
    build_xgboost_model,
)


LINEAR_WAPE = {
    24: 3.584,
    48: 3.652,
}


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

    subset = subset.dropna(
        subset=[
            "target_demand",
            *features,
        ]
    )

    X = subset[features]

    y = subset[
        "target_demand"
    ].astype(float)

    return X, y


def evaluate_horizon(
    *,
    horizon_hours: int,
    dsn: str,
) -> None:

    print()
    print("=" * 70)
    print(
        f"{horizon_hours}H XGBOOST"
    )
    print("=" * 70)

    frame = load_feature_mart(
        dsn=dsn,
        horizon_hours=horizon_hours,
    )

    frame = add_time_split(frame)

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

    print(
        f"Training rows: "
        f"{len(X_train):,}"
    )

    print(
        f"Validation rows: "
        f"{len(X_validation):,}"
    )

    model = build_xgboost_model(
        horizon_hours=horizon_hours
    )

    print()
    print("Training XGBoost...")

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

    metrics = calculate_forecast_metrics(
        y_validation,
        predictions,
    )

    print()
    print("Validation performance:")
    print()

    print(
        f"MAE:  "
        f"{metrics.mae:,.3f}"
    )

    print(
        f"RMSE: "
        f"{metrics.rmse:,.3f}"
    )

    print(
        f"MAPE: "
        f"{metrics.mape_pct:.3f}%"
    )

    print(
        f"WAPE: "
        f"{metrics.wape_pct:.3f}%"
    )

    print()
    print(
        f"Simple baseline WAPE: "
        f"{BASELINE_WAPE[horizon_hours]:.3f}%"
    )

    print(
        f"Linear model WAPE:   "
        f"{LINEAR_WAPE[horizon_hours]:.3f}%"
    )

    print(
        f"XGBoost WAPE:        "
        f"{metrics.wape_pct:.3f}%"
    )

    improvement = (
        LINEAR_WAPE[horizon_hours]
        - metrics.wape_pct
    )

    print()
    print(
        "Improvement vs Linear: "
        f"{improvement:+.3f} "
        "percentage points"
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