select
    observed_at,
    weather_location_count

from {{ ref('int_weather_regional_hourly') }}

where weather_location_count != 6