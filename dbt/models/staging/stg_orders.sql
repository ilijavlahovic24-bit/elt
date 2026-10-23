-- dbt/models/staging/stg_orders.sql
-- Staging: 1:1 with raw.orders. Rename + cast only.
-- NO filtering. NO joins. NO aggregation. Those belong in marts.

with source as (
    select * from {{ source('raw', 'orders') }}
),

renamed as (
    select
        -- identifiers: keep as-is, they're already typed
        order_id,
        customer_id,
        product_id,

        -- measures: keep as-is
        quantity,
        unit_price,

        -- dates: cast to date. Raw may arrive as timestamp; business
        -- questions are day-level ("sales by day"), so truncate here.
        cast(order_date as date) as order_date,

        -- dimensions: keep as-is, trimming is safe
        trim(region) as region

    from source
)

select * from renamed