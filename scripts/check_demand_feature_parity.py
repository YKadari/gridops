from __future__ import annotations

from datetime import timedelta

from gridops.config import Settings
from gridops.inference.features import (
    _build_demand_features_dynamodb,
    _build_demand_features_postgres,
    floor_to_utc_hour,
)


def main() -> None:
    from datetime import datetime, timezone

    settings = Settings()

    issue_at = floor_to_utc_hour(
        datetime.now(timezone.utc)
    )

    for horizon_hours in (24, 48):

        target_at = (
            issue_at
            + timedelta(
                hours=horizon_hours
            )
        )

        postgres = (
            _build_demand_features_postgres(
                dsn=settings.postgres_dsn,
                target_at=target_at,
                horizon_hours=horizon_hours,
            )
        )

        dynamodb = (
            _build_demand_features_dynamodb(
                table_name=(
                    settings.dynamodb_demand_table
                ),
                profile_name=settings.aws_profile,
                region_name=settings.aws_region,
                target_at=target_at,
                horizon_hours=horizon_hours,
            )
        )

        print()
        print("=" * 70)
        print(
            f"{horizon_hours}H DEMAND FEATURE PARITY"
        )
        print("=" * 70)

        mismatches = []

        for feature in postgres:
            postgres_value = postgres[
                feature
            ]

            dynamodb_value = dynamodb[
                feature
            ]

            difference = abs(
                postgres_value
                - dynamodb_value
            )

            print(
                f"{feature}: "
                f"postgres={postgres_value:.6f}, "
                f"dynamodb={dynamodb_value:.6f}, "
                f"diff={difference:.12f}"
            )

            if difference > 1e-9:
                mismatches.append(
                    feature
                )

        if mismatches:
            raise RuntimeError(
                "Demand feature mismatch: "
                f"{mismatches}"
            )

        print()
        print(
            "✅ Demand features match exactly."
        )


if __name__ == "__main__":
    main()