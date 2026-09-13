
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select valid_at
from "gridops"."raw"."weather_forecast_hourly"
where valid_at is null



  
  
      
    ) dbt_internal_test