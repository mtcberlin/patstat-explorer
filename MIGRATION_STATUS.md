# BigQuery Migration Status

**Date:** 2026-01-24 14:30
**Branch:** feature/bigquery-import

## Current Status: Ready to Execute Migration

### ✅ Completed

1. **Repository Cleanup**
   - Archived PostgreSQL code → `archive/postgresql/`
   - Archived migration tools → `archive/migration/`
   - Archived EPO tests → `archive/epo_tests/`
   - Moved `queries_bq.py` to root
   - Recovered `migrate_to_bq.py` to root
   - Updated README.md with new structure

2. **Schema Analysis**
   - Compared EPO BigQuery vs CSV schemas
   - **Result:** 98% compatible (27/28 tables identical)
   - **Difference:** `tls206_person` has 16 columns (EPO has 17)
   - **Impact:** None - queries don't use `reg_code` field
   - **Documentation:** `archive/migration/SCHEMA_ANALYSIS.md`

3. **CSV Extraction**
   - **Progress:** 63 of 68 CSVs extracted (93%)
   - **Size:** 489 GB extracted
   - **Location:** `~/mnt/synology/`
   - **Source:** Synology NAS (192.168.102.129)

4. **Migration Script Fixes**
   - Added missing `tls225_docdb_fam_cpc` to TABLE_CONFIG
   - Reduced `--max_bad_records` to 100 (early error detection)
   - Added explicit `--encoding=UTF-8` for international characters
   - Configured partitioning/clustering per EPO best practices

### 🔧 Next Steps

#### Step 1: Wait for CSV Extraction to Complete
```bash
# Check progress
ls ~/mnt/synology/*.csv | wc -l    # Should be ~68 when done
du -sh ~/mnt/synology/              # Expected ~500-550GB

# Monitor unzip process
ps aux | grep unzip
```

#### Step 2: Test Migration Script (Dry Run)
```bash
cd ~/Documents/development/patstat

# List detected files
python migrate_to_bq.py ~/mnt/synology --list

# Dry run (preview without loading)
python migrate_to_bq.py ~/mnt/synology --dry-run
```

**Expected output:**
- Should detect ~28 PATSTAT tables
- Should match files correctly (e.g., `tls201_part01.csv` → `tls201_appln`)
- Should show partitioning/clustering config

#### Step 3: Execute BigQuery Migration
```bash
# Full migration (all 28 tables)
python migrate_to_bq.py ~/mnt/synology

# OR single table first (test)
python migrate_to_bq.py ~/mnt/synology --table tls801_country
```

**Expected runtime:** 2-4 hours for all tables

#### Step 4: Verify Data Quality
```bash
# Check row counts in BigQuery
bq query 'SELECT COUNT(*) FROM `patstat-mtc.patstat.tls201_appln`'
# Expected: 140,525,582

bq query 'SELECT COUNT(*) FROM `patstat-mtc.patstat.tls206_person`'
# Expected: 97,853,865 (Part1: ~55M, Part2: ~43M)

bq query 'SELECT COUNT(*) FROM `patstat-mtc.patstat.tls212_citation`'
# Expected: 596,775,557
```

## Environment

### BigQuery
- **Project:** patstat-mtc
- **Dataset:** patstat (EU region)
- **Authentication:** gcloud CLI / Application Default Credentials

### Files
- **Migration Script:** `~/Documents/development/patstat/migrate_to_bq.py`
- **CSV Files:** `~/mnt/synology/*.csv`
- **Queries:** `~/Documents/development/patstat/queries_bq.py`

### Required Tools
```bash
# Should already be installed:
gcloud --version
bq version
python3 --version

# Authenticate (if needed):
gcloud auth application-default login
gcloud config set project patstat-mtc
```

## Expected Results

### Tables to Load (28 total)

| Table | Files | Expected Rows | Size |
|-------|-------|---------------|------|
| tls201_appln | 3 parts | 140,525,582 | ~25 GB |
| tls206_person | 2 parts | 97,853,865 | ~16 GB |
| tls207_pers_appln | Multiple | 408,478,469 | ~12 GB |
| tls209_appln_ipc | Multiple | 374,559,946 | ~15 GB |
| tls211_pat_publn | Multiple | 167,837,244 | ~10 GB |
| tls212_citation | Multiple | 596,775,557 | ~40 GB |
| tls224_appln_cpc | Multiple | 436,450,350 | ~9 GB |
| ... | ... | ... | ... |

**Total:** ~450-500 GB in BigQuery

### Partitioning Configuration

- **tls201_appln:** Range partitioned on `appln_filing_year` (1900-2030)
- **tls211_pat_publn:** Time partitioned on `publn_date`
- **Other tables:** No partitioning, clustering only

### Clustering Configuration

All tables clustered on relevant join/filter columns (see `migrate_to_bq.py` TABLE_CONFIG).

## Troubleshooting

### If Migration Fails

1. **Check Error Messages**
   ```bash
   # Errors will show which table/file failed
   # Common issues:
   # - Bad CSV rows (handled by --max_bad_records=100)
   # - UTF-8 encoding errors (should be fixed with --encoding=UTF-8)
   # - Schema mismatch (unlikely, autodetect should work)
   ```

2. **Resume from Failed Table**
   ```bash
   # Skip successful tables, retry failed ones manually
   python migrate_to_bq.py ~/mnt/synology --table <failed_table_name>
   ```

3. **Check BigQuery Quotas**
   - Google Cloud Console → BigQuery → Quotas
   - Should have plenty for this operation

### Known Issues

- **tls206_person:** CSV has 16 columns, EPO has 17 → No problem, autodetect handles this
- **Large files:** Some CSVs are 10+ GB → `bq load` handles this fine
- **International characters:** Fixed with `--encoding=UTF-8`

## Post-Migration

### Update Streamlit App

After successful migration, update the app:

```bash
# See APP_REWRITE_BIGQUERY_PLAN.md for details
# Main changes:
# 1. app.py: Replace PostgreSQL client with BigQuery client
# 2. queries_bq.py: Already in place
# 3. requirements.txt: Add google-cloud-bigquery
# 4. Test all 18 queries
```

## Quick Reference

```bash
# Check CSV extraction progress
ls ~/mnt/synology/*.csv | wc -l

# List migration script
python migrate_to_bq.py ~/mnt/synology --list

# Dry run
python migrate_to_bq.py ~/mnt/synology --dry-run

# Execute
python migrate_to_bq.py ~/mnt/synology

# Verify
bq query 'SELECT COUNT(*) FROM `patstat-mtc.patstat.tls201_appln`'

# Check all tables
bq ls patstat-mtc:patstat
```

## Recovery Commands

```bash
# If you need to restart the session:

# 1. Navigate to project
cd ~/Documents/development/patstat

# 2. Check git status
git status

# 3. Resume migration from this file
cat MIGRATION_STATUS.md

# 4. Continue from "Next Steps" section above
```

---

**Last Updated:** 2026-01-24 14:30
**Session State:** Ready for migration execution
**Waiting For:** CSV extraction to complete (63/68 done)
