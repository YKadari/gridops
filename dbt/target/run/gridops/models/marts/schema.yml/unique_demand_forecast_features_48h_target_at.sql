
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    

select
    target_at as unique_field,
    count(*) as n_records

from "gridops"."marts"."demand_forecast_features_48h"
where target_at is not null
group by target_at
having count(*) > 1



  
  
      
    ) dbt_internal_test