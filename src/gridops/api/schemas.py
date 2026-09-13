from __future__ import annotations

from pydantic import BaseModel, Field


class PredictionResponse(BaseModel):
    horizon_hours: int
    predicted_demand: float
    units: str = "megawatthours"


class PredictionRequest24h(BaseModel):
    demand_lag_26h: float
    demand_lag_48h: float
    demand_lag_168h: float
    demand_lag_336h: float

    demand_rolling_mean_24h: float
    demand_rolling_mean_168h: float

    demand_history_count_24h: float
    demand_history_count_168h: float

    is_weekend: bool
    is_holiday: bool
    is_day_before_holiday: bool
    is_day_after_holiday: bool

    cooling_degree_feature: float
    heating_degree_feature: float

    mean_temperature_forecast_24h: float
    min_temperature_forecast_24h: float
    max_temperature_forecast_24h: float
    temperature_range_forecast_24h: float

    mean_humidity_forecast_24h: float
    mean_dew_point_forecast_24h: float
    mean_apparent_temperature_forecast_24h: float
    mean_precipitation_forecast_24h: float
    mean_wind_speed_forecast_24h: float

    target_hour: int = Field(
        ge=0,
        le=23,
    )

    target_day_of_week: int = Field(
        ge=1,
        le=7,
    )

    target_month: int = Field(
        ge=1,
        le=12,
    )


class PredictionRequest48h(BaseModel):
    demand_lag_50h: float
    demand_lag_72h: float
    demand_lag_168h: float
    demand_lag_336h: float

    demand_rolling_mean_24h: float
    demand_rolling_mean_168h: float

    demand_history_count_24h: float
    demand_history_count_168h: float

    is_weekend: bool
    is_holiday: bool
    is_day_before_holiday: bool
    is_day_after_holiday: bool

    cooling_degree_feature: float
    heating_degree_feature: float

    mean_temperature_forecast_48h: float
    min_temperature_forecast_48h: float
    max_temperature_forecast_48h: float
    temperature_range_forecast_48h: float

    mean_humidity_forecast_48h: float
    mean_dew_point_forecast_48h: float
    mean_apparent_temperature_forecast_48h: float
    mean_precipitation_forecast_48h: float
    mean_wind_speed_forecast_48h: float

    target_hour: int = Field(
        ge=0,
        le=23,
    )

    target_day_of_week: int = Field(
        ge=1,
        le=7,
    )

    target_month: int = Field(
        ge=1,
        le=12,
    )