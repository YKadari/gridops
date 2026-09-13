from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ForecastMetrics:
    n: int
    mae: float
    rmse: float
    mape_pct: float
    wape_pct: float


def calculate_forecast_metrics(
    actual: pd.Series,
    predicted: pd.Series,
) -> ForecastMetrics:

    valid = actual.notna() & predicted.notna()

    y_true = (
        actual.loc[valid]
        .astype(float)
        .to_numpy()
    )

    y_pred = (
        predicted.loc[valid]
        .astype(float)
        .to_numpy()
    )

    if len(y_true) == 0:
        raise ValueError(
            "No valid observations available "
            "for metric calculation."
        )

    errors = y_true - y_pred

    absolute_errors = np.abs(errors)

    mae = float(
        np.mean(absolute_errors)
    )

    rmse = float(
        np.sqrt(
            np.mean(
                errors ** 2
            )
        )
    )

    nonzero = y_true != 0

    if nonzero.any():
        mape_pct = float(
            np.mean(
                absolute_errors[nonzero]
                / np.abs(y_true[nonzero])
            )
            * 100
        )
    else:
        mape_pct = float("nan")

    denominator = np.sum(
        np.abs(y_true)
    )

    if denominator == 0:
        wape_pct = float("nan")
    else:
        wape_pct = float(
            np.sum(absolute_errors)
            / denominator
            * 100
        )

    return ForecastMetrics(
        n=len(y_true),
        mae=mae,
        rmse=rmse,
        mape_pct=mape_pct,
        wape_pct=wape_pct,
    )