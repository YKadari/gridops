
  create view "gridops"."intermediate"."int_weather_forecast_regional_hourly__dbt_tmp"
    
    
  as (
    with forecasts as (

    select *
    from "gridops"."staging"."stg_weather_forecast_hourly"

),

regional as (

    select
        valid_at,

        count(distinct location_id)
            as forecast_location_count,

        avg(temperature_2m_forecast_24h)
            as mean_temperature_forecast_24h,

        min(temperature_2m_forecast_24h)
            as min_temperature_forecast_24h,

        max(temperature_2m_forecast_24h)
            as max_temperature_forecast_24h,

        avg(relative_humidity_2m_forecast_24h)
            as mean_humidity_forecast_24h,

        avg(dew_point_2m_forecast_24h)
            as mean_dew_point_forecast_24h,

        avg(apparent_temperature_forecast_24h)
            as mean_apparent_temperature_forecast_24h,

        avg(precipitation_forecast_24h)
            as mean_precipitation_forecast_24h,

        avg(wind_speed_10m_forecast_24h)
            as mean_wind_speed_forecast_24h,

        avg(temperature_2m_forecast_48h)
            as mean_temperature_forecast_48h,

        min(temperature_2m_forecast_48h)
            as min_temperature_forecast_48h,

        max(temperature_2m_forecast_48h)
            as max_temperature_forecast_48h,

        avg(relative_humidity_2m_forecast_48h)
            as mean_humidity_forecast_48h,

        avg(dew_point_2m_forecast_48h)
            as mean_dew_point_forecast_48h,

        avg(apparent_temperature_forecast_48h)
            as mean_apparent_temperature_forecast_48h,

        avg(precipitation_forecast_48h)
            as mean_precipitation_forecast_48h,

        avg(wind_speed_10m_forecast_48h)
            as mean_wind_speed_forecast_48h

    from forecasts

    group by valid_at

)

select *
from regional
  );