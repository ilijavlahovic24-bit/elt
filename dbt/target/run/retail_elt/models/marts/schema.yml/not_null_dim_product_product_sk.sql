
    
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select product_sk
from "retail"."main_marts"."dim_product"
where product_sk is null



  
  
      
    ) dbt_internal_test