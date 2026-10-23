-- dbt/models/marts/fct_orders.sql
-- One row per order. Measures + surrogate FKs to dimensions.
-- grain: one order_id per row (matches our CSV; multi-line orders would change grain).

with orders as (
    select * from "retail"."main_staging"."stg_orders"
),

customers as (
    select customer_sk, customer_id from "retail"."main_marts"."dim_customer"
),

products as (
    select product_sk, product_id from "retail"."main_marts"."dim_product"
),

dates as (
    select date_sk, date_day from "retail"."main_marts"."dim_date"
),

final as (
    select
        -- degenerate dimension: business key kept in fact for traceability
        o.order_id,

        -- surrogate foreign keys
        c.customer_sk,
        p.product_sk,
        d.date_sk,

        -- measures
        o.quantity,
        o.unit_price,
        o.quantity * o.unit_price as gross_amount

    from orders o
    left join customers c on o.customer_id = c.customer_id
    left join products  p on o.product_id  = p.product_id
    left join dates     d on o.order_date  = d.date_day
)

select * from final