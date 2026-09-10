from datetime import datetime, timezone

import pytest

from gridops.ingestion.backfill import build_monthly_windows
from gridops.ingestion.backfill import (
    build_monthly_windows,
    to_eia_inclusive_end,
)

def test_eia_inclusive_end() -> None:
    exclusive_end = datetime(
        2026,
        2,
        1,
        0,
        0,
        tzinfo=timezone.utc,
    )

    result = to_eia_inclusive_end(exclusive_end)

    assert result == datetime(
        2026,
        1,
        31,
        23,
        0,
        tzinfo=timezone.utc,
    )
    
def utc(year: int, month: int, day: int) -> datetime:
    return datetime(
        year,
        month,
        day,
        tzinfo=timezone.utc,
    )


def test_build_monthly_windows() -> None:
    windows = build_monthly_windows(
        utc(2026, 1, 15),
        utc(2026, 4, 10),
    )

    assert windows == [
        (
            utc(2026, 1, 15),
            utc(2026, 2, 1),
        ),
        (
            utc(2026, 2, 1),
            utc(2026, 3, 1),
        ),
        (
            utc(2026, 3, 1),
            utc(2026, 4, 1),
        ),
        (
            utc(2026, 4, 1),
            utc(2026, 4, 10),
        ),
    ]


def test_invalid_range_fails() -> None:
    with pytest.raises(ValueError):
        build_monthly_windows(
            utc(2026, 5, 1),
            utc(2026, 4, 1),
        )