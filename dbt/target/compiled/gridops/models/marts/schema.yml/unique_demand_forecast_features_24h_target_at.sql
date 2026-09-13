
    
    

select
    target_at as unique_field,
    count(*) as n_records

from "gridops"."marts"."demand_forecast_features_24h"
where target_at is not null
group by target_at
having count(*) > 1


