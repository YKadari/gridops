
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select target_day_of_week
from "gridops"."marts"."demand_forecast_features_48h"
where target_day_of_week is null



  
  
      
    ) dbt_internal_test