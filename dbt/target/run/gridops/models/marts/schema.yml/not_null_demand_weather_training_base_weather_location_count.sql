
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select weather_location_count
from "gridops"."marts"."demand_weather_training_base"
where weather_location_count is null



  
  
      
    ) dbt_internal_test