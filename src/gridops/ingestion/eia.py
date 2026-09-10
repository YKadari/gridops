from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd
import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

LOGGER = logging.getLogger(__name__)


class EIAError(RuntimeError):
    """Raised when the EIA API response is invalid or unusable."""


@dataclass
class EIAClient:
    api_key: str
    base_url: str = "https://api.eia.gov/v2/electricity/rto/region-data/data/"
    timeout_seconds: int = 30

    @retry(
        retry=retry_if_exception_type((requests.RequestException, EIAError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _request_page(
        self,
        *,
        respondent: str,
        data_type: str,
        start: str | None,
        end: str | None,
        offset: int,
        length: int,
    ) -> dict[str, Any]:
        params: list[tuple[str, str | int]] = [
            ("api_key", self.api_key),
            ("frequency", "hourly"),
            ("data[0]", "value"),
            ("facets[respondent][]", respondent),
            ("facets[type][]", data_type),
            ("sort[0][column]", "period"),
            ("sort[0][direction]", "asc"),
            ("offset", offset),
            ("length", length),
        ]

        if start:
            params.append(("start", start))
        if end:
            params.append(("end", end))

        response = requests.get(
            self.base_url,
            params=params,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        payload = response.json()
        api_response = payload.get("response")

        if not isinstance(api_response, dict):
            raise EIAError(f"Unexpected EIA payload: {payload}")

        if "data" not in api_response:
            raise EIAError(f"EIA response did not include data: {payload}")

        return payload

    def fetch_region_data(
        self,
        *,
        respondent: str = "PJM",
        data_type: str = "D",
        start: str | None = None,
        end: str | None = None,
        page_size: int = 5000,
    ) -> pd.DataFrame:
        if not 1 <= page_size <= 5000:
            raise ValueError("page_size must be between 1 and 5000.")

        all_rows: list[dict[str, Any]] = []
        offset = 0
        total: int | None = None

        while total is None or offset < total:
            payload = self._request_page(
                respondent=respondent,
                data_type=data_type,
                start=start,
                end=end,
                offset=offset,
                length=page_size,
            )

            api_response = payload["response"]
            rows = api_response.get("data", [])
            total = int(api_response.get("total", len(rows)))

            LOGGER.info(
                "Fetched %s rows from EIA (offset=%s, total=%s)",
                len(rows),
                offset,
                total,
            )

            if not rows:
                break

            all_rows.extend(rows)
            offset += len(rows)

            if len(rows) < page_size:
                break

        frame = pd.DataFrame(all_rows)

        if frame.empty:
            return frame

        if "period" in frame.columns:
            frame["period"] = pd.to_datetime(frame["period"], utc=True, errors="coerce")

        if "value" in frame.columns:
            frame["value"] = pd.to_numeric(frame["value"], errors="coerce")

        frame = frame.drop_duplicates().sort_values("period").reset_index(drop=True)
        return frame
