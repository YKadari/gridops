
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select mean_temperature_forecast_48h
from "gridops"."marts"."demand_forecast_features_48h"
where mean_temperature_forecast_48h is null



  
  
      
    ) dbt_internal_test