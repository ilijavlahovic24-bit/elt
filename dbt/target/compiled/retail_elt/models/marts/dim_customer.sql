-- dbt/models/marts/dim_customer.sql
-- One row per customer. Our source only carries customer_id + region,
-- so that's all we can populate - but the shape is correct for the star schema.
-- In production this would join a customers table for name/address/etc.

with customers as (
    select distinct
        customer_id,
        region   -- one "home region" per customer in our data
    from "retail"."main_staging"."stg_orders"
),

final as (
    select
        -- surrogate key: stable across runs (md5 of natural key)
        md5(cast(customer_id as varchar)) as customer_sk,
        customer_id,
        region
    from customers
)

select * from final