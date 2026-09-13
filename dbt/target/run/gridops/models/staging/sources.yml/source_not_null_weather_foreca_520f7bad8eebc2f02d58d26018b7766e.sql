
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select location_name
from "gridops"."raw"."weather_forecast_hourly"
where location_name is null



  
  
      
    ) dbt_internal_test