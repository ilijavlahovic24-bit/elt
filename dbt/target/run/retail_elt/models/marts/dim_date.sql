
    

    create  table
      "retail"."main_marts"."dim_date__dbt_tmp"
  
    
    as (
      -- dbt/models/marts/dim_date.sql
-- One row per calendar date in the range covered by orders.
-- Why: GROUP BY order_date skips days with zero orders; a date spine fills gaps.
-- Also: pre-computed year/month/quarter attributes so BI tools don't recalculate.

with date_bounds as (
    select
        min(order_date) as min_date,
        max(order_date) as max_date
    from "retail"."main_staging"."stg_orders"
),

date_spine as (
    -- DuckDB: generate_series over dates
    select
        cast(unnest(generate_series(min_date, max_date, interval 1 day)) as date) as date_day
    from date_bounds
),

final as (
    select
        -- surrogate key: deterministic hash of the natural key (date)
        md5(cast(date_day as varchar)) as date_sk,
        date_day,
        extract(year    from date_day) as year,
        extract(quarter from date_day) as quarter,
        extract(month   from date_day) as month,
        strftime(date_day, '%B')       as month_name,
        extract(day     from date_day) as day_of_month,
        extract(dow     from date_day) as day_of_week,   -- 0=Sunday..6=Saturday
        case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
    from date_spine
)

select * from final
    );
    
  