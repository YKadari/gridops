
  create view "gridops"."marts"."demand_forecast_features_24h__dbt_tmp"
    
    
  as (
    with demand_features as (

    select
        observed_at as target_at,

        -- Prediction target
        demand_value as target_demand,

        -- Known historical demand at forecast time
        lag(demand_value, 26) over (
            order by observed_at
        ) as demand_lag_26h,

        lag(demand_value, 48) over (
            order by observed_at
        ) as demand_lag_48h,

        lag(demand_value, 168) over (
            order by observed_at
        ) as demand_lag_168h,

        lag(demand_value, 336) over (
            order by observed_at
        ) as demand_lag_336h,

        -- Last 24 known demand observations,
        -- ending at t - 24h.
        avg(demand_value) over (
            order by observed_at
            rows between 49 preceding and 26 preceding
        ) as demand_rolling_mean_24h,

        -- Last 7 days known at forecast time,
        -- also ending at t - 24h.
        avg(demand_value) over (
            order by observed_at
            rows between 193 preceding and 26 preceding
        ) as demand_rolling_mean_168h,

        count(demand_value) over (
            order by observed_at
            rows between 49 preceding and 26 preceding
        ) as demand_history_count_24h,

        count(demand_value) over (
            order by observed_at
            rows between 193 preceding and 26 preceding
        ) as demand_history_count_168h,

        -- Calendar information for the TARGET hour.
        -- We use PJM/Eastern local time rather than UTC.
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

    from "gridops"."intermediate"."int_eia_demand_hourly"

),

forecast_weather as (

    select
        valid_at,

        mean_temperature_forecast_24h,
        min_temperature_forecast_24h,
        max_temperature_forecast_24h,

        mean_humidity_forecast_24h,
        mean_dew_point_forecast_24h,
        mean_apparent_temperature_forecast_24h,

        mean_precipitation_forecast_24h,
        mean_wind_speed_forecast_24h

    from "gridops"."intermediate"."int_weather_forecast_regional_hourly"

),

joined as (

    select
        demand.*,

        weather.mean_temperature_forecast_24h,
        weather.min_temperature_forecast_24h,
        weather.max_temperature_forecast_24h,

        weather.max_temperature_forecast_24h
            - weather.min_temperature_forecast_24h
            as temperature_range_forecast_24h,

        weather.mean_humidity_forecast_24h,
        weather.mean_dew_point_forecast_24h,
        weather.mean_apparent_temperature_forecast_24h,

        weather.mean_precipitation_forecast_24h,
        weather.mean_wind_speed_forecast_24h,

        greatest(
            weather.mean_temperature_forecast_24h - 18.0,
            0
        ) as cooling_degree_feature,

        greatest(
            18.0 - weather.mean_temperature_forecast_24h,
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

    from "gridops"."intermediate"."int_calendar_hourly"

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
  );