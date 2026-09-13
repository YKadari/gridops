from __future__ import annotations

import pandas as pd

from gridops.config import Settings
from gridops.modeling.data import (
    add_time_split,
    load_feature_mart,
)
from gridops.modeling.models import (
    FEATURES_BY_HORIZON,
    build_xgboost_model,
)


def prepare_split(
    frame: pd.DataFrame,
    *,
    horizon_hours: int,
    split: str,
) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:

    features = FEATURES_BY_HORIZON[horizon_hours]

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

    return X, y, subset


def analyze_horizon(
    *,
    horizon_hours: int,
    dsn: str,
) -> None:

    print()
    print("=" * 70)
    print(
        f"{horizon_hours}H XGBOOST ANALYSIS"
    )
    print("=" * 70)

    frame = load_feature_mart(
        dsn=dsn,
        horizon_hours=horizon_hours,
    )

    frame = add_time_split(frame)

    X_train, y_train, _ = prepare_split(
        frame,
        horizon_hours=horizon_hours,
        split="train",
    )

    X_validation, y_validation, validation = (
        prepare_split(
            frame,
            horizon_hours=horizon_hours,
            split="validation",
        )
    )

    model = build_xgboost_model(
        horizon_hours=horizon_hours
    )

    model.fit(
        X_train,
        y_train,
    )

    predictions = model.predict(
        X_validation
    )

    validation = validation.copy()

    validation["prediction"] = predictions

    validation["absolute_error"] = (
        validation["target_demand"]
        - validation["prediction"]
    ).abs()

    validation["absolute_pct_error"] = (
        validation["absolute_error"]
        / validation["target_demand"].abs()
        * 100
    )

    # -------------------------------------------------
    # Feature importance
    # -------------------------------------------------

    preprocessor = model.named_steps[
        "preprocessor"
    ]

    xgb_model = model.named_steps[
        "model"
    ]

    feature_names = (
        preprocessor.get_feature_names_out()
    )

    importance = pd.DataFrame(
        {
            "feature": feature_names,
            "importance":
                xgb_model.feature_importances_,
        }
    )

    importance = importance.sort_values(
        "importance",
        ascending=False,
    )

    print()
    print("Top 15 features:")
    print()

    print(
        importance.head(15).to_string(
            index=False,
            float_format=lambda x: f"{x:.4f}",
        )
    )

    # -------------------------------------------------
    # Error by target hour
    # -------------------------------------------------

    hourly_error = (
        validation
        .groupby("target_hour")
        ["absolute_pct_error"]
        .mean()
        .sort_index()
    )

    print()
    print("Mean absolute % error by target hour:")
    print()

    print(
        hourly_error.to_string(
            float_format=lambda x: f"{x:.3f}%"
        )
    )

    # -------------------------------------------------
    # Error by month
    # -------------------------------------------------

    monthly_error = (
        validation
        .groupby("target_month")
        ["absolute_pct_error"]
        .mean()
        .sort_index()
    )

    print()
    print("Mean absolute % error by month:")
    print()

    print(
        monthly_error.to_string(
            float_format=lambda x: f"{x:.3f}%"
        )
    )

    # -------------------------------------------------
    # Largest misses
    # -------------------------------------------------

    worst = validation[
        [
            "target_at",
            "target_demand",
            "prediction",
            "absolute_error",
            "absolute_pct_error",
        ]
    ].sort_values(
        "absolute_error",
        ascending=False,
    )

    print()
    print("10 largest validation misses:")
    print()

    print(
        worst.head(10).to_string(
            index=False,
            float_format=lambda x: f"{x:,.3f}",
        )
    )


def main() -> None:

    settings = Settings()

    for horizon in (24, 48):
        analyze_horizon(
            horizon_hours=horizon,
            dsn=settings.postgres_dsn,
        )


if __name__ == "__main__":
    main()