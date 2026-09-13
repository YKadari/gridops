
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select weather_location_count
from "gridops"."intermediate"."int_weather_regional_hourly"
where weather_location_count is null



  
  
      
    ) dbt_internal_test