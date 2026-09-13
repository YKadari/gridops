
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select mean_relative_humidity_2m
from "gridops"."marts"."demand_weather_training_base"
where mean_relative_humidity_2m is null



  
  
      
    ) dbt_internal_test