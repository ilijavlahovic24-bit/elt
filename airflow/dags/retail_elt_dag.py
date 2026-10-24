# airflow/dags/retail_elt_dag.py
"""
Orchestrates the retail ELT pipeline:
  extract -> load -> dbt run -> dbt test

Why orchestrate: manual runs skip steps (as we saw - forgot `load` once).
Airflow makes the order explicit and un-skippable: dbt_run depends on load,
load depends on extract. If one fails, downstream is skipped, not run blind.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"

default_args = {
    "owner": "you",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
}

with DAG(
    dag_id="retail_elt",
    description="Retail ELT: CSV -> Parquet -> DuckDB -> dbt marts",
    start_date=datetime(2026, 10, 1),
    schedule="0 6 * * *",     # every day at 06:00
    catchup=False,            # don't backfill 1 month on first load
    default_args=default_args,
    tags=["retail", "elt"],
    max_active_runs=1,        # prevent overlapping DAG runs
) as dag:

    extract = BashOperator(
        task_id="extract_orders",
        bash_command=f"cd {PROJECT_DIR} && python ingestion/extract_orders.py",
        # {{ ds }} = execution date as YYYY-MM-DD, passed to the script.
        # Why: backfill & retry must land data for the *scheduled* date,
        # not "today" - otherwise the pipeline is not idempotent.
        env={"RUN_DATE": "{{ ds }}"},
    )

    load = BashOperator(
        task_id="load_to_duckdb",
        bash_command=f"cd {PROJECT_DIR} && python warehouse/load_to_duckdb.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {PROJECT_DIR}/dbt && dbt run --no-partial-parse",
        # --no-partial-parse: avoid stale manifest issues when dbt is invoked
        # from different tasks in the same container.
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {PROJECT_DIR}/dbt && dbt test --no-partial-parse",
        # Quality gate: if any test fails, the DAG stops here.
        # Downstream "publish" tasks (dashboard refresh, exports) would be
        # skipped, so bad data never reaches consumers.
    )

    extract >> load >> dbt_run >> dbt_test