
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select observed_at
from "gridops"."intermediate"."int_eia_demand_hourly"
where observed_at is null



  
  
      
    ) dbt_internal_test