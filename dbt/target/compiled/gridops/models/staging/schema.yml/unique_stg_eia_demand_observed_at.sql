
    
    

select
    observed_at as unique_field,
    count(*) as n_records

from "gridops"."staging"."stg_eia_demand"
where observed_at is not null
group by observed_at
having count(*) > 1


