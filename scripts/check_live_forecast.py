from __future__ import annotations

from datetime import datetime, timezone

from gridops.config import Settings
from gridops.api.model_service import ModelService
from gridops.inference.features import (
    build_inference_features,
)


def main() -> None:
    settings = Settings()

    # Controlled issue time.
    # EIA data through 07:00 UTC is available,
    # so the model's 2-hour source-lag contract is satisfied.
    test_now = datetime(
        2026,
        9,
        13,
        9,
        0,
        tzinfo=timezone.utc,
    )

    model_service = ModelService()

    print("Loading MLflow champion models...")
    model_service.load_models()
    print("✅ Models loaded.")

    for horizon_hours in (24, 48):
        print()
        print("=" * 70)
        print(f"{horizon_hours}H END-TO-END LIVE FORECAST")
        print("=" * 70)

        (
            features,
            issue_at,
            target_at,
        ) = build_inference_features(
            dsn=settings.postgres_dsn,
            horizon_hours=horizon_hours,
            now=test_now,
        )

        prediction = model_service.predict(
            horizon_hours=horizon_hours,
            features=features,
        )

        print(f"Issue time:       {issue_at}")
        print(f"Target time:      {target_at}")
        print(
            f"Predicted demand: "
            f"{prediction:,.2f} megawatthours"
        )

        print(
            "✅ End-to-end forecast succeeded."
        )


if __name__ == "__main__":
    main()