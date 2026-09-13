
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select min_temperature_2m
from "gridops"."intermediate"."int_weather_regional_hourly"
where min_temperature_2m is null



  
  
      
    ) dbt_internal_test