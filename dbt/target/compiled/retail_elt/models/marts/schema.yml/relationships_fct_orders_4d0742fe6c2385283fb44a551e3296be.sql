
    
    

with child as (
    select product_sk as from_field
    from "retail"."main_marts"."fct_orders"
    where product_sk is not null
),

parent as (
    select product_sk as to_field
    from "retail"."main_marts"."dim_product"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


