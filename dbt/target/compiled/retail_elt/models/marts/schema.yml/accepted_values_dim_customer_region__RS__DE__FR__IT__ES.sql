
    
    

with all_values as (

    select
        region as value_field,
        count(*) as n_records

    from "retail"."main_marts"."dim_customer"
    group by region

)

select *
from all_values
where value_field not in (
    'RS','DE','FR','IT','ES'
)


