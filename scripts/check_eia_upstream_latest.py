from __future__ import annotations

import requests

from gridops.config import Settings


def main() -> None:
    settings = Settings()

    params = [
        ("api_key", settings.eia_api_key),
        ("frequency", "hourly"),
        ("data[0]", "value"),
        ("facets[respondent][]", "PJM"),
        ("facets[type][]", "D"),
        ("sort[0][column]", "period"),
        ("sort[0][direction]", "desc"),
        ("offset", "0"),
        ("length", "10"),
    ]

    response = requests.get(
        settings.eia_base_url,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    payload = response.json()

    rows = payload["response"]["data"]

    print()
    print("LATEST PJM DEMAND AVAILABLE DIRECTLY FROM EIA")
    print("=" * 60)

    for row in rows:
        print(
            row["period"],
            row.get("value"),
        )


if __name__ == "__main__":
    main()