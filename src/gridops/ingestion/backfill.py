from __future__ import annotations

from datetime import datetime, timedelta, timezone

def to_eia_inclusive_end(exclusive_end: datetime) -> datetime:
    """
    Convert GridOps' exclusive hourly window end into the
    inclusive end timestamp expected by the EIA API.
    """

    return exclusive_end - timedelta(hours=1)


def build_monthly_windows(
    start: datetime,
    end: datetime,
) -> list[tuple[datetime, datetime]]:
    """
    Split a datetime range into monthly ingestion windows.

    Windows are represented as [start, end), meaning the start timestamp
    is included and the end timestamp is excluded.
    """

    if start >= end:
        raise ValueError("start must be earlier than end.")

    start = start.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)

    windows: list[tuple[datetime, datetime]] = []

    current = start

    while current < end:
        if current.month == 12:
            next_month = current.replace(
                year=current.year + 1,
                month=1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        else:
            next_month = current.replace(
                month=current.month + 1,
                day=1,
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )

        window_end = min(next_month, end)

        windows.append(
            (
                current,
                window_end,
            )
        )

        current = window_end

    return windows