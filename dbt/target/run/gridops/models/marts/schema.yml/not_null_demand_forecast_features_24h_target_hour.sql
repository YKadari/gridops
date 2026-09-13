
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select target_hour
from "gridops"."marts"."demand_forecast_features_24h"
where target_hour is null



  
  
      
    ) dbt_internal_test