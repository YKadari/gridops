from __future__ import annotations

from dataclasses import dataclass, field

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

REQUIRED_NON_NULL_COLUMNS = {
    "period",
    "respondent",
    "respondent-name",
    "type",
    "type-name",
    "value-units",
}

UNIQUE_KEY = ["period", "respondent", "type"]


class DataQualityError(ValueError):
    """Raised when EIA data violates a fatal GridOps data contract rule."""


@dataclass
class DataQualityReport:
    warnings: list[str] = field(default_factory=list)
    missing_value_count: int = 0
    non_hourly_gap_count: int = 0

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)


def validate_eia_demand(
    frame: pd.DataFrame,
    *,
    expected_respondent: str = "PJM",
) -> tuple[pd.DataFrame, DataQualityReport]:
    """
    Validate hourly EIA demand data.

    Fatal problems raise DataQualityError.

    Source-level incompleteness, such as missing demand values or
    missing hours, is preserved in the raw data and recorded as a
    quality warning.
    """

    if frame.empty:
        raise DataQualityError("EIA dataset is empty.")

    missing_columns = REQUIRED_COLUMNS - set(frame.columns)

    if missing_columns:
        raise DataQualityError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    validated = frame.copy()
    report = DataQualityReport()
    errors: list[str] = []

    # Preserve which values were genuinely missing at the source.
    original_value = validated["value"].copy()

    validated["period"] = pd.to_datetime(
        validated["period"],
        utc=True,
        errors="coerce",
    )

    validated["value"] = pd.to_numeric(
        validated["value"],
        errors="coerce",
    )

    # Required metadata cannot be null.
    null_counts = validated[
        list(REQUIRED_NON_NULL_COLUMNS)
    ].isna().sum()

    columns_with_nulls = null_counts[null_counts > 0]

    if not columns_with_nulls.empty:
        errors.append(
            "Null values detected in required fields: "
            + ", ".join(
                f"{column}={count}"
                for column, count in columns_with_nulls.items()
            )
        )

    # Distinguish malformed numeric values from genuinely missing values.
    invalid_numeric = (
        original_value.notna()
        & validated["value"].isna()
    ).sum()

    if invalid_numeric:
        errors.append(
            f"Found {invalid_numeric} non-numeric demand values."
        )

    unexpected_respondents = set(
        validated["respondent"].dropna().unique()
    ) - {expected_respondent}

    if unexpected_respondents:
        errors.append(
            f"Unexpected respondents: {sorted(unexpected_respondents)}"
        )

    unexpected_types = set(
        validated["type"].dropna().unique()
    ) - {"D"}

    if unexpected_types:
        errors.append(
            f"Unexpected data types: {sorted(unexpected_types)}"
        )

    negative_values = (validated["value"] < 0).sum()

    if negative_values:
        errors.append(
            f"Found {negative_values} negative demand values."
        )

    duplicate_count = validated.duplicated(
        subset=UNIQUE_KEY,
        keep=False,
    ).sum()

    if duplicate_count:
        errors.append(
            f"Found {duplicate_count} rows involved in duplicate keys."
        )

    # Missing demand values are source-quality warnings, not fatal.
    report.missing_value_count = int(
        validated["value"].isna().sum()
    )

    if report.missing_value_count:
        report.warnings.append(
            f"{report.missing_value_count} demand values are missing."
        )

    # Missing hours are also warnings at the raw ingestion layer.
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

        report.non_hourly_gap_count = len(bad_gaps)

        if report.non_hourly_gap_count:
            report.warnings.append(
                f"{report.non_hourly_gap_count} non-hourly gaps detected."
            )

    if errors:
        raise DataQualityError(
            "EIA data failed validation:\n- "
            + "\n- ".join(errors)
        )

    validated = (
        validated
        .sort_values("period")
        .reset_index(drop=True)
    )

    return validated, report