from __future__ import annotations

import pandas as pd

from gridops.modeling.production_loader import (
    load_production_model_from_s3,
)


class ModelService:
    def __init__(
        self,
        *,
        bucket: str,
        profile_name: str | None = None,
        region_name: str | None = None,
    ) -> None:
        self.bucket = bucket
        self.profile_name = profile_name
        self.region_name = region_name

        self.models: dict[int, object] = {}
        self.metadata: dict[int, dict] = {}

    def load_models(self) -> None:
        """
        Load the 24h and 48h production champion models.

        This method is idempotent so a warm Lambda invocation
        does not download models that are already loaded.
        """
        for horizon_hours in (24, 48):

            if horizon_hours in self.models:
                continue

            model, metadata = (
                load_production_model_from_s3(
                    bucket=self.bucket,
                    horizon_hours=horizon_hours,
                    profile_name=self.profile_name,
                    region_name=self.region_name,
                )
            )

            self.models[
                horizon_hours
            ] = model

            self.metadata[
                horizon_hours
            ] = metadata

    def is_ready(self) -> bool:
        return (
            24 in self.models
            and 48 in self.models
        )

    def predict(
        self,
        *,
        horizon_hours: int,
        features: dict,
    ) -> float:

        if horizon_hours not in self.models:
            raise ValueError(
                f"No loaded model for "
                f"{horizon_hours}h horizon."
            )

        frame = pd.DataFrame(
            [features]
        )

        prediction = self.models[
            horizon_hours
        ].predict(frame)

        return float(
            prediction[0]
        )