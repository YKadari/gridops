import pandas as pd
import pytest

from gridops.quality.eia import DataQualityError, validate_eia_demand


def sample_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "period": [
                "2026-09-01T00:00:00Z",
                "2026-09-01T01:00:00Z",
                "2026-09-01T02:00:00Z",
            ],
            "respondent": ["PJM", "PJM", "PJM"],
            "respondent-name": [
                "PJM Interconnection, LLC",
                "PJM Interconnection, LLC",
                "PJM Interconnection, LLC",
            ],
            "type": ["D", "D", "D"],
            "type-name": ["Demand", "Demand", "Demand"],
            "value": [100000, 101000, 102000],
            "value-units": [
                "megawatthours",
                "megawatthours",
                "megawatthours",
            ],
        }
    )


def test_valid_data_passes() -> None:
    result, report = validate_eia_demand(sample_data())
    assert len(result) == 3
    assert result["period"].notna().all()
    assert result["value"].notna().all()
    assert not report.has_warnings


def test_duplicate_record_fails() -> None:
    frame = sample_data()

    frame = pd.concat(
        [frame, frame.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(DataQualityError):
        validate_eia_demand(frame)


def test_negative_demand_fails() -> None:
    frame = sample_data()

    frame.loc[0, "value"] = -500

    with pytest.raises(DataQualityError):
        validate_eia_demand(frame)


def test_missing_hour_creates_warning() -> None:
    frame = sample_data()
    frame = frame.drop(index=1)

    result, report = validate_eia_demand(frame)

    assert len(result) == 2
    assert report.non_hourly_gap_count == 1
    assert report.has_warnings

def test_missing_value_creates_warning() -> None:
    frame = sample_data()
    frame.loc[1, "value"] = None

    result, report = validate_eia_demand(frame)

    assert len(result) == 3
    assert report.missing_value_count == 1
    assert report.has_warnings