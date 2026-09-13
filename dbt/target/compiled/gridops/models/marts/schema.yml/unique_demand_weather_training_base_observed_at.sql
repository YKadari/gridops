
    
    

select
    observed_at as unique_field,
    count(*) as n_records

from "gridops"."marts"."demand_weather_training_base"
where observed_at is not null
group by observed_at
having count(*) > 1


