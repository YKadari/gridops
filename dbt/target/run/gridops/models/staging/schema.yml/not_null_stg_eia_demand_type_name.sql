
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select type_name
from "gridops"."staging"."stg_eia_demand"
where type_name is null



  
  
      
    ) dbt_internal_test