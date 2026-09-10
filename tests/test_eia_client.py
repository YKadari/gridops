import pytest

from gridops.ingestion.eia import EIAClient


def test_page_size_guardrail() -> None:
    client = EIAClient(api_key="fake")

    with pytest.raises(ValueError):
        client.fetch_region_data(page_size=5001)
