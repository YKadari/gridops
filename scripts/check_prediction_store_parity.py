from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pandas as pd

from gridops.config import Settings
from gridops.inference.features import (
    _build_calendar_features,
    _build_demand_features_dynamodb,
    _build_demand_features_postgres,
    _build_weather_features,
    floor_to_utc_hour,
)
from gridops.modeling.models import (
    FEATURES_BY_HORIZON,
)
from gridops.modeling.production_loader import (
    load_production_model_from_s3,
)


def build_features(
    *,
    demand_features: dict[str, float],
    weather_features: dict[str, float],
    calendar_features: dict[str, object],
    horizon_hours: int,
) -> dict[str, object]:

    features: dict[str, object] = {}

    features.update(
        demand_features
    )

    features.update(
        weather_features
    )

    features.update(
        calendar_features
    )

    expected = FEATURES_BY_HORIZON[
        horizon_hours
    ]

    return {
        feature: features[feature]
        for feature in expected
    }


def main() -> None:
    settings = Settings()

    issue_at = floor_to_utc_hour(
        datetime.now(timezone.utc)
    )

    for horizon_hours in (
        24,
        48,
    ):

        target_at = (
            issue_at
            + timedelta(
                hours=horizon_hours
            )
        )

        print()
        print("=" * 70)
        print(
            f"{horizon_hours}H "
            "PREDICTION STORE PARITY"
        )
        print("=" * 70)

        # Build the non-demand features only once.
        # This ensures both predictions use
        # identical live weather/calendar inputs.
        weather_features = (
            _build_weather_features(
                target_at=target_at,
                horizon_hours=horizon_hours,
            )
        )

        calendar_features = (
            _build_calendar_features(
                target_at=target_at
            )
        )

        postgres_demand = (
            _build_demand_features_postgres(
                dsn=settings.postgres_dsn,
                target_at=target_at,
                horizon_hours=horizon_hours,
            )
        )

        dynamodb_demand = (
            _build_demand_features_dynamodb(
                table_name=(
                    settings.dynamodb_demand_table
                ),
                profile_name=(
                    settings.aws_profile
                ),
                region_name=(
                    settings.aws_region
                ),
                target_at=target_at,
                horizon_hours=horizon_hours,
            )
        )

        postgres_features = build_features(
            demand_features=postgres_demand,
            weather_features=weather_features,
            calendar_features=calendar_features,
            horizon_hours=horizon_hours,
        )

        dynamodb_features = build_features(
            demand_features=dynamodb_demand,
            weather_features=weather_features,
            calendar_features=calendar_features,
            horizon_hours=horizon_hours,
        )

        feature_mismatches = []

        for feature in postgres_features:
            if (
                postgres_features[feature]
                != dynamodb_features[feature]
            ):
                feature_mismatches.append(
                    feature
                )

        if feature_mismatches:
            raise RuntimeError(
                "Full feature mismatch: "
                f"{feature_mismatches}"
            )

        print(
            "Full feature vectors match."
        )

        model, metadata = (
            load_production_model_from_s3(
                bucket=settings.s3_raw_bucket,
                horizon_hours=horizon_hours,
                profile_name=settings.aws_profile,
                region_name=settings.aws_region,
            )
        )

        postgres_frame = pd.DataFrame(
            [postgres_features]
        )

        dynamodb_frame = pd.DataFrame(
            [dynamodb_features]
        )

        postgres_prediction = float(
            model.predict(
                postgres_frame
            )[0]
        )

        dynamodb_prediction = float(
            model.predict(
                dynamodb_frame
            )[0]
        )

        difference = abs(
            postgres_prediction
            - dynamodb_prediction
        )

        print(
            f"Model version: "
            f"{metadata['version']}"
        )

        print(
            f"PostgreSQL prediction: "
            f"{postgres_prediction:,.6f}"
        )

        print(
            f"DynamoDB prediction:   "
            f"{dynamodb_prediction:,.6f}"
        )

        print(
            f"Difference:             "
            f"{difference:.12f}"
        )

        assert math.isclose(
            postgres_prediction,
            dynamodb_prediction,
            rel_tol=0.0,
            abs_tol=1e-9,
        )

        print()
        print(
            "✅ Predictions match."
        )


if __name__ == "__main__":
    main()