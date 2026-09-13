
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select is_missing_demand
from "gridops"."marts"."demand_weather_training_base"
where is_missing_demand is null



  
  
      
    ) dbt_internal_test