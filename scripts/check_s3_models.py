from __future__ import annotations

from gridops.config import Settings
from gridops.modeling.production_loader import (
    load_production_model_from_s3,
)


def main() -> None:
    settings = Settings()

    for horizon_hours in (24, 48):
        print()
        print("=" * 70)
        print(
            f"{horizon_hours}H S3 CHAMPION LOAD"
        )
        print("=" * 70)

        model, metadata = (
            load_production_model_from_s3(
                bucket=settings.s3_raw_bucket,
                horizon_hours=horizon_hours,
                profile_name=settings.aws_profile,
                region_name=settings.aws_region,
            )
        )

        print(
            f"Model: "
            f"{metadata['model_name']}"
        )

        print(
            f"Version: "
            f"{metadata['version']}"
        )

        print(
            f"SHA256 verified: yes"
        )

        print(
            f"Loaded object: "
            f"{type(model)}"
        )

        print(
            "✅ S3 champion loaded successfully."
        )


if __name__ == "__main__":
    main()