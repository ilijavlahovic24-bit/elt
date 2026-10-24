# warehouse/load_to_duckdb.py
"""
Load raw Parquet partitions into DuckDB as raw.orders.
Warehouse layer: 'load raw data into a queryable warehouse'.
Deliberately dumb: no transforms, just land.
"""
from pathlib import Path
import duckdb

DB_PATH = "data/warehouse/retail.duckdb"
RAW_GLOB = "data/raw/orders/date=*/orders.parquet"


def main() -> None:
    Path("data/warehouse").mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(DB_PATH)

    # DuckDB does NOT auto-create schemas. Must create `raw` explicitly.
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    # hive_partitioning=true extracts `date=YYYY-MM-DD` from folder names
    # as a real `date` column. No parse_filename() needed.
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.orders AS
        SELECT * EXCLUDE (filename)
        FROM read_parquet('{RAW_GLOB}', filename=true, hive_partitioning=true)
        QUALIFY row_number() OVER (PARTITION BY order_id ORDER BY date DESC) = 1
    """)

    n = con.execute("SELECT count(*) FROM raw.orders").fetchone()[0]
    print(f"raw.orders loaded: {n} rows")
    print(f"DB file: {Path(DB_PATH).resolve()}")
    con.close()


if __name__ == "__main__":
    main()