from __future__ import annotations

import time
from datetime import datetime, timezone

from gridops.flows.eia_incremental import (
    eia_incremental_flow,
)


INTERVAL_SECONDS = 3600


def main() -> None:
    while True:
        started_at = datetime.now(
            timezone.utc
        )

        print(
            f"[{started_at.isoformat()}] "
            "Starting scheduled EIA ingestion..."
        )

        try:
            loaded = eia_incremental_flow()

            print(
                "EIA ingestion completed. "
                f"Rows processed: {loaded}"
            )

        except Exception as exc:
            print(
                "EIA ingestion failed: "
                f"{type(exc).__name__}: {exc}"
            )

        print(
            f"Sleeping {INTERVAL_SECONDS} seconds..."
        )

        time.sleep(
            INTERVAL_SECONDS
        )


if __name__ == "__main__":
    main()