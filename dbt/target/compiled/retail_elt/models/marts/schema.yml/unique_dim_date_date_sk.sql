
    
    

select
    date_sk as unique_field,
    count(*) as n_records

from "retail"."main_marts"."dim_date"
where date_sk is not null
group by date_sk
having count(*) > 1


