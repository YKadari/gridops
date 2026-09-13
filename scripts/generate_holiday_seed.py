from pathlib import Path

import holidays
import pandas as pd


START_YEAR = 2024
END_YEAR = 2030


def main() -> None:
    calendar = holidays.UnitedStates(
        years=range(
            START_YEAR,
            END_YEAR + 1,
        ),
        observed=True,
    )

    records = [
        {
            "holiday_date": day.isoformat(),
            "holiday_name": name,
        }
        for day, name in calendar.items()
    ]

    frame = (
        pd.DataFrame(records)
        .sort_values("holiday_date")
        .reset_index(drop=True)
    )

    output = Path(
        "dbt/seeds/us_federal_holidays.csv"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame.to_csv(
        output,
        index=False,
    )

    print(
        f"Wrote {len(frame)} holiday dates "
        f"to {output}"
    )


if __name__ == "__main__":
    main()