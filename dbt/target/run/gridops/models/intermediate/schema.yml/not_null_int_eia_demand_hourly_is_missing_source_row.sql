
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select is_missing_source_row
from "gridops"."intermediate"."int_eia_demand_hourly"
where is_missing_source_row is null



  
  
      
    ) dbt_internal_test