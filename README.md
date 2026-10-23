# ELT: Retail Sales ELT Pipeline

## Status: Active Development

## Objective
Build a complete ELT pipeline that ingests raw sales data, loads it into a warehouse, transforms it into a star schema with dbt, 
orchestrates the entire flow with Airflow, and enforces data quality at every stage. 
The output is a queryable analytics table and a simple dashboard.


## Getting started
Following commands
```
# 1. INGESTION — CSV -> Parquet u data/raw/
python ingestion\extract_orders.py

# 2. LOAD — Parquet -> raw.orders tabela u DuckDB
python warehouse\load_to_duckdb.py

# 3. TRANSFORM — dbt staging model
cd dbt
dbt run

# 4. TEST — 7 generic tests
dbt test

# 5. Back to root
cd ..
```

## Project structure
