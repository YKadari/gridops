from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

from gridops.config import Settings
from gridops.ingestion.eia import EIAClient


def eia_timestamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    settings = Settings()

    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=7)

    client = EIAClient(
        api_key=settings.eia_api_key,
        base_url=settings.eia_base_url,
    )

    print("Fetching the last 7 days of PJM hourly electricity demand...")
    frame = client.fetch_region_data(
        respondent="PJM",
        data_type="D",
        start=eia_timestamp(start),
        end=eia_timestamp(end),
    )

    if frame.empty:
        raise RuntimeError("The EIA request succeeded but returned no rows.")

    output_dir = Path("data/raw/eia")
    output_dir.mkdir(parents=True, exist_ok=True)

    stamp = end.strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"pjm_demand_{stamp}.csv"
    frame.to_csv(output_path, index=False)

    print()
    print(f"Rows downloaded: {len(frame):,}")
    print(f"Columns: {list(frame.columns)}")
    print(f"Time range: {frame['period'].min()} -> {frame['period'].max()}")
    print(f"Saved to: {output_path}")
    print()
    print(frame.tail(5).to_string(index=False))


if __name__ == "__main__":
    main()
