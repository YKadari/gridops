from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO

import boto3
import pandas as pd


def build_raw_eia_key(
    *,
    respondent: str,
    start: datetime,
    end: datetime,
    created_at: datetime | None = None,
) -> str:
    if created_at is None:
        created_at = datetime.now(timezone.utc)

    created_at = created_at.astimezone(timezone.utc)

    timestamp = created_at.strftime("%Y%m%dT%H%M%SZ")

    return (
        f"eia/"
        f"respondent={respondent}/"
        f"metric=demand/"
        f"year={start.year:04d}/"
        f"month={start.month:02d}/"
        f"day={start.day:02d}/"
        f"window_start={start:%Y%m%dT%H}/"
        f"window_end={end:%Y%m%dT%H}/"
        f"ingested_at={timestamp}.csv"
    )

def build_raw_weather_key(
    *,
    location_id: str,
    start: datetime,
    end: datetime,
    created_at: datetime | None = None,
) -> str:
    if created_at is None:
        created_at = datetime.now(timezone.utc)

    created_at = created_at.astimezone(timezone.utc)

    timestamp = created_at.strftime("%Y%m%dT%H%M%SZ")

    return (
        f"weather/"
        f"provider=open-meteo/"
        f"location={location_id}/"
        f"year={start.year:04d}/"
        f"month={start.month:02d}/"
        f"window_start={start:%Y%m%dT%H}/"
        f"window_end={end:%Y%m%dT%H}/"
        f"ingested_at={timestamp}.csv"
    )
def upload_weather_frame(
    frame: pd.DataFrame,
    *,
    bucket: str,
    key: str,
    profile_name: str | None,
    region_name: str,
) -> None:
    buffer = StringIO()

    frame.to_csv(
        buffer,
        index=False,
    )

    client = create_s3_client(
        profile_name=profile_name,
        region_name=region_name,
    )

    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=buffer.getvalue().encode("utf-8"),
        ContentType="text/csv",
        Metadata={
            "gridops-layer": "raw",
            "gridops-source": "open-meteo",
        },
    )

def create_s3_client(
    *,
    profile_name: str | None,
    region_name: str,
):
    if profile_name:
        session = boto3.Session(
            profile_name=profile_name,
            region_name=region_name,
        )
    else:
        session = boto3.Session(
            region_name=region_name,
        )

    return session.client("s3")


def upload_eia_frame(
    frame: pd.DataFrame,
    *,
    bucket: str,
    key: str,
    profile_name: str | None,
    region_name: str,
) -> None:
    buffer = StringIO()

    frame.to_csv(
        buffer,
        index=False,
    )

    client = create_s3_client(
        profile_name=profile_name,
        region_name=region_name,
    )

    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=buffer.getvalue().encode("utf-8"),
        ContentType="text/csv",
        Metadata={
            "gridops-layer": "raw",
            "gridops-source": "eia",
        },
    )
def build_raw_weather_forecast_key(
    *,
    location_id: str,
    start: datetime,
    end: datetime,
    created_at: datetime | None = None,
) -> str:

    if created_at is None:
        created_at = datetime.now(timezone.utc)

    created_at = created_at.astimezone(
        timezone.utc
    )

    timestamp = created_at.strftime(
        "%Y%m%dT%H%M%SZ"
    )

    return (
        f"weather-forecast/"
        f"provider=open-meteo/"
        f"location={location_id}/"
        f"year={start.year:04d}/"
        f"month={start.month:02d}/"
        f"window_start={start:%Y%m%dT%H}/"
        f"window_end={end:%Y%m%dT%H}/"
        f"ingested_at={timestamp}.csv"
    )

def upload_weather_forecast_frame(
    frame: pd.DataFrame,
    *,
    bucket: str,
    key: str,
    profile_name: str | None,
    region_name: str,
) -> None:

    buffer = StringIO()

    frame.to_csv(
        buffer,
        index=False,
    )

    client = create_s3_client(
        profile_name=profile_name,
        region_name=region_name,
    )

    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=buffer.getvalue().encode(
            "utf-8"
        ),
        ContentType="text/csv",
        Metadata={
            "gridops-layer": "raw",
            "gridops-source": (
                "open-meteo-previous-runs"
            ),
        },
    )