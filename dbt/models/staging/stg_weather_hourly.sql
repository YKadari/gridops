select
    observed_at,
    location_id,
    location_name,

    latitude,
    longitude,

    temperature_2m,
    relative_humidity_2m,
    dew_point_2m,
    apparent_temperature,
    precipitation,
    wind_speed_10m,

    ingested_at

from {{ source('weather', 'weather_hourly') }}

where observed_at >= '2023-01-01 00:00:00+00'
  and observed_at <  '2026-01-01 00:00:00+00'