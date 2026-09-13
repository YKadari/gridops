with historical_demand as (

    select
        observed_at,
        respondent,
        respondent_name,
        data_type,
        type_name,
        demand_value,
        value_units,
        ingested_at

    from "gridops"."staging"."stg_eia_demand"

    where observed_at >= '2023-01-01 00:00:00+00'
      and observed_at <  '2026-01-01 00:00:00+00'

),

hourly_spine as (

    select
        generate_series(
            '2023-01-01 00:00:00+00'::timestamptz,
            '2025-12-31 23:00:00+00'::timestamptz,
            interval '1 hour'
        ) as observed_at

),

joined as (

    select
        spine.observed_at,

        demand.respondent,
        demand.respondent_name,
        demand.data_type,
        demand.type_name,
        demand.demand_value,
        demand.value_units,
        demand.ingested_at,

        demand.observed_at is null
            as is_missing_source_row,

        demand.demand_value is null
            as is_missing_demand

    from hourly_spine as spine

    left join historical_demand as demand
        on spine.observed_at = demand.observed_at

)

select *
from joined