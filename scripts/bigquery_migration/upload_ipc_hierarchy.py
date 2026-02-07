#!/usr/bin/env python3
"""
Upload IPC Hierarchy to BigQuery.

Reads the IPC classification hierarchy from SQLite and uploads it to BigQuery
as the `tls_ipc_hierarchy` reference table, enabling JOINs to PATSTAT tables.

Usage:
    python upload_ipc_hierarchy.py /path/to/patent-classification-2025.db
    python upload_ipc_hierarchy.py /path/to/patent-classification-2025.db --dry-run

Prerequisites:
    pip install google-cloud-bigquery python-dotenv
    Service account JSON in .env as GOOGLE_APPLICATION_CREDENTIALS_JSON
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery
from google.oauth2 import service_account


def get_bigquery_client(project_id: str) -> bigquery.Client:
    """Create BigQuery client using gcloud default credentials or service account from .env."""
    import google.auth

    # Try gcloud default credentials first (has write access after `gcloud auth application-default login`)
    try:
        credentials, _ = google.auth.default()
        print("  Using gcloud application-default credentials")
        return bigquery.Client(project=project_id, credentials=credentials)
    except google.auth.exceptions.DefaultCredentialsError:
        pass

    # Fall back to service account from .env (read-only)
    project_root = Path(__file__).parent.parent.parent
    load_dotenv(project_root / ".env")

    creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if not creds_json:
        raise ValueError(
            "No credentials found. Run `gcloud auth application-default login` "
            "or add GOOGLE_APPLICATION_CREDENTIALS_JSON to .env"
        )

    creds_info = json.loads(creds_json)
    credentials = service_account.Credentials.from_service_account_info(creds_info)
    print("  Using service account from .env")

    return bigquery.Client(project=project_id, credentials=credentials)

# BigQuery target
PROJECT_ID = "patstat-mtc"
DATASET_ID = "patstat"
TABLE_ID = f"{PROJECT_ID}.{DATASET_ID}.tls_ipc_hierarchy"

# Schema for the target table
SCHEMA = [
    bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("symbol_short", "STRING"),
    bigquery.SchemaField("symbol_patstat", "STRING"),
    bigquery.SchemaField("kind", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("level", "INT64", mode="REQUIRED"),
    bigquery.SchemaField("parent", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("parent_short", "STRING"),
    bigquery.SchemaField("title_en", "STRING"),
    bigquery.SchemaField("title_full", "STRING"),
    bigquery.SchemaField("size", "INT64"),
    bigquery.SchemaField("size_percent", "FLOAT64"),
]


# =============================================================================
# Symbol Format Conversion Functions
# =============================================================================

def zeropad_to_patstat(zeropad: str) -> str:
    """Convert zero-padded symbol to PATSTAT space-padded format.

    Example: 'A23L0007117000' -> 'A23L   7/117'

    Rules:
    - Chars [0:4]  = subclass (pass through)
    - Chars [4:8]  = group (zero-padded -> int -> right-justify in 4-char field)
    - Chars [8:14] = subgroup (strip trailing zeros; '000000' -> '00' for main groups)
    """
    if len(zeropad) < 14:
        return None  # section/class/subclass level, no PATSTAT format

    subclass = zeropad[:4]
    group_int = int(zeropad[4:8])
    subgroup_raw = zeropad[8:14]

    subgroup_str = subgroup_raw.rstrip('0') or '00'
    group_padded = str(group_int).rjust(4)

    return f"{subclass}{group_padded}/{subgroup_str}"


def patstat_to_zeropad(patstat: str) -> str:
    """Convert PATSTAT space-padded format to zero-padded symbol.

    Example: 'A23L   7/117' -> 'A23L0007117000'
    """
    if '/' not in patstat:
        return patstat

    slash_pos = patstat.index('/')
    subclass = patstat[:4]
    group_str = patstat[4:slash_pos].strip()
    subgroup_str = patstat[slash_pos + 1:]

    group_zp = group_str.zfill(4)
    subgroup_zp = subgroup_str.ljust(6, '0')

    return f"{subclass}{group_zp}{subgroup_zp}"


def short_to_patstat(short: str) -> str:
    """Convert short symbol to PATSTAT space-padded format.

    Example: 'A23L7/117' -> 'A23L   7/117'
    """
    if '/' not in short:
        return short

    slash_pos = short.index('/')
    subclass = short[:4]
    group_str = short[4:slash_pos]
    subgroup_str = short[slash_pos + 1:]

    group_padded = group_str.rjust(4)

    return f"{subclass}{group_padded}/{subgroup_str}"


def patstat_to_short(patstat: str) -> str:
    """Convert PATSTAT space-padded format to short symbol.

    Example: 'A23L   7/117' -> 'A23L7/117'
    """
    if '/' not in patstat:
        return patstat

    slash_pos = patstat.index('/')
    subclass = patstat[:4]
    group_str = patstat[4:slash_pos].strip()
    subgroup_str = patstat[slash_pos + 1:]

    return f"{subclass}{group_str}/{subgroup_str}"


# =============================================================================
# Title Chain Builder
# =============================================================================

def build_title_full(symbol: str, lookup: dict, from_level: int = 5) -> str:
    """Build concatenated title from main group level (5) downwards.

    Example: 'A01B0001040000' -> 'Hand tools > Spades; Shovels > with teeth'

    Starts at the entry's own level and walks up to from_level,
    collecting titles. Entries at from_level or above return their
    own title_en unchanged.
    """
    chain = []
    current = symbol

    while current in lookup:
        entry = lookup[current]
        if entry["level"] < from_level:
            break
        if entry["title_en"]:
            chain.append(entry["title_en"])
        current = entry["parent"]

    chain.reverse()
    return " > ".join(chain) if chain else lookup.get(symbol, {}).get("title_en", "")


# =============================================================================
# Main Upload Logic
# =============================================================================

def read_sqlite_database(db_path: Path) -> dict:
    """Read all IPC entries from SQLite and return as lookup dict."""
    print(f"Reading SQLite database: {db_path}")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        SELECT symbol, symbol_short, kind, level, parent, parent_short,
               title_en, size, size_percent
        FROM ipc
    """)

    rows = cur.fetchall()
    conn.close()

    print(f"  Loaded {len(rows):,} entries")

    # Build lookup dict
    lookup = {}
    for symbol, symbol_short, kind, level, parent, parent_short, title_en, size, size_pct in rows:
        lookup[symbol] = {
            "symbol_short": symbol_short,
            "kind": kind,
            "level": level,
            "parent": parent,
            "parent_short": parent_short,
            "title_en": title_en,
            "size": size or 0,
            "size_percent": size_pct or 0.0,
        }

    return lookup


def prepare_bigquery_rows(lookup: dict) -> list:
    """Convert lookup dict to list of BigQuery row dicts."""
    print("Preparing rows for BigQuery...")

    bq_rows = []

    for symbol, data in lookup.items():
        # Generate PATSTAT format symbol
        symbol_patstat = zeropad_to_patstat(symbol)

        # Generate full title chain
        title_full = build_title_full(symbol, lookup)

        bq_rows.append({
            "symbol": symbol,
            "symbol_short": data["symbol_short"],
            "symbol_patstat": symbol_patstat,
            "kind": data["kind"],
            "level": data["level"],
            "parent": data["parent"],
            "parent_short": data["parent_short"],
            "title_en": data["title_en"],
            "title_full": title_full,
            "size": data["size"],
            "size_percent": data["size_percent"],
        })

    print(f"  Prepared {len(bq_rows):,} rows")

    # Stats
    with_patstat = sum(1 for r in bq_rows if r["symbol_patstat"])
    with_title_full = sum(1 for r in bq_rows if r["title_full"])
    print(f"  Rows with symbol_patstat: {with_patstat:,}")
    print(f"  Rows with title_full: {with_title_full:,}")

    return bq_rows


def upload_to_bigquery(bq_rows: list, dry_run: bool = False):
    """Upload rows to BigQuery."""
    if dry_run:
        print(f"\n[DRY RUN] Would upload {len(bq_rows):,} rows to {TABLE_ID}")
        print("\nSample rows:")
        for row in bq_rows[:3]:
            print(f"  {row['symbol_short']}: {row['title_en'][:50]}...")
            print(f"    symbol_patstat: {row['symbol_patstat']}")
            print(f"    title_full: {row['title_full'][:80]}...")
        return

    print(f"\nUploading to BigQuery: {TABLE_ID}")

    client = get_bigquery_client(PROJECT_ID)

    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        write_disposition="WRITE_TRUNCATE",
    )

    job = client.load_table_from_json(bq_rows, TABLE_ID, job_config=job_config)
    job.result()  # Wait for completion

    print(f"  Loaded {job.output_rows:,} rows into {TABLE_ID}")
    print("  Done!")


def print_validation_queries():
    """Print validation queries to run after upload."""
    print("\n" + "=" * 60)
    print("VALIDATION QUERIES - Run these in BigQuery Console:")
    print("=" * 60)

    queries = [
        ("Row count (expect 79,833)",
         "SELECT COUNT(*) as cnt FROM `patstat-mtc.patstat.tls_ipc_hierarchy`"),

        ("Level distribution",
         """SELECT level, COUNT(*) as cnt
FROM `patstat-mtc.patstat.tls_ipc_hierarchy`
GROUP BY level ORDER BY level"""),

        ("JOIN test with tls209_appln_ipc",
         """SELECT i.appln_id, i.ipc_class_symbol, h.title_en
FROM `patstat-mtc.patstat.tls209_appln_ipc` i
JOIN `patstat-mtc.patstat.tls_ipc_hierarchy` h
  ON i.ipc_class_symbol = h.symbol_patstat
WHERE i.ipc_value = 'I' AND i.ipc_position = 'F'
LIMIT 5"""),

        ("title_full verification",
         """SELECT symbol_short, title_en, title_full
FROM `patstat-mtc.patstat.tls_ipc_hierarchy`
WHERE level >= 6
LIMIT 5"""),
    ]

    for name, sql in queries:
        print(f"\n-- {name}")
        print(sql)


def main():
    parser = argparse.ArgumentParser(
        description="Upload IPC hierarchy from SQLite to BigQuery"
    )
    parser.add_argument(
        "db_path",
        type=Path,
        help="Path to patent-classification-2025.db"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without uploading"
    )

    args = parser.parse_args()

    if not args.db_path.exists():
        print(f"Error: Database not found: {args.db_path}")
        sys.exit(1)

    # Read SQLite
    lookup = read_sqlite_database(args.db_path)

    # Prepare rows
    bq_rows = prepare_bigquery_rows(lookup)

    # Upload
    upload_to_bigquery(bq_rows, dry_run=args.dry_run)

    # Print validation queries
    print_validation_queries()


if __name__ == "__main__":
    main()
