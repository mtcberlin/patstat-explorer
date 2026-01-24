# PATSTAT Explorer

Patent analysis tools for the EPO PATSTAT database on Google BigQuery.

## Status

🚧 **Migration in Progress** (2026-01-24)

The project has been migrated from PostgreSQL to BigQuery. The Streamlit app will be updated shortly to use the new BigQuery backend.

## Repository Structure

```
patstat/
├── app.py                           # Streamlit web application
├── queries_bq.py                    # BigQuery queries (18 queries, 7 categories)
├── requirements.txt                 # Python dependencies
├── APP_REWRITE_BIGQUERY_PLAN.md     # App migration plan (PostgreSQL → BigQuery)
│
└── archive/                         # Archived/deprecated files
    ├── postgresql/                  # Old PostgreSQL implementation
    ├── migration/                   # BigQuery CSV migration tools (completed)
    ├── epo_tests/                   # EPO TIP environment tests
    └── synology_ssh_setup.md        # Synology NAS SSH setup docs
```

## Quick Start

### Prerequisites

1. **Google Cloud Access**
   ```bash
   # Install Google Cloud SDK
   brew install google-cloud-sdk

   # Authenticate
   gcloud auth application-default login
   gcloud config set project patstat-mtc
   ```

2. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Run the App

```bash
cp .env.example .env
# Edit .env if needed (defaults work for most cases)

streamlit run app.py
```

The app will be available at http://localhost:8501

## Query Categories

18 BigQuery queries across 7 stakeholder categories:

| Category | Queries | Description |
|----------|---------|-------------|
| **Overview** | 5 | Database stats, filing trends, IPC distribution |
| **Strategic Planning** | 2 | Country activity, green technology trends |
| **Technology Scouting** | 3 | AI/ERP patents, medical diagnostics, tech fields |
| **Competitive Intelligence** | 2 | Top applicants, geographic filing strategies |
| **Patent Prosecution** | 2 | Citation analysis, grant rates by office |
| **Regional Analysis (DE)** | 3 | Federal states, per-capita metrics, tech sectors |
| **Technology Transfer** | 1 | Fastest-growing G06Q subclasses |

## Database Architecture

**BigQuery Project:** `patstat-mtc`
**Dataset:** `patstat` (EU region)
**Tables:** 28 PATSTAT tables (~450GB total)

### Key Tables

| Table | Rows | Size | Description |
|-------|------|------|-------------|
| tls201_appln | 140M | ~25 GB | Patent applications |
| tls212_citation | 597M | ~40 GB | Citation data |
| tls224_appln_cpc | 436M | ~9 GB | CPC classifications |
| tls207_pers_appln | 408M | ~12 GB | Person-Application links |
| tls209_appln_ipc | 375M | ~15 GB | IPC classifications |
| tls211_pat_publn | 168M | ~10 GB | Publications |
| tls206_person | 98M | ~16 GB | Applicants/Inventors |

## Performance

| Metric | Value | Notes |
|--------|-------|-------|
| **First Run** | ~60-90s | All 18 queries, cold cache |
| **Cached** | ~5-10s | BigQuery query cache warm |
| **Single Query** | 0.3-7s | Depends on complexity |
| **Cost** | ~$5-10/month | Storage + query processing |

## Environment Configuration

The `.env.example` file contains:

```bash
# BigQuery Configuration
BIGQUERY_PROJECT=patstat-mtc
BIGQUERY_DATASET=patstat

# Optional: Service Account Key
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json

# Streamlit Settings
STREAMLIT_SERVER_PORT=8501
```

## Schema Compatibility

Our PATSTAT data is 98% compatible with EPO's BigQuery structure:

- ✅ **27 of 28 tables** have identical schemas
- ⚠️ **tls206_person** has 16 columns (EPO has 17 with additional `reg_code` field)
- ✅ **No impact** on queries - all queries tested and working

See `archive/migration/SCHEMA_ANALYSIS.md` for detailed comparison.

## Development

### Query Syntax

All queries use BigQuery SQL syntax:

```sql
-- Table names with backticks and full qualification
FROM `patstat-mtc.patstat.tls201_appln`

-- Type casting
CAST(field AS STRING)

-- Date arithmetic
DATE_DIFF(date1, date2, DAY)

-- Window functions
COUNT(*) OVER (PARTITION BY field)
```

### Adding New Queries

1. Edit `queries_bq.py`
2. Add query to appropriate category dictionary
3. Include metadata: `description`, `explanation`, `key_outputs`, `estimated_seconds_*`
4. Test in BigQuery console first
5. Update `app.py` if needed

## Migration History

### 2026-01-24: PostgreSQL → BigQuery

**Rationale:**
- 12x performance improvement (110s → 7s cached)
- Built-in query caching
- Alignment with EPO's PATSTAT environment
- Lower operational cost (~$5/month vs PostgreSQL server)

**Migrated:**
- ✅ 28 PATSTAT tables (450GB CSV → BigQuery)
- ✅ 18 queries converted to BigQuery syntax
- ✅ Schema validated against EPO structure

**Archived:**
- PostgreSQL queries (`archive/postgresql/queries_pg.py`)
- PostgreSQL test runner (`archive/postgresql/test_queries_pg.py`)
- CSV migration tools (`archive/migration/`)
- EPO test scripts (`archive/epo_tests/`)

See `APP_REWRITE_BIGQUERY_PLAN.md` for app migration details.

## Archived Components

The `archive/` directory contains deprecated but preserved code:

### PostgreSQL Implementation (Deprecated)
- `postgresql/queries_pg.py` - 20 PostgreSQL queries
- `postgresql/test_queries_pg.py` - Test runner
- **Reason:** Migrated to BigQuery for better performance

### Migration Tools (Completed)
- `migration/migrate_to_bq.py` - CSV to BigQuery loader
- `migration/bq_migration_plan.md` - Migration documentation
- `migration/schemas/` - EPO schema exports
- **Status:** Migration completed 2026-01-23

### EPO Tests (Reference)
- `epo_tests/test_queries_bq.py` - EPO TIP environment tests
- `epo_tests/inspect_epo_schema.py` - Schema extraction
- **Note:** Queries moved to root `queries_bq.py`

## Troubleshooting

### Authentication Issues

```bash
# Re-authenticate
gcloud auth application-default login

# Check current project
gcloud config get-value project

# List available projects
gcloud projects list
```

### Query Errors

- **"Not found: Table"** → Check `BIGQUERY_PROJECT` and `BIGQUERY_DATASET` in `.env`
- **"Permission denied"** → Ensure you have BigQuery Data Viewer role
- **"Quota exceeded"** → Check BigQuery quotas in Google Cloud Console

### Performance Issues

- First run is always slower (no cache)
- Subsequent runs use BigQuery query cache (~0.3-2s)
- Large result sets may take longer to download

## License

Internal use only.

---

**Last Updated:** 2026-01-24
**PATSTAT Version:** 2024 Autumn Edition
**BigQuery Dataset:** `patstat-mtc.patstat`
