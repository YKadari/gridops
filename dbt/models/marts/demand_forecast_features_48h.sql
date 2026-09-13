with demand_features as (

    select
        observed_at as target_at,

        -- Prediction target
        demand_value as target_demand,

        -- Freshest demand assumed available when the
        -- 48-hour forecast is issued, including a
        -- conservative 2-hour source-lag buffer.
        lag(demand_value, 50) over (
            order by observed_at
        ) as demand_lag_50h,

        -- Same hour three days earlier.
        lag(demand_value, 72) over (
            order by observed_at
        ) as demand_lag_72h,

        -- Same hour one week earlier.
        lag(demand_value, 168) over (
            order by observed_at
        ) as demand_lag_168h,

        -- Same hour two weeks earlier.
        lag(demand_value, 336) over (
            order by observed_at
        ) as demand_lag_336h,

        -- Most recent 24 demand observations available
        -- at forecast issue time.
        avg(demand_value) over (
            order by observed_at
            rows between 73 preceding and 50 preceding
        ) as demand_rolling_mean_24h,

        -- Most recent 168 observations available
        -- at forecast issue time.
        avg(demand_value) over (
            order by observed_at
            rows between 217 preceding and 50 preceding
        ) as demand_rolling_mean_168h,

        count(demand_value) over (
            order by observed_at
            rows between 73 preceding and 50 preceding
        ) as demand_history_count_24h,

        count(demand_value) over (
            order by observed_at
            rows between 217 preceding and 50 preceding
        ) as demand_history_count_168h,

        -- Calendar features for the target hour.
        extract(
            hour from observed_at
            at time zone 'America/New_York'
        )::integer as target_hour,

        extract(
            isodow from observed_at
            at time zone 'America/New_York'
        )::integer as target_day_of_week,

        extract(
            month from observed_at
            at time zone 'America/New_York'
        )::integer as target_month,

        (
            extract(
                isodow from observed_at
                at time zone 'America/New_York'
            ) in (6, 7)
        ) as is_weekend

    from {{ ref('int_eia_demand_hourly') }}

),

forecast_weather as (

    select
        valid_at,

        mean_temperature_forecast_48h,
        min_temperature_forecast_48h,
        max_temperature_forecast_48h,

        mean_humidity_forecast_48h,
        mean_dew_point_forecast_48h,
        mean_apparent_temperature_forecast_48h,

        mean_precipitation_forecast_48h,
        mean_wind_speed_forecast_48h

    from {{ ref('int_weather_forecast_regional_hourly') }}

),

joined as (

    select
        demand.*,

        weather.mean_temperature_forecast_48h,
        weather.min_temperature_forecast_48h,
        weather.max_temperature_forecast_48h,

        weather.max_temperature_forecast_48h
            - weather.min_temperature_forecast_48h
            as temperature_range_forecast_48h,

        weather.mean_humidity_forecast_48h,
        weather.mean_dew_point_forecast_48h,
        weather.mean_apparent_temperature_forecast_48h,

        weather.mean_precipitation_forecast_48h,
        weather.mean_wind_speed_forecast_48h,

        greatest(
            weather.mean_temperature_forecast_48h - 18.0,
            0
        ) as cooling_degree_feature,

        greatest(
            18.0 - weather.mean_temperature_forecast_48h,
            0
        ) as heating_degree_feature

    from demand_features as demand

    left join forecast_weather as weather
        on demand.target_at = weather.valid_at

),

calendar as (

    select
        target_at,
        is_holiday,
        is_day_before_holiday,
        is_day_after_holiday

    from {{ ref('int_calendar_hourly') }}
    

)

select
    joined.*,
    calendar.is_holiday,
    calendar.is_day_before_holiday,
    calendar.is_day_after_holiday
from joined
left join calendar
    on joined.target_at = calendar.target_at
where joined.target_at >= '2024-01-20 12:00:00+00'
  and joined.target_at <  '2026-01-01 00:00:00+00'