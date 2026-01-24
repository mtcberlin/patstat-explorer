# Streamlit App Migration: PostgreSQL → BigQuery

**Status:** Planning
**Branch:** `feature/migrate-to-bigquery`
**Date:** 2026-01-24

## Overview

Clean migration from PostgreSQL to BigQuery backend. No hybrid approach - complete replacement.

## Goals

1. ✅ Remove all PostgreSQL dependencies
2. ✅ Use existing BigQuery queries from `epo_tests/queries_bq.py`
3. ✅ Maintain same Streamlit UI/UX
4. ✅ Improve performance (~7s cached vs 110s+ PostgreSQL)
5. ✅ Use own BigQuery instance (`patstat-mtc.patstat`)

## Files to Change

### 1. Move Queries
```bash
# Existing BigQuery queries are ready
cp epo_tests/queries_bq.py queries.py
rm queries_pg.py
```

### 2. Update app.py

**Remove:**
```python
import psycopg2
from urllib.parse import urlparse

DATABASE_URL = os.getenv("DATABASE_URL")
# PostgreSQL connection code
```

**Add:**
```python
from google.cloud import bigquery

PROJECT_ID = os.getenv("BIGQUERY_PROJECT", "patstat-mtc")
DATASET_ID = os.getenv("BIGQUERY_DATASET", "patstat")

# Initialize BigQuery client
client = bigquery.Client(project=PROJECT_ID)

def run_query(sql):
    """Execute BigQuery query and return results as DataFrame"""
    # Replace table placeholders with fully qualified names
    sql_qualified = sql.replace(
        "`tls",
        f"`{PROJECT_ID}.{DATASET_ID}.tls"
    )

    query_job = client.query(sql_qualified)
    df = query_job.to_dataframe()

    return df, query_job.total_bytes_processed
```

### 3. Table Name Qualification

BigQuery requires fully qualified table names:
```sql
-- queries_bq.py has:
FROM `tls201_appln`

-- Must become:
FROM `patstat-mtc.patstat.tls201_appln`
```

**Solution:** String replacement in `run_query()` function (see above)

### 4. Update requirements.txt

**Remove:**
```
psycopg2-binary==2.9.9
```

**Add:**
```
google-cloud-bigquery==3.25.0
google-cloud-bigquery-storage==2.26.0  # For faster downloads
pyarrow>=15.0.0  # Required for to_dataframe()
db-dtypes>=1.2.0  # BigQuery data types
```

**Keep:**
```
streamlit==1.39.0
pandas==2.2.3
python-dotenv==1.0.1
```

### 5. Update .env.example

**Remove:**
```
DATABASE_URL=postgresql://user:pass@host:5432/patstat
```

**Add:**
```
# BigQuery Configuration
BIGQUERY_PROJECT=patstat-mtc
BIGQUERY_DATASET=patstat

# Optional: Service Account Key (if not using gcloud auth)
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### 6. Update README.md

**Replace PostgreSQL Setup Section:**

```markdown
## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure BigQuery Access

**Option A: Use gcloud (Recommended for local development)**
```bash
gcloud auth application-default login
gcloud config set project patstat-mtc
```

**Option B: Service Account Key**
```bash
# Download service account key from Google Cloud Console
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env if needed (defaults work for most cases)
```

### 4. Run App

```bash
streamlit run app.py
```

The app will be available at http://localhost:8501
```

**Update Performance Metrics:**
```markdown
## Performance

- **First Run:** ~60-90s (all 20 queries)
- **Cached:** ~5-10s (BigQuery query cache)
- **Single Query:** ~0.3-7s depending on complexity
```

## Migration Checklist

### Phase 1: Preparation (Current)
- [x] Audit existing BigQuery queries in `epo_tests/queries_bq.py`
- [x] Document schema compatibility
- [x] Plan migration steps
- [ ] Create feature branch

### Phase 2: Code Changes
- [ ] Copy `epo_tests/queries_bq.py` → `queries.py`
- [ ] Update `app.py` with BigQuery client
- [ ] Add table name qualification logic
- [ ] Update `requirements.txt`
- [ ] Update `.env.example`
- [ ] Update `README.md`

### Phase 3: Testing
- [ ] Test all 20 queries against `patstat-mtc.patstat`
- [ ] Verify performance (should be ~7s cached)
- [ ] Check error handling
- [ ] Test with fresh BigQuery session (no cache)

### Phase 4: Cleanup
- [ ] Remove `queries_pg.py`
- [ ] Remove `test_queries_pg.py`
- [ ] Move PostgreSQL files to `archive/`
- [ ] Update git branch

### Phase 5: Documentation
- [ ] Update comments in code
- [ ] Add BigQuery cost estimates to README
- [ ] Document any query differences found during testing

## Query Syntax - Already Converted ✓

All queries in `epo_tests/queries_bq.py` already use BigQuery syntax:

| PostgreSQL | BigQuery | Status |
|------------|----------|--------|
| `tls201_appln` | `` `tls201_appln` `` | ✓ |
| `::TEXT` | `CAST(x AS STRING)` | ✓ |
| `(date1 - date2)` | `DATE_DIFF(date1, date2, DAY)` | ✓ |
| `VALUES (...)` | `UNNEST([STRUCT(...)])` | ✓ |
| `DOUBLE PRECISION` | `FLOAT64` | ✓ |

## Cost Estimation

**BigQuery Pricing (EU region):**
- Storage: $0.02/GB/month × 150GB = **$3/month**
- Query Processing: $5/TB × ~0.5TB/month = **$2.50/month**

**Total: ~$5-10/month** (much cheaper than PostgreSQL server)

## Known Differences from EPO Environment

### Schema
- `tls206_person` has 16 columns (EPO has 17 with `reg_code`)
- No impact on queries - `reg_code` not used

### Table Names
- EPO uses: `` `p-epo-tip-prj-3a1f.p_epo_tip_euwe4_bqd_patstatb.tls201_appln` ``
- We use: `` `patstat-mtc.patstat.tls201_appln` ``
- String replacement handles this automatically

## Rollback Plan

If BigQuery migration fails:
1. PostgreSQL code is in `archive/`
2. Restore from branch: `git checkout main`
3. Files can be moved back from archive if needed

But: **Not expected - queries already tested in EPO environment**

## Timeline

1. **Now:** CSV migration to BigQuery running
2. **After CSV migration:** Create feature branch
3. **Day 1:** Code changes + testing
4. **Day 2:** Documentation + merge to main
5. **Result:** Single production-ready BigQuery-based app

## Success Criteria

- ✅ All 20 queries execute successfully
- ✅ Performance < 10s for cached queries
- ✅ No PostgreSQL dependencies remaining
- ✅ Clean git history with feature branch
- ✅ Updated documentation
