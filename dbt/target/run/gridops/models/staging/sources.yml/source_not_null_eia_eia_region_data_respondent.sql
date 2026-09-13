
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select respondent
from "gridops"."raw"."eia_region_data"
where respondent is null



  
  
      
    ) dbt_internal_test