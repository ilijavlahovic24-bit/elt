# scripts/check_db.py
r"""Quick sanity check on the DuckDB file. Run from D:\Luminix\ELT."""
import duckdb

con = duckdb.connect("data/warehouse/retail.duckdb")

# Use information_schema (standard SQL) instead of SHOW SCHEMAS
# because SHOW SCHEMAS returns 3 columns in DuckDB 1.5.6, and its shape
# is version-dependent. information_schema.schemata is portable across engines.
print("Schemas:")
for (s,) in con.execute(
    "SELECT schema_name FROM information_schema.schemata ORDER BY schema_name"
).fetchall():
    print(f"  {s}")

for schema in ("raw", "main_staging", "main_marts"):
    try:
        tables = con.execute(f"SHOW TABLES FROM {schema}").fetchall()
        print(f"\nTables in {schema}: {[t[0] for t in tables]}")
    except Exception as e:
        print(f"\nTables in {schema}: <schema missing: {e}>")

print(
    "\nfct_orders row count:",
    con.execute("SELECT count(*) FROM main_marts.fct_orders").fetchone()[0],
)

print("\nSales by region (sanity check):")
rows = con.execute("""
    SELECT c.region, SUM(f.gross_amount) AS total
    FROM main_marts.fct_orders f
    JOIN main_marts.dim_customer c ON f.customer_sk = c.customer_sk
    GROUP BY c.region
    ORDER BY c.region
""").fetchall()
for region, total in rows:
    print(f"  {region}: {total:.2f}")

con.close()