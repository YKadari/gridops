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


LATEST_AVAILABLE_COLUMNS = {
    24: "demand_lag_26h",
    48: "demand_lag_50h",
}


def evaluate_horizon(
    *,
    horizon_hours: int,
    dsn: str,
) -> None:

    frame = load_feature_mart(
        dsn=dsn,
        horizon_hours=horizon_hours,
    )

    frame = add_time_split(frame)

    print()
    print(
        f"========== {horizon_hours}H FORECAST =========="
    )

    print()
    print("Dataset split sizes:")

    print(
        frame["split"]
        .value_counts()
        .reindex(
            [
                "train",
                "validation",
                "test",
            ]
        )
    )

    latest_column = (
        LATEST_AVAILABLE_COLUMNS[
            horizon_hours
        ]
    )

    baselines = {
        "latest_available": latest_column,

        "weekly_persistence":
            "demand_lag_168h",

        "recent_24h_average":
            "demand_rolling_mean_24h",
    }

    results = []

    # Do NOT evaluate the test set yet.
    for split in [
        "train",
        "validation",
    ]:
        split_frame = frame[
            frame["split"] == split
        ]

        for (
            baseline_name,
            prediction_column,
        ) in baselines.items():

            metrics = (
                calculate_forecast_metrics(
                    split_frame[
                        "target_demand"
                    ],
                    split_frame[
                        prediction_column
                    ],
                )
            )

            results.append(
                {
                    "horizon":
                        horizon_hours,
                    "split":
                        split,
                    "baseline":
                        baseline_name,
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
                }
            )

    results_frame = pd.DataFrame(
        results
    )

    print()
    print("Baseline performance:")
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
        "NOTE: Test-set performance "
        "remains intentionally hidden."
    )


def main() -> None:
    settings = Settings()

    for horizon in [
        24,
        48,
    ]:
        evaluate_horizon(
            horizon_hours=horizon,
            dsn=settings.postgres_dsn,
        )


if __name__ == "__main__":
    main()