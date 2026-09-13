from __future__ import annotations

import mlflow
import mlflow.sklearn
import pandas as pd


MODEL_URIS = {
    24: "models:/gridops-demand-24h@champion",
    48: "models:/gridops-demand-48h@champion",
}


class ModelService:
    def __init__(self) -> None:
        self.models: dict[int, object] = {}

    def load_models(self) -> None:
        for horizon, uri in MODEL_URIS.items():
            self.models[horizon] = (
                mlflow.sklearn.load_model(uri)
            )

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

        return float(prediction[0])