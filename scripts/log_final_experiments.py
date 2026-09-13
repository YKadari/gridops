from __future__ import annotations

from pathlib import Path

import mlflow
import pandas as pd


EXPERIMENT_NAME = "gridops-demand-forecasting"

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


def load_cv_metrics(
    horizon_hours: int,
) -> dict[str, float]:
    path = Path(
        f"artifacts/tuning/"
        f"xgboost_cv_summary_{horizon_hours}h.csv"
    )

    frame = pd.read_csv(path)

    champion = frame[
        frame["config_number"] == 6
    ].iloc[0]

    return {
        "cv_mean_wape_pct":
            float(champion["mean_wape_pct"]),
        "cv_std_wape_pct":
            float(champion["std_wape_pct"]),
        "cv_mean_mae":
            float(champion["mean_mae"]),
        "cv_mean_rmse":
            float(champion["mean_rmse"]),
    }


def main() -> None:
    final_metrics_path = Path(
        "artifacts/final_test/"
        "final_test_metrics.csv"
    )

    final_metrics = pd.read_csv(
        final_metrics_path
    )

    mlflow.set_experiment(
        EXPERIMENT_NAME
    )

    for horizon_hours in (24, 48):
        row = final_metrics[
            final_metrics["horizon_hours"]
            == horizon_hours
        ].iloc[0]

        cv_metrics = load_cv_metrics(
            horizon_hours
        )

        run_name = (
            f"xgboost-champion-"
            f"{horizon_hours}h-final"
        )

        with mlflow.start_run(
            run_name=run_name
        ) as run:

            mlflow.log_params(
                {
                    "algorithm": "xgboost",
                    "horizon_hours":
                        horizon_hours,
                    **CHAMPION_PARAMS,
                }
            )

            mlflow.log_metrics(
                {
                    "test_mae":
                        float(row["mae"]),

                    "test_rmse":
                        float(row["rmse"]),

                    "test_mape_pct":
                        float(row["mape_pct"]),

                    "test_wape_pct":
                        float(row["wape_pct"]),

                    "baseline_test_wape_pct":
                        float(
                            row[
                                "baseline_wape_pct"
                            ]
                        ),

                    "relative_wape_reduction_pct":
                        float(
                            row[
                                "relative_wape_reduction_pct"
                            ]
                        ),

                    **cv_metrics,
                }
            )

            mlflow.set_tags(
                {
                    "project": "GridOps",
                    "task":
                        "PJM demand forecasting",
                    "model_status":
                        "frozen_champion",
                    "test_period":
                        "2025-10-01_to_2025-12-31",
                    "test_set_reused_for_tuning":
                        "false",
                }
            )

            mlflow.log_artifact(
                str(
                    Path(
                        "artifacts/tuning/"
                        f"xgboost_cv_summary_"
                        f"{horizon_hours}h.csv"
                    )
                ),
                artifact_path="tuning",
            )

            mlflow.log_artifact(
                str(
                    Path(
                        "artifacts/tuning/"
                        f"xgboost_cv_folds_"
                        f"{horizon_hours}h.csv"
                    )
                ),
                artifact_path="tuning",
            )

            mlflow.log_artifact(
                str(
                    Path(
                        "artifacts/final_test/"
                        f"predictions_"
                        f"{horizon_hours}h.csv"
                    )
                ),
                artifact_path="final_test",
            )

            mlflow.log_artifact(
                str(final_metrics_path),
                artifact_path="final_test",
            )

            print(
                f"Logged {horizon_hours}h run:"
            )

            print(
                f"  Run ID: "
                f"{run.info.run_id}"
            )


if __name__ == "__main__":
    main()