
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select mean_temperature_2m
from "gridops"."marts"."demand_weather_training_base"
where mean_temperature_2m is null



  
  
      
    ) dbt_internal_test