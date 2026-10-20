"""
Ingestion: pull raw orders, land them as Parquet in the raw zone.

Design principles:
  1. Land first, trust later - no business logic here, only typing.
  2. Idempotent - re-running today overwrites today's partition.
  3. Schema contract enforced - drift halts the pipeline.
  4. Atomic write - temp file + rename, never half-written parquet.
"""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Config
# -------------------------------------------------------------------------
RAW_DIR = Path("data/raw/orders")
SOURCE_CSV = Path("data/source/orders.csv")   # in real life: an API

# Schema contract. Key = column, value = expected dtype.
# Adding a column to this dict is a *deliberate* act, not an accident.
EXPECTED_SCHEMA: dict[str, str] = {
    "order_id":    "int64",
    "customer_id": "int64",
    "product_id":  "string",
    "quantity":    "int64",
    "unit_price":  "float64",
    "order_date":  "datetime64[ns]",
    "region":      "string",
}

# Volume sanity: accept 80%..120% of yesterday's row count.
VOLUME_MIN = 0.8
VOLUME_MAX = 1.2


# -------------------------------------------------------------------------
# 1. Extract
# -------------------------------------------------------------------------
def extract_from_csv(path: Path, chunk_size: int = 10_000) -> pd.DataFrame:
    """
    Read CSV in chunks to mimic paginated API behaviour.

    Why chunks? Real APIs return data page-by-page; you must loop until
    exhausted. This mirrors that pattern so the code is easy to port.
    For big CSVs it also avoids loading everything into memory at once
    (here we eventually concatenate, but the pattern is there).
    """
    log.info("Reading source: %s", path)
    chunks = []
    for i, chunk in enumerate(pd.read_csv(path, chunksize=chunk_size)):
        log.info("  chunk %d: %d rows", i, len(chunk))
        chunks.append(chunk)
    df = pd.concat(chunks, ignore_index=True)
    log.info("Extracted %d rows total", len(df))
    return df


def extract_from_api_paginated(base_url: str, page_size: int = 100) -> pd.DataFrame:
    """
    Real API pagination - kept as a reference, not called by default.

    Why this matters on interview: APIs never return *all* data in one call.
    Without a loop over pages you'd land only page 1 and think it's complete.
    """
    import requests
    frames = []
    skip = 0
    while True:
        r = requests.get(base_url, params={"limit": page_size, "skip": skip}, timeout=30)
        r.raise_for_status()
        payload = r.json()
        rows = payload.get("carts", [])
        if not rows:
            break
        frames.append(pd.DataFrame(rows))
        skip += page_size
        if skip >= payload.get("total", 0):
            break
    return pd.concat(frames, ignore_index=True)


# -------------------------------------------------------------------------
# 2. Schema drift check
# -------------------------------------------------------------------------
def check_schema(df: pd.DataFrame) -> None:
    """
    Compare incoming schema against the contract.

    Three outcomes:
      - OK              -> proceed
      - backward compat -> log a warning, proceed (new columns are benign)
      - breaking        -> raise, halt the pipeline (missing/renamed columns)
    """
    expected_cols = set(EXPECTED_SCHEMA.keys())
    actual_cols   = set(df.columns)

    missing = expected_cols - actual_cols
    extra   = actual_cols   - expected_cols

    if missing:
        # Breaking: we lost data we rely on.
        raise ValueError(f"Schema drift (breaking): missing columns {sorted(missing)}")

    if extra:
        # Backward compatible: new columns won't hurt downstream dbt models.
        log.warning("Schema drift (compatible): extra columns %s", sorted(extra))

    # Type drift check on columns we do expect.
    for col in expected_cols & actual_cols:
        expected_dtype = EXPECTED_SCHEMA[col]
        actual_dtype = str(df[col].dtype)
        if actual_dtype != expected_dtype:
            raise ValueError(
                f"Schema drift (type): column '{col}' expected {expected_dtype}, got {actual_dtype}"
            )


# -------------------------------------------------------------------------
# 3. Volume check
# -------------------------------------------------------------------------
def check_volume(df: pd.DataFrame, run_date: date) -> None:
    """
    Sanity: today's row count must be 80%..120% of yesterday's.
    First run has no baseline - skip.
    """
    yesterday = run_date.replace(day=run_date.day - 1) if run_date.day > 1 else None
    if yesterday is None:
        log.info("Volume check skipped (no baseline)")
        return

    y_path = RAW_DIR / f"date={yesterday.isoformat()}" / "orders.parquet"
    if not y_path.exists():
        log.info("Volume check skipped (no baseline file)")
        return

    y_rows = pq.read_metadata(y_path).num_rows
    today_rows = len(df)
    ratio = today_rows / y_rows if y_rows else 0
    log.info("Volume: yesterday=%d today=%d ratio=%.2f", y_rows, today_rows, ratio)

    if not (VOLUME_MIN <= ratio <= VOLUME_MAX):
        raise ValueError(
            f"Volume anomaly: {today_rows} rows vs yesterday {y_rows} (ratio {ratio:.2f})"
        )


# -------------------------------------------------------------------------
# 4. Atomic write to partition
# -------------------------------------------------------------------------
def write_partition(df: pd.DataFrame, run_date: date) -> Path:
    """
    Write df to data/raw/orders/date=YYYY-MM-DD/orders.parquet atomically.

    Why atomic: a crash mid-write would leave a corrupt parquet file that
    dbt would later try to read. We write to .tmp and rename - rename is
    atomic on POSIX, so either the file is complete or absent, never partial.
    """
    partition = RAW_DIR / f"date={run_date.isoformat()}"
    partition.mkdir(parents=True, exist_ok=True)
    target = partition / "orders.parquet"
    tmp = target.with_suffix(".parquet.tmp")

    # Cast to declared schema before writing (Parquet requires types).
    for col, dtype in EXPECTED_SCHEMA.items():
        df[col] = df[col].astype(dtype)

    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), tmp)
    os.replace(tmp, target)   # atomic on POSIX
    log.info("Wrote %d rows to %s", len(df), target)
    return target


# -------------------------------------------------------------------------
# 5. Entrypoint
# -------------------------------------------------------------------------
def main(run_date: date | None = None) -> None:
    run_date = run_date or datetime.now(timezone.utc).date()

    df = extract_from_csv(SOURCE_CSV)
    check_schema(df)       # fail-fast on drift
    check_volume(df, run_date)  # fail-fast on anomaly
    write_partition(df, run_date)


if __name__ == "__main__":
    main()