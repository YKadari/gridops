
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select period
from "gridops"."raw"."eia_region_data"
where period is null



  
  
      
    ) dbt_internal_test