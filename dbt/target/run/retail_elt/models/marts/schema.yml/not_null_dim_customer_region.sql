
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select region
from "retail"."main_marts"."dim_customer"
where region is null



  
  
      
    ) dbt_internal_test