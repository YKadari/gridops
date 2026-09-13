
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select mean_relative_humidity_2m
from "gridops"."intermediate"."int_weather_regional_hourly"
where mean_relative_humidity_2m is null



  
  
      
    ) dbt_internal_test