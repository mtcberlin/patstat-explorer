#!/usr/bin/env python3
"""
Migrate PATSTAT CSV files to BigQuery.

Usage:
    python migrate_to_bq.py /path/to/csv/folder
    python migrate_to_bq.py /path/to/csv/folder --table tls201_appln  # Single table
    python migrate_to_bq.py /path/to/csv/folder --dry-run             # Preview only

Prerequisites:
    pip install google-cloud-bigquery
    bq auth login  # or set GOOGLE_APPLICATION_CREDENTIALS
"""

import os
import sys
import glob
import argparse
import subprocess
import json
from pathlib import Path

# BigQuery project and dataset
PROJECT_ID = "patstat-mtc"
DATASET_ID = "patstat"

# Table configurations based on EPO best practices
# Partitioning on appln_filing_year where applicable for faster queries
TABLE_CONFIG = {
    "tls201_appln": {
        "partition_field": "appln_filing_year",
        "cluster_fields": ["appln_auth", "granted"],
        "description": "Main patent applications table"
    },
    "tls202_appln_title": {
        "cluster_fields": ["appln_id"],
        "description": "Application titles"
    },
    "tls203_appln_abstr": {
        "cluster_fields": ["appln_id"],
        "description": "Application abstracts"
    },
    "tls204_appln_prior": {
        "cluster_fields": ["appln_id"],
        "description": "Priority claims"
    },
    "tls205_tech_rel": {
        "cluster_fields": ["appln_id"],
        "description": "Technical relations"
    },
    "tls206_person": {
        "cluster_fields": ["person_ctry_code", "psn_sector"],
        "description": "Persons (applicants/inventors)"
    },
    "tls207_pers_appln": {
        "cluster_fields": ["appln_id", "person_id"],
        "description": "Person-Application link table"
    },
    "tls209_appln_ipc": {
        "cluster_fields": ["appln_id"],
        "description": "IPC classifications"
    },
    "tls210_appln_n_cls": {
        "cluster_fields": ["appln_id"],
        "description": "National classifications"
    },
    "tls211_pat_publn": {
        "partition_field": "publn_date",
        "cluster_fields": ["appln_id", "publn_auth"],
        "description": "Patent publications"
    },
    "tls212_citation": {
        "cluster_fields": ["pat_publn_id", "cited_pat_publn_id"],
        "description": "Citation data"
    },
    "tls214_npl_publn": {
        "description": "Non-patent literature"
    },
    "tls215_citn_categ": {
        "description": "Citation categories"
    },
    "tls216_appln_contn": {
        "cluster_fields": ["appln_id"],
        "description": "Continuation data"
    },
    "tls222_appln_jp_class": {
        "cluster_fields": ["appln_id"],
        "description": "Japanese classifications"
    },
    "tls223_appln_docus": {
        "cluster_fields": ["appln_id"],
        "description": "DOCUS classifications"
    },
    "tls224_appln_cpc": {
        "cluster_fields": ["appln_id"],
        "description": "CPC classifications"
    },
    "tls226_person_orig": {
        "cluster_fields": ["person_id"],
        "description": "Original person names"
    },
    "tls227_pers_publn": {
        "cluster_fields": ["pat_publn_id", "person_id"],
        "description": "Person-Publication link"
    },
    "tls228_docdb_fam_citn": {
        "cluster_fields": ["docdb_family_id"],
        "description": "DOCDB family citations"
    },
    "tls229_appln_nace2": {
        "cluster_fields": ["appln_id"],
        "description": "NACE2 industry codes"
    },
    "tls230_appln_techn_field": {
        "cluster_fields": ["appln_id"],
        "description": "Technology fields"
    },
    "tls231_inpadoc_legal_event": {
        "cluster_fields": ["appln_id"],
        "description": "Legal events"
    },
    "tls801_country": {
        "description": "Country codes lookup"
    },
    "tls803_legal_event_code": {
        "description": "Legal event codes lookup"
    },
    "tls901_techn_field_ipc": {
        "description": "Technology field IPC mapping"
    },
    "tls902_ipc_nace2": {
        "description": "IPC to NACE2 mapping"
    },
    "tls904_nuts": {
        "description": "NUTS regional codes"
    },
    "tls906_person": {
        "cluster_fields": ["person_id"],
        "description": "Harmonized persons"
    },
}


def find_csv_files(folder, table_name=None):
    """Find all PATSTAT CSV files in folder."""
    folder = Path(folder)
    files = {}

    # PATSTAT CSVs are typically named like: tls201_part01.csv or tls201_appln.csv
    patterns = ["*.csv", "*.CSV", "*.txt", "*.TXT"]

    for pattern in patterns:
        for f in folder.glob(pattern):
            # Extract table name from filename
            name = f.stem.lower()

            # Handle multipart files: tls201_part01 -> tls201
            if '_part' in name:
                base_name = name.split('_part')[0]
            else:
                base_name = name

            # Match known tables
            for table in TABLE_CONFIG.keys():
                if base_name.startswith(table.replace('_', '')):
                    base_name = table
                    break
                if table in base_name:
                    base_name = table
                    break

            if table_name and base_name != table_name:
                continue

            if base_name not in files:
                files[base_name] = []
            files[base_name].append(str(f))

    return files


def get_bq_schema_from_csv(csv_file):
    """Infer BigQuery schema from CSV header."""
    import csv

    with open(csv_file, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.reader(f)
        headers = next(reader)

        # Sample first few rows to infer types
        sample_rows = []
        for i, row in enumerate(reader):
            if i >= 100:
                break
            sample_rows.append(row)

    schema = []
    for i, col in enumerate(headers):
        col_name = col.strip().lower()

        # Infer type from column name and values
        if col_name.endswith('_id') or col_name.endswith('_nr'):
            col_type = 'INT64'
        elif col_name.endswith('_date'):
            col_type = 'DATE'
        elif col_name.endswith('_year'):
            col_type = 'INT64'
        elif col_name in ['granted', 'publn_first_grant', 'publn_claims']:
            col_type = 'STRING'
        elif col_name.endswith('_size') or col_name.endswith('_count'):
            col_type = 'INT64'
        elif col_name == 'weight':
            col_type = 'FLOAT64'
        else:
            # Check sample values
            col_type = 'STRING'
            if sample_rows:
                values = [row[i] if i < len(row) else '' for row in sample_rows]
                values = [v for v in values if v.strip()]
                if values:
                    # Check if all numeric
                    try:
                        [int(v) for v in values[:10]]
                        col_type = 'INT64'
                    except:
                        try:
                            [float(v) for v in values[:10]]
                            col_type = 'FLOAT64'
                        except:
                            col_type = 'STRING'

        schema.append(f"{col_name}:{col_type}")

    return schema


def load_csv_to_bq(csv_files, table_name, dry_run=False):
    """Load CSV file(s) to BigQuery using bq command."""
    config = TABLE_CONFIG.get(table_name, {})
    full_table = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    print(f"\n{'='*60}")
    print(f"Loading: {table_name}")
    print(f"Files: {len(csv_files)}")
    print(f"Target: {full_table}")

    # Build bq load command
    cmd = [
        "bq", "load",
        "--source_format=CSV",
        "--skip_leading_rows=1",
        "--allow_quoted_newlines",
        "--replace",  # Replace existing table
        "--max_bad_records=1000",
    ]

    # Add clustering if configured
    if 'cluster_fields' in config:
        cmd.append(f"--clustering_fields={','.join(config['cluster_fields'])}")

    # Add partitioning if configured (requires schema)
    # Note: For range partitioning on INT64, we need special handling
    if 'partition_field' in config:
        field = config['partition_field']
        if field.endswith('_year'):
            cmd.append(f"--range_partitioning={field},1900,2030,1")
        elif field.endswith('_date'):
            cmd.append(f"--time_partitioning_field={field}")

    # Add table description
    if 'description' in config:
        cmd.append(f"--description={config['description']}")

    # Auto-detect schema from first file
    cmd.append("--autodetect")

    # Target table
    cmd.append(full_table)

    # Source files (can be multiple)
    cmd.extend(csv_files)

    print(f"\nCommand: {' '.join(cmd[:10])}...")

    if dry_run:
        print("[DRY RUN] Would execute above command")
        return True

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Successfully loaded {table_name}")
            return True
        else:
            print(f"✗ Error loading {table_name}:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False


def create_dataset(dry_run=False):
    """Create the dataset if it doesn't exist."""
    cmd = [
        "bq", "mk",
        "--dataset",
        "--location=EU",  # PATSTAT is EU-based
        f"--description=PATSTAT Patent Database",
        f"{PROJECT_ID}:{DATASET_ID}"
    ]

    print(f"Creating dataset: {PROJECT_ID}.{DATASET_ID}")

    if dry_run:
        print("[DRY RUN] Would create dataset")
        return True

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0 or "already exists" in result.stderr:
        print("✓ Dataset ready")
        return True
    else:
        print(f"Warning: {result.stderr}")
        return True  # Continue anyway


def main():
    parser = argparse.ArgumentParser(description='Migrate PATSTAT CSV to BigQuery')
    parser.add_argument('folder', help='Folder containing PATSTAT CSV files')
    parser.add_argument('--table', help='Load specific table only')
    parser.add_argument('--dry-run', action='store_true', help='Preview without loading')
    parser.add_argument('--list', action='store_true', help='List found CSV files')
    args = parser.parse_args()

    if not os.path.isdir(args.folder):
        print(f"Error: {args.folder} is not a directory")
        sys.exit(1)

    # Find CSV files
    print(f"Scanning {args.folder} for PATSTAT CSV files...")
    files = find_csv_files(args.folder, args.table)

    if not files:
        print("No PATSTAT CSV files found!")
        print("Expected filenames like: tls201_appln.csv, tls206_person.csv, etc.")
        sys.exit(1)

    print(f"\nFound {len(files)} tables:")
    for table, csvs in sorted(files.items()):
        total_size = sum(os.path.getsize(f) for f in csvs) / 1024 / 1024 / 1024
        print(f"  {table}: {len(csvs)} file(s), {total_size:.2f} GB")

    if args.list:
        return

    # Create dataset
    create_dataset(args.dry_run)

    # Load each table
    print("\n" + "="*60)
    print("Starting migration...")
    print("="*60)

    success = 0
    failed = 0

    for table, csvs in sorted(files.items()):
        if load_csv_to_bq(csvs, table, args.dry_run):
            success += 1
        else:
            failed += 1

    print("\n" + "="*60)
    print(f"Migration complete: {success} succeeded, {failed} failed")
    print("="*60)

    if success > 0 and not args.dry_run:
        print(f"\nYou can now query your data:")
        print(f"  bq query 'SELECT COUNT(*) FROM `{PROJECT_ID}.{DATASET_ID}.tls201_appln`'")


if __name__ == "__main__":
    main()
