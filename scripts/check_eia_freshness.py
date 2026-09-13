from gridops.config import Settings
from gridops.database.monitoring import (
    record_eia_freshness,
)


def main() -> None:
    settings = Settings()

    result = record_eia_freshness(
        dsn=settings.postgres_dsn,
        expected_lag_hours=2.0,
    )

    print()
    print("EIA SOURCE FRESHNESS")
    print("=" * 50)

    print(
        f"Checked at:        "
        f"{result['checked_at']}"
    )

    print(
        f"Latest observation:"
        f" {result['latest_observed_at']}"
    )

    print(
        f"Observed lag:      "
        f" {result['source_lag_hours']:.2f} hours"
    )

    print(
        f"Expected lag:      "
        f" {result['expected_lag_hours']:.2f} hours"
    )

    print(
        f"Freshness gap:     "
        f" {result['freshness_gap_hours']:+.2f} hours"
    )


if __name__ == "__main__":
    main()