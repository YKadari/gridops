from __future__ import annotations

import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import (
    LinearRegression,
    RidgeCV,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)

from xgboost import XGBRegressor


CATEGORICAL_FEATURES = [
    "target_hour",
    "target_day_of_week",
    "target_month",
]


COMMON_NUMERIC_FEATURES = [
    "demand_lag_168h",
    "demand_lag_336h",
    "demand_rolling_mean_24h",
    "demand_rolling_mean_168h",
    "demand_history_count_24h",
    "demand_history_count_168h",

    "is_weekend",
    "is_holiday",
    "is_day_before_holiday",
    "is_day_after_holiday",

    "cooling_degree_feature",
    "heating_degree_feature",
]


FEATURES_BY_HORIZON = {
    24: [
        "demand_lag_26h",
        "demand_lag_48h",
        *COMMON_NUMERIC_FEATURES,

        "mean_temperature_forecast_24h",
        "min_temperature_forecast_24h",
        "max_temperature_forecast_24h",
        "temperature_range_forecast_24h",
        "mean_humidity_forecast_24h",
        "mean_dew_point_forecast_24h",
        "mean_apparent_temperature_forecast_24h",
        "mean_precipitation_forecast_24h",
        "mean_wind_speed_forecast_24h",

        *CATEGORICAL_FEATURES,
    ],

    48: [
        "demand_lag_50h",
        "demand_lag_72h",
        *COMMON_NUMERIC_FEATURES,

        "mean_temperature_forecast_48h",
        "min_temperature_forecast_48h",
        "max_temperature_forecast_48h",
        "temperature_range_forecast_48h",
        "mean_humidity_forecast_48h",
        "mean_dew_point_forecast_48h",
        "mean_apparent_temperature_forecast_48h",
        "mean_precipitation_forecast_48h",
        "mean_wind_speed_forecast_48h",

        *CATEGORICAL_FEATURES,
    ],
}


def build_preprocessor(
    *,
    horizon_hours: int,
) -> ColumnTransformer:

    features = FEATURES_BY_HORIZON[
        horizon_hours
    ]

    numeric_features = [
        feature
        for feature in features
        if feature not in CATEGORICAL_FEATURES
    ]

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                StandardScaler(),
                numeric_features,
            ),
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )


def build_linear_model(
    *,
    horizon_hours: int,
) -> Pipeline:

    return Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(
                    horizon_hours=horizon_hours
                ),
            ),
            (
                "model",
                LinearRegression(),
            ),
        ]
    )


def build_ridge_model(
    *,
    horizon_hours: int,
) -> Pipeline:

    return Pipeline(
        steps=[
            (
                "preprocessor",
                build_preprocessor(
                    horizon_hours=horizon_hours
                ),
            ),
            (
                "model",
                RidgeCV(
                    alphas=np.logspace(
                        -3,
                        4,
                        30,
                    )
                ),
            ),
        ]
    )


def build_xgboost_model(
    *,
    horizon_hours: int,
    params: dict | None = None,
) -> Pipeline:

    features = FEATURES_BY_HORIZON[
        horizon_hours
    ]

    numeric_features = [
        feature
        for feature in features
        if feature not in CATEGORICAL_FEATURES
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                "passthrough",
                numeric_features,
            ),
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    model_params = {
        "objective": "reg:squarederror",
        "n_estimators": 500,
        "learning_rate": 0.05,
        "max_depth": 6,
        "min_child_weight": 5,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "reg_lambda": 1.0,
        "reg_alpha": 0.0,
        "random_state": 42,
        "n_jobs": -1,
    }

    if params is not None:
        model_params.update(params)

    model = XGBRegressor(
        **model_params
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "model",
                model,
            ),
        ]
    )