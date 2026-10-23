
    
    

select
    product_sk as unique_field,
    count(*) as n_records

from "retail"."main_marts"."dim_product"
where product_sk is not null
group by product_sk
having count(*) > 1


