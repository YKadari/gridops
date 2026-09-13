from __future__ import annotations

from gridops.config import Settings
from gridops.inference.features import (
    build_inference_features,
)
from datetime import datetime, timezone


def main() -> None:

    settings = Settings()

    print("Starting live feature check...")

    test_now = datetime(
        2026,
        9,
        13,
        9,
        0,
        tzinfo=timezone.utc,
    )

    for horizon_hours in (
        24,
        48,
    ):

        print()
        print("=" * 70)

        print(
            f"{horizon_hours}H "
            f"LIVE FEATURE BUILD"
        )

        print("=" * 70)

        print(
            f"Calling feature builder for "
            f"{horizon_hours}h..."
        )

        (
            features,
            issue_at,
            target_at,
        ) = build_inference_features(
            dsn=settings.postgres_dsn,
            horizon_hours=horizon_hours,
            now=test_now,
        )

        print(
            f"Feature builder returned for "
            f"{horizon_hours}h."
        )

        print(
            f"Forecast issue hour: "
            f"{issue_at}"
        )

        print(
            f"Target hour: "
            f"{target_at}"
        )

        print(
            f"Feature count: "
            f"{len(features)}"
        )

        print()

        for name, value in (
            features.items()
        ):
            print(
                f"{name}: {value}"
            )

        print()
        print(
            "✅ Live feature build "
            "succeeded."
        )


if __name__ == "__main__":
    main()