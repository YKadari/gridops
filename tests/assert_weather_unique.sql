select
    observed_at,
    location_id,
    count(*) as record_count

from {{ ref('stg_weather_hourly') }}

group by
    observed_at,
    location_id

having count(*) > 1