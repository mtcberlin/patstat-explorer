---
title: 'Upload IPC Hierarchy to BigQuery'
slug: 'upload-ipc-hierarchy-bigquery'
created: '2026-02-07'
status: 'in-progress'
stepsCompleted: [1, 2, 3]
tech_stack: ['python', 'google-cloud-bigquery', 'sqlite3']
files_to_modify: ['scripts/bigquery_migration/upload_ipc_hierarchy.py']
code_patterns: ['bigquery-client', 'sqlite-reader']
test_patterns: ['validation-queries']
---

# Tech-Spec: Upload IPC Hierarchy to BigQuery

**Created:** 2026-02-07

## Overview

### Problem Statement

PATSTAT's classification tables (`tls209_appln_ipc`, `tls224_appln_cpc`) store IPC/CPC codes but lack:
- Human-readable titles (what does `A23L7/117` actually mean?)
- The full parent-child hierarchy for navigation
- A normalized symbol format for reliable JOINs (PATSTAT uses space-padded format like `A23L   7/117`)

### Solution

Upload the IPC classification hierarchy from SQLite (`patent-classification-2025.db`, 79,833 entries, version 2025.01) to BigQuery as a new reference table `tls_ipc_hierarchy`. Generate computed columns:
- `symbol_patstat` — PATSTAT-compatible space-padded format for direct JOINs
- `title_full` — Concatenated ancestor chain for meaningful context

### Scope

**In Scope:**
- Python upload script reading SQLite → BigQuery
- Symbol format conversion functions (zero-padded ↔ PATSTAT ↔ short)
- `title_full` generation (ancestor chain from main group level)
- Validation queries to verify JOIN compatibility

**Out of Scope:**
- MCP server extension (separate ticket)
- CPC hierarchy (only IPC for now)
- French titles (`title_fr` left as placeholder)

## Context for Development

### Codebase Patterns

Existing BigQuery migration scripts in `scripts/bigquery_migration/`:
- `migrate_to_bq.py` — CSV loader with schema definitions
- Uses `google-cloud-bigquery` Python client
- Project: `patstat-mtc`, Dataset: `patstat`

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `context/ipc_analysis/patent-classification-2025.db` | Source SQLite database |
| `context/ipc_analysis/mcp-patstat-extension-spec.md` | Detailed spec with conversion functions |
| `scripts/bigquery_migration/migrate_to_bq.py` | Existing migration patterns |

### Technical Decisions

1. **Target table:** `patstat-mtc.patstat.tls_ipc_hierarchy`
2. **Symbol format conversion:** Python functions verified against all 79,039 subgroup entries with zero errors
3. **title_full strategy:** Concatenate from main group level (5) downward with ` > ` separator
4. **Write disposition:** `WRITE_TRUNCATE` (full replace on re-upload)

## Implementation Plan

### Tasks

- [ ] **Task 1:** Create upload script `scripts/bigquery_migration/upload_ipc_hierarchy.py`
  - Read SQLite database
  - Build lookup dict for title_full generation
  - Convert symbols to PATSTAT format
  - Upload to BigQuery with schema

- [ ] **Task 2:** Implement conversion functions
  - `zeropad_to_patstat()` — `A23L0007117000` → `A23L   7/117`
  - `patstat_to_zeropad()` — reverse
  - `build_title_full()` — ancestor chain builder

- [ ] **Task 3:** Run upload and validate
  - Execute script against `patent-classification-2025.db`
  - Verify 79,833 rows loaded
  - Run validation queries

### Acceptance Criteria

```gherkin
GIVEN the SQLite database with 79,833 IPC entries
WHEN the upload script is executed
THEN tls_ipc_hierarchy contains 79,833 rows in BigQuery

GIVEN a PATSTAT IPC code like 'A23L   7/117'
WHEN JOINing tls209_appln_ipc.ipc_class_symbol to tls_ipc_hierarchy.symbol_patstat
THEN the JOIN succeeds and returns the English title

GIVEN an IPC subgroup like 'A01B1/04' (level 7)
WHEN querying title_full
THEN it returns the ancestor chain: "Hand tools > Spades; Shovels > with teeth"

GIVEN the 4 test queries from the spec
WHEN executed against the uploaded table
THEN all return expected results
```

## Additional Context

### Dependencies

- `google-cloud-bigquery` Python package
- BigQuery authentication (`gcloud auth login` or service account)
- Access to `patstat-mtc` project

### Testing Strategy

Run these validation queries post-upload:

```sql
-- 1. Row count
SELECT COUNT(*) FROM tls_ipc_hierarchy  -- Should be 79,833

-- 2. JOIN test
SELECT i.appln_id, i.ipc_class_symbol, h.title_en
FROM tls209_appln_ipc i
JOIN tls_ipc_hierarchy h ON i.ipc_class_symbol = h.symbol_patstat
WHERE i.appln_id = 8668048

-- 3. Hierarchy navigation
SELECT symbol_short, title_en, level
FROM tls_ipc_hierarchy
WHERE parent = 'H04L0041000000'

-- 4. title_full verification
SELECT symbol_short, title_en, title_full
FROM tls_ipc_hierarchy
WHERE symbol_short = 'A01B1/04'
```

### Notes

- Script location: `scripts/bigquery_migration/upload_ipc_hierarchy.py`
- Can be re-run when new IPC version is released (currently 2025.01)
- `symbol_patstat` is NULL for section/class/subclass levels (no slash in format)
