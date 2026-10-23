-- dbt/models/marts/dim_product.sql
-- One row per product. Source has only product_id - no name/category.
-- Still a valid dimension: the star schema shape matters more than attribute richness.

with products as (
    select distinct product_id
    from "retail"."main_staging"."stg_orders"
),

final as (
    select
        md5(product_id) as product_sk,
        product_id
    from products
)

select * from final