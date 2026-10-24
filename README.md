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

Airflow (Docker) — Orchestration
```
cd airflow

# Booting the entire Airflow environment (for the first time, or when changing the Dockerfile)
docker compose up -d --build

# Boot without rebuild (when only Python files within the project are changed)
docker compose up -d

# Extinguishing and cleaning the container (used when something gets stuck)
docker compose down --remove-orphans

# Container status check
docker compose ps

# Viewing logs (eg if the webserver won't boot)
docker compose logs airflow-scheduler --tail 50
docker compose logs airflow-webserver --tail 50

# Manually creating an admin user (if the login does not work)
docker compose exec airflow-scheduler airflow users create --role Admin --username admin --password admin --firstname Admin --lastname User --email admin@example.com

# Manually running the DAG from the terminal (without opening the UI)
docker compose exec airflow-scheduler airflow dags trigger retail_elt

cd ..
```

Reset
```
Remove-Item -Recurse -Force data\raw -ErrorAction SilentlyContinue
Remove-Item data\warehouse\retail.duckdb -ErrorAction SilentlyContinue
```

## Project structure
```
retail-elt/
├── README.md
├── docker-compose.yml          # dolazi u Sesiji 5
├── requirements.txt
├── .gitignore
├── data/
│   ├── raw/                    # ignored u git-u
│   └── warehouse/              # duckdb fajl, ignored
├── ingestion/
│   └── extract_orders.py
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── models/
│       ├── staging/
│       └── marts/
├── airflow/
│   └── dags/
│       └── retail_elt_dag.py
└── tests/
    └── quality_checks.sql
```