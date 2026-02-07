# PATSTAT Schema Analysis

## EPO BigQuery vs PostgreSQL CSV Comparison

**Analysis Date:** 2026-01-24
**EPO Schema Source:** `migration/schemas/epo_patstat_schema_20260123_214726.json`
**PostgreSQL Source:** Synology CSVs (75GB)

## Summary

Our PATSTAT CSV files are **98% compatible** with EPO's BigQuery structure. Only 1 table has a minor schema difference.

## Key Table Comparison

| Table | PG Columns | EPO Columns | Status | Notes |
|-------|------------|-------------|--------|-------|
| tls201_appln | 27 | 27 | ✅ Match | Main applications table |
| tls206_person | 16 | 17 | ⚠️ Diff | Missing `reg_code` field |
| tls207_pers_appln | 4 | 4 | ✅ Match | Person-Application links |
| tls209_appln_ipc | 7 | 7 | ✅ Match | IPC classifications |
| tls211_pat_publn | 10 | 10 | ✅ Match | Publications |
| tls212_citation | 10 | 10 | ✅ Match | Citation network |
| tls224_appln_cpc | 2 | 2 | ✅ Match | CPC classifications |

## Schema Difference Details

### tls206_person (16 vs 17 columns)

**PostgreSQL columns (16):**
1. person_id
2. person_name
3. person_name_orig_lg
4. person_address
5. person_ctry_code
6. nuts
7. nuts_level
8. doc_std_name_id
9. doc_std_name
10. psn_id
11. psn_name
12. psn_level
13. psn_sector
14. han_id
15. han_name
16. han_harmonized

**EPO additional column:**
17. reg_code (STRING, nullable) - Regional code identifier

## Migration Impact

**Impact Level:** LOW
**Action Required:** None

The missing `reg_code` field will not affect:
- Data loading (CSV has valid 16-column structure)
- BigQuery import (`--autodetect` will create correct 16-column schema)
- Query compatibility (our queries don't reference `reg_code`)
- Data integrity (all existing queries tested against 16-column structure)

## Row Count Expectations

Based on EPO BigQuery and PostgreSQL sources:

| Table | Expected Rows | EPO Rows | Size (GB) |
|-------|---------------|----------|-----------|
| tls201_appln | 140,525,582 | 140,525,582 | ~25 |
| tls206_person | 97,853,865 | 97,853,865 | ~16 |
| tls207_pers_appln | 408,478,469 | 408,478,469 | ~12 |
| tls209_appln_ipc | 374,559,946 | 374,559,946 | ~15 |
| tls211_pat_publn | 167,837,244 | 167,837,244 | ~10 |
| tls212_citation | 596,775,557 | 596,775,557 | ~40 |
| tls224_appln_cpc | 436,450,350 | 436,450,350 | ~9 |

## Recommendations

1. ✅ Proceed with migration using current CSV files
2. ✅ Use `--autodetect` for schema inference (already configured)
3. ✅ Verify row counts post-migration match expected values
4. ⚠️ Document that `tls206_person.reg_code` is not available in our dataset
5. 💡 Consider requesting updated CSVs with `reg_code` for future refreshes

## Migration Script Status

**File:** `migrate_to_bq.py`
**Status:** ✅ Ready for execution
**Recent fixes:**
- Added missing `tls225_docdb_fam_cpc` configuration
- Reduced `--max_bad_records` to 100 (early error detection)
- Added explicit `--encoding=UTF-8` for international characters
- Configured partitioning and clustering per EPO best practices

## Next Steps

1. Wait for CSV extraction to complete (~19/68 files extracted)
2. Run `--dry-run` to validate file detection
3. Execute migration to BigQuery
4. Verify row counts and data quality
