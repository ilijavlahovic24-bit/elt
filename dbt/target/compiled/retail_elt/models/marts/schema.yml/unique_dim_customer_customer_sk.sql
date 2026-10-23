
    
    

select
    customer_sk as unique_field,
    count(*) as n_records

from "retail"."main_marts"."dim_customer"
where customer_sk is not null
group by customer_sk
having count(*) > 1


