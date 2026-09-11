from datetime import datetime, timezone

from gridops.storage.s3 import build_raw_eia_key


def test_build_raw_eia_key() -> None:
    start = datetime(
        2026,
        9,
        10,
        4,
        tzinfo=timezone.utc,
    )

    end = datetime(
        2026,
        9,
        11,
        3,
        tzinfo=timezone.utc,
    )

    created_at = datetime(
        2026,
        9,
        11,
        5,
        30,
        tzinfo=timezone.utc,
    )

    key = build_raw_eia_key(
        respondent="PJM",
        start=start,
        end=end,
        created_at=created_at,
    )

    assert key == (
        "eia/respondent=PJM/metric=demand/"
        "year=2026/month=09/day=10/"
        "window_start=20260910T04/"
        "window_end=20260911T03/"
        "ingested_at=20260911T053000Z.csv"
    )