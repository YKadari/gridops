
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select max_temperature_2m
from "gridops"."intermediate"."int_weather_regional_hourly"
where max_temperature_2m is null



  
  
      
    ) dbt_internal_test