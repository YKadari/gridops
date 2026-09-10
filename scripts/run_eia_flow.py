from datetime import datetime, timezone

from gridops.flows.eia_pipeline import eia_ingestion_flow


if __name__ == "__main__":
    eia_ingestion_flow(
        start=datetime(
            2025,
            12,
            1,
            tzinfo=timezone.utc,
        ),
        end=datetime(
            2025,
            12,
            2,
            tzinfo=timezone.utc,
        ),
        respondent="PJM",
    )