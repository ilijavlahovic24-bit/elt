
    
    

with child as (
    select customer_sk as from_field
    from "retail"."main_marts"."fct_orders"
    where customer_sk is not null
),

parent as (
    select customer_sk as to_field
    from "retail"."main_marts"."dim_customer"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


