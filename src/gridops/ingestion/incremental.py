from __future__ import annotations

from datetime import datetime, timedelta, timezone


def as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError("datetime must be timezone-aware.")

    return dt.astimezone(timezone.utc)


def floor_to_hour(dt: datetime) -> datetime:
    dt = as_utc(dt)

    return dt.replace(
        minute=0,
        second=0,
        microsecond=0,
    )


def plan_incremental_window(
    latest_period: datetime | None,
    *,
    now: datetime | None = None,
    overlap_hours: int = 24,
    source_lag_hours: int = 2,
    bootstrap_hours: int = 168,
) -> tuple[datetime, datetime]:
    """
    Plan the next GridOps incremental ingestion window.

    The pipeline deliberately overlaps recent data so revised or
    late-arriving observations can be refreshed through PostgreSQL UPSERTs.
    """

    if overlap_hours < 0:
        raise ValueError("overlap_hours cannot be negative.")

    if source_lag_hours < 0:
        raise ValueError("source_lag_hours cannot be negative.")

    if bootstrap_hours <= 0:
        raise ValueError("bootstrap_hours must be positive.")

    if now is None:
        now = datetime.now(timezone.utc)

    now = as_utc(now)

    end = floor_to_hour(
        now - timedelta(hours=source_lag_hours)
    )

    if latest_period is None:
        start = end - timedelta(hours=bootstrap_hours)
    else:
        latest_period = as_utc(latest_period)

        start = latest_period - timedelta(
            hours=overlap_hours
        )

    return start, end