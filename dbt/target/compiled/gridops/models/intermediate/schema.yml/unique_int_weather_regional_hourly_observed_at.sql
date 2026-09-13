
    
    

select
    observed_at as unique_field,
    count(*) as n_records

from "gridops"."intermediate"."int_weather_regional_hourly"
where observed_at is not null
group by observed_at
having count(*) > 1


