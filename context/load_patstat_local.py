#!/usr/bin/env python3
"""
Load PATSTAT CSV files from local disk directly to BigQuery.

This script:
1. Finds all PATSTAT CSV files in a directory
2. Creates tables if they don't exist (using v2 schema with partitioning/clustering)
3. Loads data using 'bq load' (streams through client, no GCS needed)
4. Tracks progress and supports resuming
5. Validates row counts after loading

Usage:
    python load_patstat_local.py /path/to/csv/files PROJECT_ID DATASET

Example:
    python load_patstat_local.py /tmp/patstat my-project patstat
    python load_patstat_local.py . my-project patstat --dry-run
    python load_patstat_local.py /data my-project patstat --resume
    python load_patstat_local.py /data my-project patstat --parallel 4
"""

import os
import sys
import glob
import json
import subprocess
import argparse
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Table definitions with schema, partitioning, and clustering
# Matches create_patstat_tables_bq_v2.sql
TABLE_DEFINITIONS = {
    'tls201_appln': {
        'schema': 'appln_id:INTEGER,appln_auth:STRING,appln_nr:STRING,appln_kind:STRING,appln_filing_date:DATE,appln_filing_year:INTEGER,appln_nr_epodoc:STRING,appln_nr_original:STRING,ipr_type:STRING,receiving_office:STRING,internat_appln_id:INTEGER,int_phase:STRING,reg_phase:STRING,nat_phase:STRING,earliest_filing_date:DATE,earliest_filing_year:INTEGER,earliest_filing_id:INTEGER,earliest_publn_date:DATE,earliest_publn_year:INTEGER,earliest_pat_publn_id:INTEGER,granted:STRING,docdb_family_id:INTEGER,inpadoc_family_id:INTEGER,docdb_family_size:INTEGER,nb_citing_docdb_fam:INTEGER,nb_applicants:INTEGER,nb_inventors:INTEGER',
        'partition': '--range_partitioning=appln_filing_year,1900,2030,1',
        'cluster': '--clustering_fields=appln_auth,docdb_family_id,granted',
        'expected_count': 140525582,
    },
    'tls202_appln_title': {
        'schema': 'appln_id:INTEGER,appln_title_lg:STRING,appln_title:STRING',
        'cluster': '--clustering_fields=appln_id',
        'expected_count': 119259497,
    },
    'tls203_appln_abstr': {
        'schema': 'appln_id:INTEGER,appln_abstract_lg:STRING,appln_abstract:STRING',
        'cluster': '--clustering_fields=appln_id',
        'expected_count': 96536721,
    },
    'tls204_appln_prior': {
        'schema': 'appln_id:INTEGER,prior_appln_id:INTEGER,prior_appln_seq_nr:INTEGER',
        'cluster': '--clustering_fields=appln_id,prior_appln_id',
        'expected_count': 53194773,
    },
    'tls205_tech_rel': {
        'schema': 'appln_id:INTEGER,tech_rel_appln_id:INTEGER',
        'cluster': '--clustering_fields=appln_id',
        'expected_count': 4160592,
    },
    'tls206_person': {
        'schema': 'person_id:INTEGER,person_name:STRING,person_name_orig_lg:STRING,person_address:STRING,person_ctry_code:STRING,nuts:STRING,nuts_level:INTEGER,doc_std_name_id:INTEGER,doc_std_name:STRING,psn_id:INTEGER,psn_name:STRING,psn_level:INTEGER,psn_sector:STRING,han_id:INTEGER,han_name:STRING,han_harmonized:INTEGER',
        'cluster': '--clustering_fields=person_ctry_code,psn_id,han_id',
        'expected_count': 97853865,
    },
    'tls207_pers_appln': {
        'schema': 'person_id:INTEGER,appln_id:INTEGER,applt_seq_nr:INTEGER,invt_seq_nr:INTEGER',
        'cluster': '--clustering_fields=appln_id,person_id,applt_seq_nr',
        'expected_count': 408478469,
    },
    'tls209_appln_ipc': {
        'schema': 'appln_id:INTEGER,ipc_class_symbol:STRING,ipc_class_level:STRING,ipc_version:DATE,ipc_value:STRING,ipc_position:STRING,ipc_gener_auth:STRING',
        'cluster': '--clustering_fields=appln_id,ipc_class_symbol',
        'expected_count': 374559946,
    },
    'tls210_appln_n_cls': {
        'schema': 'appln_id:INTEGER,nat_class_symbol:STRING',
        'cluster': '--clustering_fields=appln_id',
        'expected_count': 26217769,
    },
    'tls211_pat_publn': {
        'schema': 'pat_publn_id:INTEGER,publn_auth:STRING,publn_nr:STRING,publn_nr_original:STRING,publn_kind:STRING,appln_id:INTEGER,publn_date:DATE,publn_lg:STRING,publn_first_grant:STRING,publn_claims:INTEGER',
        'cluster': '--clustering_fields=appln_id,publn_auth',
        'expected_count': 167837244,
    },
    'tls212_citation': {
        'schema': 'pat_publn_id:INTEGER,citn_replenished:INTEGER,citn_id:INTEGER,citn_origin:STRING,cited_pat_publn_id:INTEGER,cited_appln_id:INTEGER,pat_citn_seq_nr:INTEGER,cited_npl_publn_id:STRING,npl_citn_seq_nr:INTEGER,citn_gener_auth:STRING',
        'cluster': '--clustering_fields=pat_publn_id,cited_appln_id,cited_pat_publn_id',
        'expected_count': 596775557,
    },
    'tls214_npl_publn': {
        'schema': 'npl_publn_id:STRING,xp_nr:INTEGER,npl_type:STRING,npl_biblio:STRING,npl_author:STRING,npl_title1:STRING,npl_title2:STRING,npl_editor:STRING,npl_volume:STRING,npl_issue:STRING,npl_publn_date:STRING,npl_publn_end_date:STRING,npl_publisher:STRING,npl_page_first:STRING,npl_page_last:STRING,npl_abstract_nr:STRING,npl_doi:STRING,npl_isbn:STRING,npl_issn:STRING,online_availability:STRING,online_classification:STRING,online_search_date:STRING',
        'cluster': '--clustering_fields=npl_publn_id',
        'expected_count': 43569746,
    },
    'tls215_citn_categ': {
        'schema': 'pat_publn_id:INTEGER,citn_replenished:INTEGER,citn_id:INTEGER,citn_categ:STRING,relevant_claim:INTEGER',
        'cluster': '--clustering_fields=pat_publn_id,citn_id',
        'expected_count': 1346861951,
    },
    'tls216_appln_contn': {
        'schema': 'appln_id:INTEGER,parent_appln_id:INTEGER,contn_type:STRING',
        'cluster': '--clustering_fields=appln_id',
        'expected_count': 5819586,
    },
    'tls222_appln_jp_class': {
        'schema': 'appln_id:INTEGER,jp_class_scheme:STRING,jp_class_symbol:STRING',
        'cluster': '--clustering_fields=appln_id,jp_class_symbol',
        'expected_count': 428299335,
    },
    'tls224_appln_cpc': {
        'schema': 'appln_id:INTEGER,cpc_class_symbol:STRING',
        'cluster': '--clustering_fields=appln_id,cpc_class_symbol',
        'expected_count': 436450350,
    },
    'tls225_docdb_fam_cpc': {
        'schema': 'docdb_family_id:INTEGER,cpc_class_symbol:STRING,cpc_gener_auth:STRING,cpc_version:DATE,cpc_position:STRING,cpc_value:STRING,cpc_action_date:DATE,cpc_status:STRING,cpc_data_source:STRING',
        'cluster': '--clustering_fields=docdb_family_id,cpc_class_symbol',
        'expected_count': 224464483,
    },
    'tls226_person_orig': {
        'schema': 'person_orig_id:INTEGER,person_id:INTEGER,source:STRING,source_version:STRING,name_freeform:STRING,person_name_orig_lg:STRING,last_name:STRING,first_name:STRING,middle_name:STRING,address_freeform:STRING,address_1:STRING,address_2:STRING,address_3:STRING,address_4:STRING,address_5:STRING,street:STRING,city:STRING,zip_code:STRING,state:STRING,person_ctry_code:STRING,residence_ctry_code:STRING,role:STRING',
        'cluster': '--clustering_fields=person_id,person_ctry_code',
        'expected_count': 120640365,
    },
    'tls227_pers_publn': {
        'schema': 'person_id:INTEGER,pat_publn_id:INTEGER,applt_seq_nr:INTEGER,invt_seq_nr:INTEGER',
        'cluster': '--clustering_fields=pat_publn_id,person_id',
        'expected_count': 533935876,
    },
    'tls228_docdb_fam_citn': {
        'schema': 'docdb_family_id:INTEGER,cited_docdb_family_id:INTEGER',
        'cluster': '--clustering_fields=docdb_family_id,cited_docdb_family_id',
        'expected_count': 307465107,
    },
    'tls229_appln_nace2': {
        'schema': 'appln_id:INTEGER,nace2_code:STRING,weight:FLOAT',
        'cluster': '--clustering_fields=appln_id,nace2_code',
        'expected_count': 166322438,
    },
    'tls230_appln_techn_field': {
        'schema': 'appln_id:INTEGER,techn_field_nr:INTEGER,weight:FLOAT',
        'cluster': '--clustering_fields=appln_id,techn_field_nr',
        'expected_count': 166549096,
    },
    'tls231_inpadoc_legal_event': {
        'schema': 'event_id:INTEGER,appln_id:INTEGER,event_seq_nr:INTEGER,event_type:STRING,event_auth:STRING,event_code:STRING,event_filing_date:DATE,event_publn_date:DATE,event_effective_date:DATE,event_text:STRING,ref_doc_auth:STRING,ref_doc_nr:STRING,ref_doc_kind:STRING,ref_doc_date:DATE,ref_doc_text:STRING,party_type:STRING,party_seq_nr:INTEGER,party_new:STRING,party_old:STRING,spc_nr:STRING,spc_filing_date:DATE,spc_patent_expiry_date:DATE,spc_extension_date:DATE,spc_text:STRING,designated_states:STRING,extension_states:STRING,fee_country:STRING,fee_payment_date:DATE,fee_renewal_year:INTEGER,fee_text:STRING,lapse_country:STRING,lapse_date:DATE,lapse_text:STRING,reinstate_country:STRING,reinstate_date:DATE,reinstate_text:STRING,class_scheme:STRING,class_symbol:STRING',
        'cluster': '--clustering_fields=appln_id,event_auth,event_code',
        'expected_count': 498252938,
    },
    'tls801_country': {
        'schema': 'ctry_code:STRING,iso_alpha3:STRING,st3_name:STRING,organisation_flag:STRING,continent:STRING,eu_member:STRING,epo_member:STRING,oecd_member:STRING,discontinued:STRING',
        'expected_count': 242,
    },
    'tls803_legal_event_code': {
        'schema': 'event_auth:STRING,event_code:STRING,event_descr:STRING,event_descr_orig:STRING,event_category_code:STRING,event_category_title:STRING',
        'expected_count': 4185,
    },
    'tls901_techn_field_ipc': {
        'schema': 'ipc_maingroup_symbol:STRING,techn_field_nr:INTEGER,techn_sector:STRING,techn_field:STRING',
        'expected_count': 771,
    },
    'tls902_ipc_nace2': {
        'schema': 'ipc:STRING,not_with_ipc:STRING,unless_with_ipc:STRING,nace2_code:STRING,nace2_weight:INTEGER,nace2_descr:STRING',
        'expected_count': 863,
    },
    'tls904_nuts': {
        'schema': 'nuts:STRING,nuts_level:INTEGER,nuts_label:STRING',
        'expected_count': 2056,
    },
}


def get_file_size_gb(filepath):
    """Get file size in GB."""
    return os.path.getsize(filepath) / (1024**3)


def find_csv_files(base_dir):
    """Find all PATSTAT CSV files grouped by table."""
    tables = {}

    for table_name in TABLE_DEFINITIONS.keys():
        pattern = os.path.join(base_dir, f"{table_name}_part*.csv")
        files = sorted(glob.glob(pattern))
        if files:
            total_size = sum(get_file_size_gb(f) for f in files)
            tables[table_name] = {
                'files': files,
                'count': len(files),
                'total_size_gb': total_size,
            }

    return tables


def run_command(cmd, dry_run=False):
    """Run a shell command and return success status."""
    if dry_run:
        print(f"  [DRY-RUN] {' '.join(cmd)}")
        return True, ""

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout per file
        )
        if result.returncode != 0:
            return False, result.stderr
        return True, result.stdout
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def table_exists(project, dataset, table):
    """Check if table exists in BigQuery."""
    cmd = ['bq', 'show', '--format=json', f'{project}:{dataset}.{table}']
    success, _ = run_command(cmd)
    return success


def create_table(project, dataset, table_name, definition, dry_run=False):
    """Create a BigQuery table with schema, partitioning, and clustering."""
    full_table = f'{project}:{dataset}.{table_name}'

    cmd = [
        'bq', 'mk',
        '--table',
        '--schema', definition['schema'],
    ]

    # Add partitioning if defined
    if 'partition' in definition:
        cmd.append(definition['partition'])

    # Add clustering if defined
    if 'cluster' in definition:
        cmd.append(definition['cluster'])

    cmd.append(full_table)

    return run_command(cmd, dry_run)


def load_file(project, dataset, table_name, filepath, definition, dry_run=False, replace=False):
    """Load a single CSV file into BigQuery.

    Args:
        replace: If True, use --replace to truncate table before loading.
                 Use this for the first file of a table to ensure clean slate.
    """
    full_table = f'{project}:{dataset}.{table_name}'

    cmd = [
        'bq', 'load',
        '--source_format=CSV',
        '--skip_leading_rows=1',
        '--allow_quoted_newlines',
        '--allow_jagged_rows',
        '--max_bad_records=100',  # Allow some bad records
    ]

    if replace:
        cmd.append('--replace')

    cmd.extend([full_table, filepath])

    return run_command(cmd, dry_run)


def get_row_count(project, dataset, table_name):
    """Get current row count from BigQuery."""
    cmd = [
        'bq', 'query',
        '--format=json',
        '--use_legacy_sql=false',
        f'SELECT COUNT(*) as cnt FROM `{project}.{dataset}.{table_name}`'
    ]
    success, output = run_command(cmd)
    if success and output:
        try:
            result = json.loads(output)
            return int(result[0]['cnt'])
        except:
            pass
    return None


def load_progress_file(progress_file):
    """Load progress from file."""
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {'loaded_files': [], 'completed_tables': []}


def save_progress_file(progress_file, progress):
    """Save progress to file."""
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)


def format_time(seconds):
    """Format seconds as human readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


def format_size(gb):
    """Format size in GB."""
    if gb < 1:
        return f"{gb*1024:.0f} MB"
    return f"{gb:.1f} GB"


def main():
    parser = argparse.ArgumentParser(
        description='Load PATSTAT CSV files to BigQuery',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python load_patstat_local.py /tmp/patstat my-project patstat
  python load_patstat_local.py . my-project patstat --dry-run
  python load_patstat_local.py /data my-project patstat --resume
  python load_patstat_local.py /data my-project patstat --tables tls201_appln,tls206_person
        """
    )
    parser.add_argument('csv_dir', help='Directory containing PATSTAT CSV files')
    parser.add_argument('project', help='GCP project ID')
    parser.add_argument('dataset', help='BigQuery dataset name')
    parser.add_argument('--dry-run', action='store_true', help='Show commands without executing')
    parser.add_argument('--resume', action='store_true', help='Resume from previous run')
    parser.add_argument('--tables', help='Comma-separated list of specific tables to load')
    parser.add_argument('--skip-create', action='store_true', help='Skip table creation (tables must exist)')
    parser.add_argument('--verify', action='store_true', help='Only verify row counts, no loading')

    args = parser.parse_args()

    # Validate directory
    if not os.path.isdir(args.csv_dir):
        print(f"ERROR: Directory not found: {args.csv_dir}")
        sys.exit(1)

    # Find CSV files
    print(f"\nScanning for PATSTAT CSV files in: {args.csv_dir}")
    tables = find_csv_files(args.csv_dir)

    if not tables:
        print("ERROR: No PATSTAT CSV files found!")
        print("Expected files like: tls201_appln_part01.csv, tls206_person_part01.csv, etc.")
        sys.exit(1)

    # Filter tables if specified
    if args.tables:
        filter_tables = [t.strip() for t in args.tables.split(',')]
        tables = {k: v for k, v in tables.items() if k in filter_tables}

    # Summary
    total_files = sum(t['count'] for t in tables.values())
    total_size = sum(t['total_size_gb'] for t in tables.values())

    print(f"\nFound {len(tables)} tables, {total_files} files, {format_size(total_size)} total")
    print("-" * 70)

    for table_name, info in sorted(tables.items()):
        print(f"  {table_name:<30} {info['count']:>3} files  {format_size(info['total_size_gb']):>10}")

    print("-" * 70)

    # Verify only mode
    if args.verify:
        print("\nVERIFICATION MODE - Checking row counts...")
        print("-" * 70)
        for table_name in sorted(tables.keys()):
            expected = TABLE_DEFINITIONS[table_name].get('expected_count', 0)
            actual = get_row_count(args.project, args.dataset, table_name)
            if actual is None:
                status = "NOT FOUND"
            elif actual == expected:
                status = "OK"
            elif actual > 0:
                pct = (actual / expected) * 100 if expected else 0
                status = f"{pct:.1f}%"
            else:
                status = "EMPTY"
            print(f"  {table_name:<30} Expected: {expected:>15,}  Actual: {actual or 0:>15,}  [{status}]")
        return

    # Load progress
    progress_file = os.path.join(args.csv_dir, '.patstat_load_progress.json')
    progress = load_progress_file(progress_file) if args.resume else {'loaded_files': [], 'completed_tables': []}

    # Confirm before starting
    if not args.dry_run:
        print(f"\nTarget: {args.project}:{args.dataset}")
        response = input("\nProceed with loading? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    # Process each table
    print("\n" + "=" * 70)
    start_time = time.time()
    errors = []

    for table_idx, (table_name, info) in enumerate(sorted(tables.items()), 1):
        definition = TABLE_DEFINITIONS[table_name]

        print(f"\n[{table_idx}/{len(tables)}] {table_name.upper()}")
        print(f"    Files: {info['count']}, Size: {format_size(info['total_size_gb'])}")

        # Skip if already completed
        if table_name in progress['completed_tables']:
            print(f"    SKIPPED (already completed)")
            continue

        # Create table if needed
        if not args.skip_create:
            if not table_exists(args.project, args.dataset, table_name) or args.dry_run:
                print(f"    Creating table...")
                success, error = create_table(args.project, args.dataset, table_name, definition, args.dry_run)
                if not success:
                    print(f"    ERROR creating table: {error}")
                    errors.append((table_name, 'create', error))
                    continue

        # Load each file
        # Determine if we need to REPLACE or APPEND:
        # - If resuming (some files already loaded): use APPEND for all remaining files
        # - If fresh start (no files loaded yet): use REPLACE for first file, then APPEND
        # This ensures we don't duplicate data when re-running on existing tables
        already_loaded_count = sum(1 for f in info['files'] if f in progress['loaded_files'])
        need_replace_first = (already_loaded_count == 0)

        if already_loaded_count > 0:
            print(f"    Resuming: {already_loaded_count}/{info['count']} files already loaded, using APPEND mode")
        else:
            print(f"    Fresh load: will REPLACE on first file, then APPEND")

        table_start = time.time()
        for file_idx, filepath in enumerate(info['files'], 1):
            filename = os.path.basename(filepath)
            file_size = get_file_size_gb(filepath)

            # Skip if already loaded
            if filepath in progress['loaded_files']:
                print(f"    [{file_idx}/{info['count']}] {filename} - SKIPPED (already loaded)")
                continue

            # Determine write mode: REPLACE for first file of fresh load, APPEND otherwise
            use_replace = need_replace_first
            mode_str = "REPLACE" if use_replace else "APPEND"

            print(f"    [{file_idx}/{info['count']}] {filename} ({format_size(file_size)}) [{mode_str}]...", end=' ', flush=True)

            file_start = time.time()
            success, error = load_file(args.project, args.dataset, table_name, filepath, definition, args.dry_run, replace=use_replace)
            elapsed = time.time() - file_start

            if success:
                speed = file_size / elapsed * 3600 if elapsed > 0 else 0  # GB/hour
                print(f"OK ({format_time(elapsed)}, {speed:.1f} GB/h)")
                progress['loaded_files'].append(filepath)
                save_progress_file(progress_file, progress)
                # After first successful load, switch to APPEND mode
                need_replace_first = False
            else:
                print(f"FAILED")
                print(f"        Error: {error[:200]}")
                errors.append((table_name, filename, error))
                # Keep need_replace_first=True so retry will still use REPLACE

        # Mark table as complete
        table_elapsed = time.time() - table_start
        print(f"    Table complete in {format_time(table_elapsed)}")
        progress['completed_tables'].append(table_name)
        save_progress_file(progress_file, progress)

    # Summary
    total_elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total time: {format_time(total_elapsed)}")
    print(f"  Tables processed: {len(progress['completed_tables'])}/{len(tables)}")
    print(f"  Files loaded: {len(progress['loaded_files'])}/{total_files}")

    if errors:
        print(f"\n  ERRORS ({len(errors)}):")
        for table, file_or_stage, error in errors:
            print(f"    - {table}/{file_or_stage}: {error[:100]}")
    else:
        print("\n  All loads completed successfully!")

    if not args.dry_run:
        print(f"\n  Progress saved to: {progress_file}")
        print(f"  Run with --verify to check row counts")


if __name__ == "__main__":
    main()
