from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class TimeFold:
    name: str
    train_end: pd.Timestamp
    validation_start: pd.Timestamp
    validation_end: pd.Timestamp


TIME_FOLDS = [
    TimeFold(
        name="fold_1",
        train_end=pd.Timestamp(
            "2024-10-01T00:00:00Z"
        ),
        validation_start=pd.Timestamp(
            "2024-10-01T00:00:00Z"
        ),
        validation_end=pd.Timestamp(
            "2025-01-01T00:00:00Z"
        ),
    ),
    TimeFold(
        name="fold_2",
        train_end=pd.Timestamp(
            "2025-01-01T00:00:00Z"
        ),
        validation_start=pd.Timestamp(
            "2025-01-01T00:00:00Z"
        ),
        validation_end=pd.Timestamp(
            "2025-04-01T00:00:00Z"
        ),
    ),
    TimeFold(
        name="fold_3",
        train_end=pd.Timestamp(
            "2025-04-01T00:00:00Z"
        ),
        validation_start=pd.Timestamp(
            "2025-04-01T00:00:00Z"
        ),
        validation_end=pd.Timestamp(
            "2025-07-01T00:00:00Z"
        ),
    ),
    TimeFold(
        name="fold_4",
        train_end=pd.Timestamp(
            "2025-07-01T00:00:00Z"
        ),
        validation_start=pd.Timestamp(
            "2025-07-01T00:00:00Z"
        ),
        validation_end=pd.Timestamp(
            "2025-10-01T00:00:00Z"
        ),
    ),
]


def get_fold_frames(
    frame: pd.DataFrame,
    *,
    fold: TimeFold,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    train = frame[
        frame["target_at"] < fold.train_end
    ].copy()

    validation = frame[
        (
            frame["target_at"]
            >= fold.validation_start
        )
        & (
            frame["target_at"]
            < fold.validation_end
        )
    ].copy()

    return train, validation