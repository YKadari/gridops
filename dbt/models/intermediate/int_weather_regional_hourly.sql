with weather as (

    select
        observed_at,
        location_id,
        temperature_2m,
        relative_humidity_2m,
        dew_point_2m,
        apparent_temperature,
        precipitation,
        wind_speed_10m

    from {{ ref('stg_weather_hourly') }}

),

aggregated as (

    select
        observed_at,

        count(distinct location_id)
            as weather_location_count,

        avg(temperature_2m)
            as mean_temperature_2m,

        min(temperature_2m)
            as min_temperature_2m,

        max(temperature_2m)
            as max_temperature_2m,

        avg(relative_humidity_2m)
            as mean_relative_humidity_2m,

        avg(dew_point_2m)
            as mean_dew_point_2m,

        avg(apparent_temperature)
            as mean_apparent_temperature,

        avg(precipitation)
            as mean_precipitation,

        max(precipitation)
            as max_precipitation,

        avg(wind_speed_10m)
            as mean_wind_speed_10m,

        max(wind_speed_10m)
            as max_wind_speed_10m

    from weather

    group by observed_at

)

select *
from aggregated