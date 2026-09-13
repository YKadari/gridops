
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select mean_humidity_forecast_24h
from "gridops"."marts"."demand_forecast_features_24h"
where mean_humidity_forecast_24h is null



  
  
      
    ) dbt_internal_test