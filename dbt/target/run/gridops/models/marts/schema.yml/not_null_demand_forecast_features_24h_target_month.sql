
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select target_month
from "gridops"."marts"."demand_forecast_features_24h"
where target_month is null



  
  
      
    ) dbt_internal_test