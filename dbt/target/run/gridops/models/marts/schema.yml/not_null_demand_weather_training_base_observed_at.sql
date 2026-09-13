
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select observed_at
from "gridops"."marts"."demand_weather_training_base"
where observed_at is null



  
  
      
    ) dbt_internal_test