# PATSTAT Data Loading Guide

**Generated:** 2026-01-26 | **Target:** Google BigQuery

## Overview

This guide covers loading EPO PATSTAT data into Google BigQuery. PATSTAT is distributed as CSV files (~450 GB total) that need to be uploaded to BigQuery.

## Prerequisites

1. **PATSTAT Subscription** - Download from [EPO BDDS](https://publication-bdds.apps.epo.org/raw-data/products/subscription/product/17)
2. **Google Cloud Project** with BigQuery enabled
3. **Service Account** with BigQuery Data Editor role
4. **`bq` CLI** installed and authenticated

## Quick Start

```bash
# Navigate to project
cd /path/to/patstat

# Load all tables (interactive confirmation)
python context/load_patstat_local.py /path/to/csv PROJECT_ID DATASET

# Example
python context/load_patstat_local.py ~/Downloads/patstat_2025a patstat-mtc patstat
```

## Loading Script

### `load_patstat_local.py`

The loading script in `context/load_patstat_local.py` handles:

1. **Table Discovery** - Finds all `tls*_part*.csv` files
2. **Table Creation** - Creates BigQuery tables with schema, partitioning, and clustering
3. **Data Loading** - Uses `bq load` to stream data directly (no GCS required)
4. **Progress Tracking** - Saves progress to resume interrupted loads
5. **Row Validation** - Verifies row counts after loading

### Usage

```bash
python context/load_patstat_local.py CSV_DIR PROJECT DATASET [OPTIONS]

Arguments:
  CSV_DIR     Directory containing PATSTAT CSV files
  PROJECT     GCP project ID (e.g., patstat-mtc)
  DATASET     BigQuery dataset name (e.g., patstat)

Options:
  --dry-run     Show commands without executing
  --resume      Resume from previous run (uses progress file)
  --verify      Only verify row counts, no loading
  --tables      Comma-separated list of specific tables
  --skip-create Skip table creation (tables must exist)
```

### Examples

```bash
# Preview what will be loaded
python context/load_patstat_local.py ~/Downloads/patstat patstat-mtc patstat --dry-run

# Load only specific tables
python context/load_patstat_local.py ~/Downloads/patstat patstat-mtc patstat \
  --tables tls201_appln,tls206_person,tls207_pers_appln

# Resume interrupted load
python context/load_patstat_local.py ~/Downloads/patstat patstat-mtc patstat --resume

# Verify row counts after loading
python context/load_patstat_local.py ~/Downloads/patstat patstat-mtc patstat --verify
```

## Table Definitions

Each table is created with optimized BigQuery settings:

### Example: `tls201_appln`

```sql
-- Schema
appln_id:INTEGER, appln_auth:STRING, appln_nr:STRING, ...

-- Partitioning (for large tables with year columns)
--range_partitioning=appln_filing_year,1900,2030,1

-- Clustering (for common filter/join columns)
--clustering_fields=appln_auth,docdb_family_id,granted
```

### Optimization Strategy

| Table Type | Partitioning | Clustering |
|------------|--------------|------------|
| Applications | `appln_filing_year` | `appln_auth`, `docdb_family_id` |
| Persons | None | `person_ctry_code`, `psn_id` |
| Classifications | None | `appln_id`, `ipc_class_symbol` |
| Citations | None | `pat_publn_id`, `cited_appln_id` |
| Publications | None | `appln_id`, `publn_auth` |

## Expected Row Counts

| Table | Expected Rows |
|-------|---------------|
| tls201_appln | 140,525,582 |
| tls202_appln_title | 119,259,497 |
| tls203_appln_abstr | 96,536,721 |
| tls204_appln_prior | 53,194,773 |
| tls205_tech_rel | 4,160,592 |
| tls206_person | 97,853,865 |
| tls207_pers_appln | 408,478,469 |
| tls209_appln_ipc | 374,559,946 |
| tls210_appln_n_cls | 26,217,769 |
| tls211_pat_publn | 167,837,244 |
| tls212_citation | 596,775,557 |
| tls214_npl_publn | 43,569,746 |
| tls215_citn_categ | 1,346,861,951 |
| tls216_appln_contn | 5,819,586 |
| tls222_appln_jp_class | 428,299,335 |
| tls224_appln_cpc | 436,450,350 |
| tls225_docdb_fam_cpc | 224,464,483 |
| tls226_person_orig | 120,640,365 |
| tls227_pers_publn | 533,935,876 |
| tls228_docdb_fam_citn | 307,465,107 |
| tls229_appln_nace2 | 166,322,438 |
| tls230_appln_techn_field | 166,549,096 |
| tls231_inpadoc_legal_event | 498,252,938 |
| tls801_country | 242 |
| tls803_legal_event_code | 4,185 |
| tls901_techn_field_ipc | 771 |
| tls902_ipc_nace2 | 863 |
| tls904_nuts | 2,056 |

## Troubleshooting

### Bad Records

The script allows up to 100 bad records per file (`--max_bad_records=100`). Common issues:

- **Encoding errors** - Some files may have non-UTF8 characters
- **Quoted newlines** - Handled by `--allow_quoted_newlines`
- **Jagged rows** - Handled by `--allow_jagged_rows`

### Large Files

For very large tables (>100GB), loading may take several hours. The script:
- Has a 2-hour timeout per file
- Tracks progress to allow resuming
- Displays loading speed (GB/hour)

### Resume After Error

If loading fails:

1. Check the error message in output
2. Fix the issue (e.g., permissions, quota)
3. Run with `--resume` to continue from last successful file

```bash
# Resume from progress file
python context/load_patstat_local.py ~/Downloads/patstat patstat-mtc patstat --resume
```

Progress is saved to `.patstat_load_progress.json` in the CSV directory.

## Cost Estimation

| Operation | Estimated Cost |
|-----------|----------------|
| Initial load | ~$100-200 (one-time) |
| Storage | ~$10/month |
| Queries | ~$5-10/month (typical usage) |

BigQuery charges:
- **Storage:** $0.02/GB/month (active), $0.01/GB/month (long-term)
- **Queries:** $5/TB scanned (first 1TB/month free)

## Alternative: PostgreSQL

For local development, see `context/create_patstat_tables.sql` which provides:
- PostgreSQL schema definitions
- COPY commands for loading CSVs
- Index creation statements

```bash
# Example PostgreSQL load
psql -d patstat < context/create_patstat_tables.sql
```

Note: PostgreSQL requires a server with ~500GB disk space and 32GB+ RAM for reasonable performance.

## Data Source

PATSTAT data is available from:

- **EPO BDDS:** https://publication-bdds.apps.epo.org/
- **Product ID:** 17 (PATSTAT Global)
- **Update Frequency:** Twice yearly (Spring/Autumn)
- **Current Version:** 2025 Autumn Edition
