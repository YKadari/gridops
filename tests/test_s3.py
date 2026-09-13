from datetime import datetime, timezone

from gridops.storage.s3 import build_raw_eia_key

from gridops.storage.s3 import (
    build_raw_eia_key,
    build_raw_weather_key,
)


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

def test_build_raw_weather_key() -> None:
    start = datetime(
        2023,
        1,
        1,
        tzinfo=timezone.utc,
    )

    end = datetime(
        2023,
        2,
        1,
        tzinfo=timezone.utc,
    )

    created_at = datetime(
        2023,
        2,
        1,
        5,
        30,
        tzinfo=timezone.utc,
    )

    key = build_raw_weather_key(
        location_id="philadelphia",
        start=start,
        end=end,
        created_at=created_at,
    )

    assert key == (
        "weather/provider=open-meteo/"
        "location=philadelphia/"
        "year=2023/month=01/"
        "window_start=20230101T00/"
        "window_end=20230201T00/"
        "ingested_at=20230201T053000Z.csv"
    )