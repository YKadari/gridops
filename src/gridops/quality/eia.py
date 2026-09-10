from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {
    "period",
    "respondent",
    "respondent-name",
    "type",
    "type-name",
    "value",
    "value-units",
}

UNIQUE_KEY = ["period", "respondent", "type"]


class DataQualityError(ValueError):
    """Raised when incoming EIA data violates the GridOps data contract."""


def validate_eia_demand(
    frame: pd.DataFrame,
    *,
    expected_respondent: str = "PJM",
) -> pd.DataFrame:
    """
    Validate hourly EIA demand data.

    Returns a cleaned and chronologically sorted DataFrame when all checks pass.
    Raises DataQualityError if the incoming data violates the contract.
    """

    if frame.empty:
        raise DataQualityError("EIA dataset is empty.")

    missing_columns = REQUIRED_COLUMNS - set(frame.columns)

    if missing_columns:
        raise DataQualityError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    validated = frame.copy()

    # Convert fields to the types GridOps expects.
    validated["period"] = pd.to_datetime(
        validated["period"],
        utc=True,
        errors="coerce",
    )

    validated["value"] = pd.to_numeric(
        validated["value"],
        errors="coerce",
    )

    errors: list[str] = []

    # Required fields cannot be null.
    null_counts = validated[list(REQUIRED_COLUMNS)].isna().sum()
    columns_with_nulls = null_counts[null_counts > 0]

    if not columns_with_nulls.empty:
        errors.append(
            "Null values detected: "
            + ", ".join(
                f"{column}={count}"
                for column, count in columns_with_nulls.items()
            )
        )

    # We requested one specific balancing authority.
    unexpected_respondents = set(
        validated["respondent"].dropna().unique()
    ) - {expected_respondent}

    if unexpected_respondents:
        errors.append(
            f"Unexpected respondents: {sorted(unexpected_respondents)}"
        )

    # D is EIA's identifier for demand.
    unexpected_types = set(
        validated["type"].dropna().unique()
    ) - {"D"}

    if unexpected_types:
        errors.append(
            f"Unexpected data types: {sorted(unexpected_types)}"
        )

    # Protect the modeling layer from impossible/suspicious values.
    negative_values = (validated["value"] < 0).sum()

    if negative_values:
        errors.append(
            f"Found {negative_values} negative demand values."
        )

    # One observation per authority, metric and hour.
    duplicate_count = validated.duplicated(
        subset=UNIQUE_KEY,
        keep=False,
    ).sum()

    if duplicate_count:
        errors.append(
            f"Found {duplicate_count} rows involved in duplicate keys."
        )

    # Since EIA timestamps are UTC, DST does not create 23/25-hour days.
    periods = (
        validated["period"]
        .dropna()
        .drop_duplicates()
        .sort_values()
    )

    if len(periods) > 1:
        differences = periods.diff().dropna()

        bad_gaps = differences[
            differences.dt.total_seconds() != 3600
        ]

        if not bad_gaps.empty:
            errors.append(
                f"Found {len(bad_gaps)} non-hourly gaps in the time series."
            )

    if errors:
        raise DataQualityError(
            "EIA data failed validation:\n- " + "\n- ".join(errors)
        )

    return (
        validated
        .sort_values("period")
        .reset_index(drop=True)
    )