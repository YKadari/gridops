from datetime import datetime, timezone

from gridops.config import Settings
from gridops.ingestion.eia import EIAClient


def eia_timestamp(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H")


def main() -> None:
    settings = Settings()

    client = EIAClient(
        api_key=settings.eia_api_key,
        base_url=settings.eia_base_url,
    )

    start = datetime(
        2023,
        11,
        1,
        tzinfo=timezone.utc,
    )

    end = datetime(
        2023,
        11,
        30,
        23,
        tzinfo=timezone.utc,
    )

    frame = client.fetch_region_data(
        respondent="PJM",
        data_type="D",
        start=eia_timestamp(start),
        end=eia_timestamp(end),
    )

    print(f"Rows returned: {len(frame)}")
    print()

    # Find rows where demand is missing.
    null_rows = frame[frame["value"].isna()]

    print("NULL VALUE ROWS")
    print("----------------")
    print(null_rows[["period", "respondent", "value"]].to_string(index=False))

    print()

    # Find gaps in timestamps.
    periods = (
        frame["period"]
        .dropna()
        .drop_duplicates()
        .sort_values()
    )

    differences = periods.diff()

    gaps = differences[
        differences.dt.total_seconds() != 3600
    ].dropna()

    print("TIME GAPS")
    print("---------")

    for index in gaps.index:
        location = periods.index.get_loc(index)

        previous_period = periods.iloc[location - 1]
        current_period = periods.iloc[location]

        print(
            f"{previous_period} -> {current_period} "
            f"({current_period - previous_period})"
        )


if __name__ == "__main__":
    main()