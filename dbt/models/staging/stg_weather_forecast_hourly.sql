select
    valid_at,
    location_id,
    location_name,
    latitude,
    longitude,

    temperature_2m_forecast_24h,
    relative_humidity_2m_forecast_24h,
    dew_point_2m_forecast_24h,
    apparent_temperature_forecast_24h,
    precipitation_forecast_24h,
    wind_speed_10m_forecast_24h,

    temperature_2m_forecast_48h,
    relative_humidity_2m_forecast_48h,
    dew_point_2m_forecast_48h,
    apparent_temperature_forecast_48h,
    precipitation_forecast_48h,
    wind_speed_10m_forecast_48h,

    ingested_at

from {{ source('weather_forecast', 'weather_forecast_hourly') }}

where valid_at >= '2024-01-01 00:00:00+00'
  and valid_at <  '2026-01-01 00:00:00+00'