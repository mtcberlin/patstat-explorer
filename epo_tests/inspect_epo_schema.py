#!/usr/bin/env python3
"""
Inspect EPO PATSTAT BigQuery schema to understand their best practices.
Outputs table schemas, partitioning, clustering, and sizes.

Usage:
    python inspect_epo_schema.py              # Query all tables
    python inspect_epo_schema.py tls201_appln # Query specific table
"""

import sys
import json
from datetime import datetime

import pandas as pd

try:
    from epo.tipdata.patstat import PatstatClient
except ImportError:
    print("ERROR: epo.tipdata.patstat module not found.")
    print("Run this in EPO Jupyter environment.")
    sys.exit(1)


def to_dataframe(result):
    """Convert sql_query result (list of dicts) to DataFrame."""
    if result is None:
        return None
    if isinstance(result, pd.DataFrame):
        return result
    if isinstance(result, list):
        return pd.DataFrame(result) if result else pd.DataFrame()
    return result


def get_dataset_info(patstat):
    """Get dataset-level information."""
    # This query gets the project and dataset from a simple query
    query = """
        SELECT
            table_catalog as project_id,
            table_schema as dataset_id
        FROM `INFORMATION_SCHEMA.TABLES`
        LIMIT 1
    """
    try:
        result = to_dataframe(patstat.sql_query(query, use_legacy_sql=False))
        if result is not None and len(result) > 0:
            return result.iloc[0].to_dict()
    except Exception as e:
        print(f"Could not get dataset info: {e}")
    return None


def get_all_tables(patstat):
    """Get list of all tables with basic info."""
    query = """
        SELECT
            table_name,
            table_type,
            creation_time,
            ROUND(size_bytes / 1024 / 1024 / 1024, 2) as size_gb,
            row_count
        FROM `INFORMATION_SCHEMA.TABLES`
        LEFT JOIN `INFORMATION_SCHEMA.TABLE_STORAGE`
            USING (table_catalog, table_schema, table_name)
        ORDER BY size_bytes DESC NULLS LAST
    """
    try:
        return to_dataframe(patstat.sql_query(query, use_legacy_sql=False))
    except Exception as e:
        # Fallback without storage info
        print(f"Storage info not available, trying basic query: {e}")
        query = """
            SELECT
                table_name,
                table_type,
                creation_time
            FROM `INFORMATION_SCHEMA.TABLES`
            ORDER BY table_name
        """
        return to_dataframe(patstat.sql_query(query, use_legacy_sql=False))


def get_table_schema(patstat, table_name):
    """Get detailed schema for a specific table."""
    query = f"""
        SELECT
            column_name,
            data_type,
            is_nullable,
            ordinal_position,
            column_default
        FROM `INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
    """
    return to_dataframe(patstat.sql_query(query, use_legacy_sql=False))


def get_table_partitioning(patstat, table_name):
    """Get partitioning info for a table."""
    query = f"""
        SELECT
            table_name,
            partition_id,
            total_rows,
            total_logical_bytes,
            last_modified_time
        FROM `INFORMATION_SCHEMA.PARTITIONS`
        WHERE table_name = '{table_name}'
        ORDER BY partition_id
        LIMIT 20
    """
    try:
        return to_dataframe(patstat.sql_query(query, use_legacy_sql=False))
    except Exception:
        return None


def get_table_options(patstat, table_name):
    """Get table options (clustering, partitioning config)."""
    query = f"""
        SELECT
            option_name,
            option_value
        FROM `INFORMATION_SCHEMA.TABLE_OPTIONS`
        WHERE table_name = '{table_name}'
    """
    try:
        return to_dataframe(patstat.sql_query(query, use_legacy_sql=False))
    except Exception:
        return None


def get_table_sample(patstat, table_name, limit=5):
    """Get sample rows from a table."""
    query = f"SELECT * FROM `{table_name}` LIMIT {limit}"
    try:
        return to_dataframe(patstat.sql_query(query, use_legacy_sql=False))
    except Exception as e:
        print(f"Could not get sample: {e}")
        return None


def inspect_table(patstat, table_name):
    """Full inspection of a single table."""
    print(f"\n{'='*70}")
    print(f"  TABLE: {table_name}")
    print('='*70)

    # Schema
    print("\n  COLUMNS:")
    print(f"  {'-'*66}")
    schema = get_table_schema(patstat, table_name)
    if schema is not None and len(schema) > 0:
        for _, row in schema.iterrows():
            nullable = "NULL" if row['is_nullable'] == 'YES' else "NOT NULL"
            print(f"    {row['column_name']:<30} {row['data_type']:<20} {nullable}")

    # Options (partitioning, clustering)
    print("\n  TABLE OPTIONS:")
    print(f"  {'-'*66}")
    options = get_table_options(patstat, table_name)
    if options is not None and len(options) > 0:
        for _, row in options.iterrows():
            print(f"    {row['option_name']}: {row['option_value']}")
    else:
        print("    No special options (no partitioning/clustering)")

    # Partitions
    partitions = get_table_partitioning(patstat, table_name)
    if partitions is not None and len(partitions) > 0:
        print("\n  PARTITIONS (first 20):")
        print(f"  {'-'*66}")
        for _, row in partitions.iterrows():
            print(f"    {row['partition_id']}: {row['total_rows']:,} rows")

    return {
        "table_name": table_name,
        "columns": schema.to_dict('records') if schema is not None else [],
        "options": options.to_dict('records') if options is not None else [],
        "partitions": partitions.to_dict('records') if partitions is not None else []
    }


def main():
    print("Connecting to EPO PATSTAT BigQuery...")
    patstat = PatstatClient(env='PROD')
    print("✓ Connected\n")

    # Get dataset info
    dataset_info = get_dataset_info(patstat)
    if dataset_info:
        print(f"Project: {dataset_info.get('project_id', 'unknown')}")
        print(f"Dataset: {dataset_info.get('dataset_id', 'unknown')}")

    # Check if specific table requested
    if len(sys.argv) > 1:
        table_name = sys.argv[1]
        result = inspect_table(patstat, table_name)

        # Save to JSON
        output_file = f"schema_{table_name}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n\nSchema saved to: {output_file}")
        return

    # List all tables
    print("\n" + "="*70)
    print("  ALL TABLES")
    print("="*70)

    tables = get_all_tables(patstat)
    all_schemas = []

    if tables is not None:
        print(f"\n  {'Table':<30} {'Type':<15} {'Size (GB)':>12} {'Rows':>15}")
        print(f"  {'-'*30} {'-'*15} {'-'*12} {'-'*15}")

        for _, row in tables.iterrows():
            size = f"{row.get('size_gb', 'N/A'):>10}" if 'size_gb' in row else "N/A"
            rows = f"{row.get('row_count', 'N/A'):>13,}" if 'row_count' in row and row.get('row_count') else "N/A"
            print(f"  {row['table_name']:<30} {row['table_type']:<15} {size:>12} {rows:>15}")

        # Inspect key tables
        key_tables = [
            'tls201_appln',      # Main applications table
            'tls206_person',     # Persons (applicants/inventors)
            'tls207_pers_appln', # Person-Application link
            'tls209_appln_ipc',  # IPC classifications
            'tls211_pat_publn',  # Publications
            'tls212_citation',   # Citations
            'tls224_appln_cpc',  # CPC classifications
        ]

        print("\n\nInspecting key tables for schema details...")
        for table in key_tables:
            if table in tables['table_name'].values:
                schema_info = inspect_table(patstat, table)
                all_schemas.append(schema_info)

    # Save all schemas
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"epo_patstat_schema_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "dataset_info": dataset_info,
            "tables": tables.to_dict('records') if tables is not None else [],
            "key_table_schemas": all_schemas
        }, f, indent=2, default=str)

    print(f"\n\n{'='*70}")
    print(f"  Schema exported to: {output_file}")
    print('='*70)

    # Generate CREATE TABLE statements
    print("\n\nGenerating CREATE TABLE statements...")
    create_file = f"create_tables_{timestamp}.sql"
    with open(create_file, 'w') as f:
        f.write("-- EPO PATSTAT Table Schemas\n")
        f.write(f"-- Generated: {timestamp}\n")
        f.write("-- Target project: patstat-mtc\n\n")

        for schema_info in all_schemas:
            table_name = schema_info['table_name']
            columns = schema_info['columns']
            options = schema_info['options']

            f.write(f"\n-- {table_name}\n")
            f.write(f"CREATE TABLE IF NOT EXISTS `patstat-mtc.patstat.{table_name}` (\n")

            col_defs = []
            for col in columns:
                nullable = "" if col['is_nullable'] == 'YES' else " NOT NULL"
                col_defs.append(f"    {col['column_name']} {col['data_type']}{nullable}")

            f.write(",\n".join(col_defs))
            f.write("\n)")

            # Add options
            option_parts = []
            for opt in options:
                if opt['option_name'] == 'partition_expiration_days':
                    continue  # Skip this one
                option_parts.append(f"{opt['option_name']}={opt['option_value']}")

            if option_parts:
                f.write("\nOPTIONS (\n    ")
                f.write(",\n    ".join(option_parts))
                f.write("\n)")

            f.write(";\n")

    print(f"  CREATE TABLE statements saved to: {create_file}")


if __name__ == "__main__":
    main()
