select
    period as observed_at,
    respondent,
    respondent_name,
    data_type,
    type_name,
    value as demand_value,
    value_units,
    ingested_at

from {{ source('eia', 'eia_region_data') }}

where respondent = 'PJM'
  and data_type = 'D'