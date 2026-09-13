
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select respondent_name
from "gridops"."staging"."stg_eia_demand"
where respondent_name is null



  
  
      
    ) dbt_internal_test