from datetime import datetime, timezone

from gridops.ingestion.incremental import plan_incremental_window


def test_incremental_window_from_latest_period() -> None:
    latest = datetime(
        2026,
        9,
        10,
        2,
        tzinfo=timezone.utc,
    )

    now = datetime(
        2026,
        9,
        10,
        15,
        37,
        tzinfo=timezone.utc,
    )

    start, end = plan_incremental_window(
        latest,
        now=now,
        overlap_hours=24,
        source_lag_hours=2,
    )

    assert start == datetime(
        2026,
        9,
        9,
        2,
        tzinfo=timezone.utc,
    )

    assert end == datetime(
        2026,
        9,
        10,
        13,
        tzinfo=timezone.utc,
    )


def test_incremental_window_bootstraps_without_data() -> None:
    now = datetime(
        2026,
        9,
        10,
        15,
        37,
        tzinfo=timezone.utc,
    )

    start, end = plan_incremental_window(
        None,
        now=now,
        bootstrap_hours=168,
        source_lag_hours=2,
    )

    assert end == datetime(
        2026,
        9,
        10,
        13,
        tzinfo=timezone.utc,
    )

    assert (end - start).total_seconds() == 168 * 3600