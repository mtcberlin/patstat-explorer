#!/usr/bin/env python3
"""
Upload IPC 2026.01 Tables to BigQuery.

Reads the enriched IPC classification database from SQLite and uploads
4 tables to BigQuery for use with PATSTAT:

  1. tls_ipc_hierarchy   — core hierarchy (80K rows)
  2. tls_ipc_catchword   — keyword search index (21K rows)
  3. tls_ipc_concordance  — version change tracking (1.2K rows)
  4. tls_ipc_everused     — all historical symbols (93K rows)

Usage:
    python upload_ipc_hierarchy.py /path/to/patent-classification-2026.db
    python upload_ipc_hierarchy.py /path/to/patent-classification-2026.db --dry-run
    python upload_ipc_hierarchy.py /path/to/patent-classification-2026.db --table hierarchy
    python upload_ipc_hierarchy.py /path/to/patent-classification-2026.db --table catchword

Prerequisites:
    pip install google-cloud-bigquery python-dotenv
    gcloud auth application-default login  (for write access)
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


# BigQuery target
PROJECT_ID = "patstat-mtc"
DATASET_ID = "patstat"

TABLE_HIERARCHY = f"{PROJECT_ID}.{DATASET_ID}.tls_ipc_hierarchy"
TABLE_CATCHWORD = f"{PROJECT_ID}.{DATASET_ID}.tls_ipc_catchword"
TABLE_CONCORDANCE = f"{PROJECT_ID}.{DATASET_ID}.tls_ipc_concordance"
TABLE_EVERUSED = f"{PROJECT_ID}.{DATASET_ID}.tls_ipc_everused"


# =============================================================================
# BigQuery Schemas
# =============================================================================

SCHEMA_HIERARCHY = [
    bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("symbol_short", "STRING"),
    bigquery.SchemaField("symbol_patstat", "STRING"),
    bigquery.SchemaField("kind", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("level", "INT64", mode="REQUIRED"),
    bigquery.SchemaField("parent", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("parent_short", "STRING"),
    bigquery.SchemaField("title_en", "STRING"),
    bigquery.SchemaField("title_full", "STRING"),
    bigquery.SchemaField("ipc_version", "STRING"),
    bigquery.SchemaField("latest_version_date", "STRING"),
    bigquery.SchemaField("introduced_date", "STRING"),
    bigquery.SchemaField("additional_content", "STRING"),
    bigquery.SchemaField("section_title", "STRING"),
    bigquery.SchemaField("class_title", "STRING"),
    bigquery.SchemaField("subclass_title", "STRING"),
]

SCHEMA_CATCHWORD = [
    bigquery.SchemaField("catchword", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("symbol_short", "STRING"),
    bigquery.SchemaField("symbol_patstat", "STRING"),
    bigquery.SchemaField("parent_catchword", "STRING"),
]

SCHEMA_CONCORDANCE = [
    bigquery.SchemaField("from_symbol", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("from_symbol_patstat", "STRING"),
    bigquery.SchemaField("to_symbol", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("to_symbol_patstat", "STRING"),
    bigquery.SchemaField("from_version", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("to_version", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("modification", "STRING"),
    bigquery.SchemaField("default_reclassification", "STRING"),
    bigquery.SchemaField("revision_project", "STRING"),
]

SCHEMA_EVERUSED = [
    bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("symbol_patstat", "STRING"),
    bigquery.SchemaField("introduced_date", "STRING"),
    bigquery.SchemaField("deprecated_date", "STRING"),
    bigquery.SchemaField("is_active", "BOOL"),
]


# =============================================================================
# BigQuery Client
# =============================================================================

def get_bigquery_client(project_id: str) -> bigquery.Client:
    """Create BigQuery client using gcloud default credentials or service account from .env."""
    import google.auth

    try:
        credentials, _ = google.auth.default()
        print("  Using gcloud application-default credentials")
        return bigquery.Client(project=project_id, credentials=credentials)
    except google.auth.exceptions.DefaultCredentialsError:
        pass

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


# =============================================================================
# Read from SQLite
# =============================================================================

def read_hierarchy(db_path: Path) -> list[dict]:
    """Read ipc table from SQLite."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT symbol, symbol_short, symbol_patstat, kind, level,
               parent, parent_short, title_en, title_full,
               ipc_version, latest_version_date, introduced_date,
               additional_content, section_title, class_title, subclass_title
        FROM ipc
    """)

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def read_catchword(db_path: Path) -> list[dict]:
    """Read ipc_catchword table from SQLite."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT catchword, symbol, symbol_short, symbol_patstat, parent_catchword FROM ipc_catchword")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def read_concordance(db_path: Path) -> list[dict]:
    """Read ipc_concordance table from SQLite."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT from_symbol, from_symbol_patstat, to_symbol, to_symbol_patstat,
               from_version, to_version, modification, default_reclassification,
               revision_project
        FROM ipc_concordance
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def read_everused(db_path: Path) -> list[dict]:
    """Read ipc_everused table from SQLite."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT symbol, symbol_patstat, introduced_date, deprecated_date, is_active FROM ipc_everused")
    rows = []
    for r in cur.fetchall():
        row = dict(r)
        row["is_active"] = bool(row["is_active"])
        rows.append(row)
    conn.close()
    return rows


# =============================================================================
# Upload
# =============================================================================

def upload_table(client: bigquery.Client, table_id: str, schema: list,
                 rows: list[dict], dry_run: bool = False):
    """Upload rows to a BigQuery table."""
    if dry_run:
        print(f"\n[DRY RUN] Would upload {len(rows):,} rows to {table_id}")
        print("  Sample rows:")
        for row in rows[:3]:
            cols = list(row.keys())
            preview = {k: str(v)[:60] for k, v in row.items() if v is not None}
            print(f"    {preview}")
        return

    print(f"\nUploading {len(rows):,} rows to {table_id}...")

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_TRUNCATE",
    )

    job = client.load_table_from_json(rows, table_id, job_config=job_config)
    job.result()

    print(f"  Loaded {job.output_rows:,} rows into {table_id}")


# =============================================================================
# Validation Queries
# =============================================================================

def print_validation_queries():
    """Print validation queries to run after upload."""
    print("\n" + "=" * 70)
    print("VALIDATION QUERIES - Run these in BigQuery Console:")
    print("=" * 70)

    queries = [
        ("Row counts",
         """SELECT 'tls_ipc_hierarchy' as tbl, COUNT(*) as cnt FROM `patstat-mtc.patstat.tls_ipc_hierarchy`
UNION ALL SELECT 'tls_ipc_catchword', COUNT(*) FROM `patstat-mtc.patstat.tls_ipc_catchword`
UNION ALL SELECT 'tls_ipc_concordance', COUNT(*) FROM `patstat-mtc.patstat.tls_ipc_concordance`
UNION ALL SELECT 'tls_ipc_everused', COUNT(*) FROM `patstat-mtc.patstat.tls_ipc_everused`"""),

        ("Level distribution",
         """SELECT level, COUNT(*) as cnt
FROM `patstat-mtc.patstat.tls_ipc_hierarchy`
GROUP BY level ORDER BY level"""),

        ("JOIN test with tls209_appln_ipc",
         """SELECT i.appln_id, i.ipc_class_symbol, h.title_en, h.title_full
FROM `patstat-mtc.patstat.tls209_appln_ipc` i
JOIN `patstat-mtc.patstat.tls_ipc_hierarchy` h
  ON i.ipc_class_symbol = h.symbol_patstat
WHERE i.ipc_value = 'I' AND i.ipc_position = 'F'
LIMIT 5"""),

        ("Catchword search test",
         """SELECT c.catchword, h.symbol_short, h.title_en
FROM `patstat-mtc.patstat.tls_ipc_catchword` c
JOIN `patstat-mtc.patstat.tls_ipc_hierarchy` h ON c.symbol = h.symbol
WHERE LOWER(c.catchword) LIKE '%laser%'
LIMIT 10"""),

        ("Concordance affected patents",
         """SELECT c.from_symbol_patstat, c.to_symbol_patstat, c.modification,
       COUNT(DISTINCT a.appln_id) as affected
FROM `patstat-mtc.patstat.tls_ipc_concordance` c
JOIN `patstat-mtc.patstat.tls209_appln_ipc` a
  ON a.ipc_class_symbol = c.from_symbol_patstat
GROUP BY 1, 2, 3
ORDER BY affected DESC
LIMIT 10"""),

        ("Deprecated symbols in use",
         """SELECT e.symbol_patstat, e.introduced_date, e.deprecated_date,
       COUNT(DISTINCT a.appln_id) as patent_count
FROM `patstat-mtc.patstat.tls209_appln_ipc` a
JOIN `patstat-mtc.patstat.tls_ipc_everused` e
  ON a.ipc_class_symbol = e.symbol_patstat
WHERE e.is_active = FALSE
GROUP BY 1, 2, 3
ORDER BY patent_count DESC
LIMIT 10"""),

        ("Match rate improvement check",
         """SELECT
  COUNTIF(h.symbol IS NOT NULL) as matched,
  COUNTIF(h.symbol IS NULL AND e.symbol IS NOT NULL) as in_everused_only,
  COUNTIF(h.symbol IS NULL AND e.symbol IS NULL) as unknown
FROM (SELECT DISTINCT ipc_class_symbol FROM `patstat-mtc.patstat.tls209_appln_ipc`) d
LEFT JOIN `patstat-mtc.patstat.tls_ipc_hierarchy` h ON d.ipc_class_symbol = h.symbol_patstat
LEFT JOIN `patstat-mtc.patstat.tls_ipc_everused` e ON d.ipc_class_symbol = e.symbol_patstat"""),
    ]

    for name, sql in queries:
        print(f"\n-- {name}")
        print(sql)


# =============================================================================
# Main
# =============================================================================

TABLES = {
    "hierarchy": (TABLE_HIERARCHY, SCHEMA_HIERARCHY, read_hierarchy),
    "catchword": (TABLE_CATCHWORD, SCHEMA_CATCHWORD, read_catchword),
    "concordance": (TABLE_CONCORDANCE, SCHEMA_CONCORDANCE, read_concordance),
    "everused": (TABLE_EVERUSED, SCHEMA_EVERUSED, read_everused),
}


def main():
    parser = argparse.ArgumentParser(
        description="Upload IPC 2026.01 tables from SQLite to BigQuery"
    )
    parser.add_argument(
        "db_path",
        type=Path,
        help="Path to patent-classification-2026.db",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without uploading",
    )
    parser.add_argument(
        "--table",
        choices=list(TABLES.keys()) + ["all"],
        default="all",
        help="Which table to upload (default: all)",
    )

    args = parser.parse_args()

    if not args.db_path.exists():
        print(f"Error: Database not found: {args.db_path}")
        sys.exit(1)

    # Determine which tables to upload
    if args.table == "all":
        targets = list(TABLES.keys())
    else:
        targets = [args.table]

    # Create BQ client once (skip if dry run)
    client = None
    if not args.dry_run:
        client = get_bigquery_client(PROJECT_ID)

    # Upload each table
    for name in targets:
        table_id, schema, reader = TABLES[name]
        print(f"\n{'='*60}")
        print(f"Table: {name} ({table_id})")
        print(f"{'='*60}")

        rows = reader(args.db_path)
        print(f"  Read {len(rows):,} rows from SQLite")

        upload_table(client, table_id, schema, rows, dry_run=args.dry_run)

    # Print validation queries
    print_validation_queries()


if __name__ == "__main__":
    main()
