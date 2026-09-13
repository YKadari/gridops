from __future__ import annotations

import requests

from gridops.config import Settings
from gridops.modeling.data import load_feature_mart
from gridops.modeling.models import FEATURES_BY_HORIZON


API_BASE_URL = "http://127.0.0.1:8000"


def get_sample_features(
    *,
    dsn: str,
    horizon_hours: int,
) -> tuple[dict, float, str]:

    frame = load_feature_mart(
        dsn=dsn,
        horizon_hours=horizon_hours,
    )

    features = FEATURES_BY_HORIZON[
        horizon_hours
    ]

    usable = frame.dropna(
        subset=[
            "target_demand",
            *features,
        ]
    ).copy()

    # Use a historical row only as an integration-test input.
    sample = usable.iloc[-1]

    feature_payload = {}

    for feature in features:
        value = sample[feature]

        # Convert numpy/pandas scalars into normal
        # Python values for JSON serialization.
        if hasattr(value, "item"):
            value = value.item()

        feature_payload[feature] = value

    return (
        feature_payload,
        float(sample["target_demand"]),
        str(sample["target_at"]),
    )


def test_horizon(
    *,
    dsn: str,
    horizon_hours: int,
) -> None:

    payload, actual_demand, target_at = (
        get_sample_features(
            dsn=dsn,
            horizon_hours=horizon_hours,
        )
    )

    url = (
        f"{API_BASE_URL}/predict/"
        f"{horizon_hours}h"
    )

    print()
    print("=" * 70)
    print(
        f"{horizon_hours}H API TEST"
    )
    print("=" * 70)

    print(
        f"Target timestamp: {target_at}"
    )

    response = requests.post(
        url,
        json=payload,
        timeout=30,
    )

    print(
        f"HTTP status: "
        f"{response.status_code}"
    )

    response.raise_for_status()

    body = response.json()

    predicted_demand = float(
        body["predicted_demand"]
    )

    absolute_error = abs(
        actual_demand
        - predicted_demand
    )

    print(
        f"Actual demand:    "
        f"{actual_demand:,.2f}"
    )

    print(
        f"Predicted demand: "
        f"{predicted_demand:,.2f}"
    )

    print(
        f"Absolute error:   "
        f"{absolute_error:,.2f}"
    )

    print(
        f"Units: "
        f"{body['units']}"
    )

    assert (
        body["horizon_hours"]
        == horizon_hours
    )

    assert predicted_demand > 0

    print(
        "✅ API prediction succeeded."
    )


def main() -> None:

    settings = Settings()

    for horizon_hours in (
        24,
        48,
    ):
        test_horizon(
            dsn=settings.postgres_dsn,
            horizon_hours=horizon_hours,
        )


if __name__ == "__main__":
    main()