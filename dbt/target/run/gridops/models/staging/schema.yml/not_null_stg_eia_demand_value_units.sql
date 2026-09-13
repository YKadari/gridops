
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select value_units
from "gridops"."staging"."stg_eia_demand"
where value_units is null



  
  
      
    ) dbt_internal_test