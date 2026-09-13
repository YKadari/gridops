
  create view "gridops"."marts"."demand_weather_training_base__dbt_tmp"
    
    
  as (
    with demand as (

    select *
    from "gridops"."intermediate"."int_eia_demand_hourly"

),

weather as (

    select *
    from "gridops"."intermediate"."int_weather_regional_hourly"

),

joined as (

    select
        demand.observed_at,

        demand.demand_value,

        demand.is_missing_source_row,
        demand.is_missing_demand,

        weather.weather_location_count,

        weather.mean_temperature_2m,
        weather.min_temperature_2m,
        weather.max_temperature_2m,

        weather.mean_relative_humidity_2m,
        weather.mean_dew_point_2m,

        weather.mean_apparent_temperature,

        weather.mean_precipitation,
        weather.max_precipitation,

        weather.mean_wind_speed_10m,
        weather.max_wind_speed_10m

    from demand

    left join weather
        on demand.observed_at = weather.observed_at

)

select *
from joined
  );