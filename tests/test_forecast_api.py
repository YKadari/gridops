from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

import gridops.api.main as api_main


ISSUE_AT = datetime(
    2026,
    9,
    13,
    9,
    0,
    tzinfo=timezone.utc,
)

LATEST_EIA = datetime(
    2026,
    9,
    13,
    7,
    0,
    tzinfo=timezone.utc,
)


@pytest.mark.parametrize(
    "horizon_hours",
    [24, 48],
)
def test_live_forecast_success(
    monkeypatch,
    horizon_hours: int,
) -> None:


    from datetime import timedelta

    target_at = (
        ISSUE_AT
        + timedelta(hours=horizon_hours)
    )

    monkeypatch.setattr(
        api_main.model_service,
        "load_models",
        lambda: None,
    )

    monkeypatch.setattr(
        api_main,
        "get_serving_freshness_status",
        lambda **kwargs: {
            "checked_at": ISSUE_AT,
            "checked_hour": ISSUE_AT,
            "latest_observed_at": LATEST_EIA,
            "required_latest_at": LATEST_EIA,
            "source_lag_hours": 2.0,
            "expected_lag_hours": 2.0,
            "freshness_gap_hours": 0.0,
            "is_fresh": True,
        },
    )

    monkeypatch.setattr(
        api_main,
        "build_inference_features_dynamodb",
        lambda **kwargs: (
            {"example_feature": 1.0},
            ISSUE_AT,
            target_at,
        ),
    )

    monkeypatch.setattr(
        api_main.model_service,
        "predict",
        lambda **kwargs: 98765.43,
    )

    with TestClient(api_main.app) as client:
        response = client.post(
            f"/forecast/{horizon_hours}h"
        )

    assert response.status_code == 200

    body = response.json()

    assert body["horizon_hours"] == horizon_hours
    assert body["predicted_demand"] == pytest.approx(
        98765.43
    )

    assert body["units"] == "megawatthours"

    assert body[
        "eia_latest_observed_at"
    ].startswith(
        "2026-09-13T07:00:00"
    )


@pytest.mark.parametrize(
    "horizon_hours",
    [24, 48],
)
def test_live_forecast_rejects_stale_eia(
    monkeypatch,
    horizon_hours: int,
) -> None:

    required_latest = datetime(
        2026,
        9,
        13,
        8,
        0,
        tzinfo=timezone.utc,
    )

    monkeypatch.setattr(
        api_main.model_service,
        "load_models",
        lambda: None,
    )

    monkeypatch.setattr(
        api_main,
        "get_serving_freshness_status",
        lambda **kwargs: {
            "checked_at": ISSUE_AT,
            "checked_hour": ISSUE_AT,
            "latest_observed_at": LATEST_EIA,
            "required_latest_at": required_latest,
            "source_lag_hours": 3.0,
            "expected_lag_hours": 2.0,
            "freshness_gap_hours": 1.0,
            "is_fresh": False,
        },
    )

    with TestClient(api_main.app) as client:
        response = client.post(
            f"/forecast/{horizon_hours}h"
        )

    assert response.status_code == 503

    body = response.json()

    assert (
        body["detail"]["message"]
        == "EIA demand data is too stale "
        "for a safe forecast."
    )

    assert (
        body["detail"]["source_lag_hours"]
        == 3.0
    )

    assert (
        body["detail"]["expected_lag_hours"]
        == 2.0
    )