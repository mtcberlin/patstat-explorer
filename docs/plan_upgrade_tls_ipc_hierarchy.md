# Upgrade Plan: `tls_ipc_hierarchy` → IPC 2026.01

> **Status: DONE**
> Created: 2026-02-08
> Completed: 2026-02-08

## What exists today

**Current table** (`tls_ipc_hierarchy`): 79,833 rows from IPC 2025.01, sourced from a pre-built SQLite database (`patent-classification-2025.db`). Schema: `symbol`, `symbol_short`, `symbol_patstat`, `kind`, `level`, `parent`, `parent_short`, `title_en`, `title_full`, `size`, `size_percent`.

**Current upload script** (`scripts/bigquery_migration/upload_ipc_hierarchy.py`): Reads from SQLite, adds `symbol_patstat` conversion and `title_full` chain, uploads to BigQuery with `WRITE_TRUNCATE`.

## What's available in IPC 2026.01

Source data in `context/ipc_analysis/ipc2026.01/` (~268 MB total):

| Source File | Records | What it adds |
|---|---|---|
| `EN_ipc_scheme_20260101.xml` | ~82,156 entries | Hierarchy, titles, cross-references |
| `ipc_valid_symbols_20260101.xml` | 80,145 symbols | `latestVersionIndicator` (when last modified) |
| `EN_ipc_title_list_20260101/` | 80,734 lines | Tab-separated titles (easy parsing alternative) |
| `EN_ipc_definitions_20260101.xml` | 11,716 definitions | Glossary, scope notes, limiting references |
| `EN_ipc_catchwordindex_20260101.xml` | ~22,867 entries | Keyword-to-symbol search index |
| `ipc_concordancelist_20260101.xml` | ~hundreds | 2025→2026 symbol changes/additions/deletions |
| `20260101_inventory_of_IPC_ever_used_symbols.csv` | ~92,856 rows | Historical: when every symbol was introduced/deprecated |
| `EN_ipc_warnings_20260101.xml` | 1,267 warnings | Reclassification status notes |

## Data gap analysis

Queried `tls209_appln_ipc` in BigQuery (2026-02-08):

| Metric | Value |
|---|---|
| Distinct symbols in `tls209_appln_ipc` | 81,336 |
| Valid symbols in IPC 2026.01 | 80,145 |
| Matched (have titles via hierarchy) | 69,227 (85.1%) |
| **Unmatched (deprecated, no titles)** | **12,109 (14.9%)** |
| Patent-IPC rows referencing unmatched symbols | **54,281,338 (14.5% of 374M)** |
| Ever-used CSV entries | 92,856 (has dates, no descriptions) |

Top unmatched symbols by usage: `G06F 17/30` (497K uses), `H04L 29/06` (482K), `H04L 29/08` (393K). These are symbols deprecated in earlier IPC editions (2018-2022) but still heavily referenced in PATSTAT.

The ever-used CSV provides introduction and deprecation dates but **no titles or descriptions** for deprecated symbols.

## Decided approach: 4 tables + SQLite-first

### Phase 1: Build local SQLite database

Script: `scripts/bigquery_migration/build_ipc_2026_database.py`

Parse all IPC 2026.01 source files into a local SQLite database (`patent-classification-2026.db`) for validation before BigQuery upload. This follows the same pattern as the existing 2025 database and the CPC workflow.

### Phase 2: Upload to BigQuery

Adapt `scripts/bigquery_migration/upload_ipc_hierarchy.py` to read from the new SQLite and upload all 4 tables.

---

### Table 1: `tls_ipc_hierarchy` (upgrade existing — ~80K rows)

The core lookup/join table. Update to 2026.01 and enrich.

| Column | Source | Purpose |
|---|---|---|
| `symbol` | scheme XML | Primary key (14-char zero-padded) |
| `symbol_short` | derived | Human-readable (`A01B1/02`) |
| `symbol_patstat` | derived | JOIN key to `tls209_appln_ipc.ipc_class_symbol` |
| `kind` | scheme XML | `s`/`c`/`u`/`m`/`1`-`9` |
| `level` | scheme XML | 2-14 |
| `parent` | scheme XML | Parent symbol |
| `parent_short` | derived | Parent readable |
| `title_en` | scheme XML / title list | English title |
| `title_full` | derived | Breadcrumb chain (`A > B > C`) |
| `ipc_version` | NEW | `'20260101'` — which edition this is |
| `latest_version_date` | NEW from valid_symbols | When this symbol was last modified (YYYYMMDD) |
| `introduced_date` | NEW from ever-used CSV | When this symbol was first introduced (YYYYMMDD) |
| `additional_content` | NEW from definitions XML | Combined plain text from glossary, scope notes, cross-references (~11.7K symbols). Searchable via LIKE queries. |
| `section_title` | NEW derived | e.g. "HUMAN NECESSITIES" for quick grouping |
| `class_title` | NEW derived | e.g. "AGRICULTURE; FORESTRY..." |
| `subclass_title` | NEW derived | e.g. "SOIL WORKING IN AGRICULTURE..." |

**Dropped columns** (vs. 2025 version):
- `size`, `size_percent` — removed for now. Will be recomputed later from `tls209_appln_ipc` (for IPC) and `tls224_appln_cpc` (for CPC hierarchy) as a separate task.

### Table 2: `tls_ipc_catchword` (new — ~23K rows)

Keyword search index for finding IPC symbols by natural language terms.

| Column | Type | Purpose |
|---|---|---|
| `catchword` | STRING | The keyword/phrase (e.g. "ABACUSES", "semiconductor") |
| `symbol` | STRING | Target IPC symbol (14-char zero-padded) |
| `symbol_short` | STRING | Readable form |
| `symbol_patstat` | STRING | JOIN key to `tls209_appln_ipc` |
| `parent_catchword` | STRING | Parent keyword for hierarchical catchwords |

**Use case — find patents by keyword:**
```sql
SELECT c.catchword, h.symbol_short, h.title_en, COUNT(DISTINCT a.appln_id) as patent_count
FROM `patstat-mtc.patstat.tls_ipc_catchword` c
JOIN `patstat-mtc.patstat.tls_ipc_hierarchy` h ON c.symbol = h.symbol
JOIN `patstat-mtc.patstat.tls209_appln_ipc` a ON h.symbol_patstat = a.ipc_class_symbol
WHERE c.catchword LIKE '%laser%'
GROUP BY c.catchword, h.symbol_short, h.title_en
ORDER BY patent_count DESC
```

### Table 3: `tls_ipc_concordance` (new — small, ~hundreds of rows)

Version-to-version change tracking. Schema allows stacking future concordances.

| Column | Type | Purpose |
|---|---|---|
| `from_symbol` | STRING | Symbol in previous version (14-char) |
| `from_symbol_patstat` | STRING | PATSTAT format for JOIN |
| `to_symbol` | STRING | Symbol in new version (14-char) |
| `to_symbol_patstat` | STRING | PATSTAT format for JOIN |
| `from_version` | STRING | `'20250101'` |
| `to_version` | STRING | `'20260101'` |
| `modification` | STRING | `c`=changed, `n`=new, `d`=deleted |
| `default_reclassification` | STRING | `Y`/`N` |
| `revision_project` | STRING | WIPO project code |

**Use case — find patents affected by reclassification:**
```sql
SELECT c.from_symbol_patstat, c.to_symbol_patstat, c.modification,
       COUNT(DISTINCT a.appln_id) as affected_patents
FROM `patstat-mtc.patstat.tls_ipc_concordance` c
JOIN `patstat-mtc.patstat.tls209_appln_ipc` a ON a.ipc_class_symbol = c.from_symbol_patstat
GROUP BY c.from_symbol_patstat, c.to_symbol_patstat, c.modification
ORDER BY affected_patents DESC
```

### Table 4: `tls_ipc_everused` (new — ~93K rows)

All IPC symbols ever used, with lifecycle dates. Covers the 12,109 deprecated symbols (54M patent-IPC rows) that have no entry in the current hierarchy.

| Column | Type | Purpose |
|---|---|---|
| `symbol` | STRING | IPC symbol (14-char zero-padded) |
| `symbol_patstat` | STRING | PATSTAT format for JOIN to `tls209_appln_ipc` |
| `introduced_date` | STRING | When first introduced (YYYYMMDD) |
| `deprecated_date` | STRING | When deprecated (YYYYMMDD), NULL if still active |
| `is_active` | BOOL | TRUE if symbol is in current IPC 2026.01 |

**Use case — identify deprecated classifications in a patent portfolio:**
```sql
SELECT e.symbol_patstat, e.introduced_date, e.deprecated_date,
       COUNT(DISTINCT a.appln_id) as patent_count
FROM `patstat-mtc.patstat.tls209_appln_ipc` a
JOIN `patstat-mtc.patstat.tls_ipc_everused` e ON a.ipc_class_symbol = e.symbol_patstat
WHERE e.is_active = FALSE
GROUP BY e.symbol_patstat, e.introduced_date, e.deprecated_date
ORDER BY patent_count DESC
LIMIT 20
```

## What we skip (and why)

- **French translations**: Low analytical value for SQL joins; adds complexity
- **Illustrations/images**: Not useful in BigQuery (no image search)
- **Fixed texts**: UI labels, not analytical data
- **Warnings**: Reclassification status — niche use, can be added later
- **Statistics XLS files**: Derivative data, recomputable from the hierarchy itself
- **Structured definitions** (glossary, scope notes as separate columns): Skipped for now; raw text goes into `additional_content` for LIKE search

## Implementation steps

### Step 1: `build_ipc_2026_database.py` — Build SQLite

New script in `scripts/bigquery_migration/`. Parse order:

1. **Scheme XML** (`EN_ipc_scheme_20260101.xml`) → `ipc` table: hierarchy, titles, parent-child
2. **Title list** (`EN_ipc_title_list_20260101/`) → cross-check and fill any title gaps
3. **Valid symbols** (`ipc_valid_symbols_20260101.xml`) → add `latest_version_date`
4. **Ever-used CSV** (`20260101_inventory_of_IPC_ever_used_symbols.csv`) → `ipc_everused` table + `introduced_date` into `ipc` table
5. **Definitions XML** (`EN_ipc_definitions_20260101.xml`) → extract plain text into `additional_content`
6. **Catchword index** (`EN_ipc_catchwordindex_20260101.xml`) → `ipc_catchword` table
7. **Concordance list** (`ipc_concordancelist_20260101.xml`) → `ipc_concordance` table
8. Derive `title_full`, `section_title`, `class_title`, `subclass_title`
9. Generate `symbol_patstat` for all tables
10. Write `ipc_metadata` table with provenance

### Step 2: Validate SQLite locally

- Row counts per table
- Level/kind distribution matches expectations
- `symbol_patstat` format spot checks
- `title_full` chain verification
- `additional_content` populated for ~11.7K symbols
- Catchword-to-symbol references resolve
- Concordance symbols are valid

### Step 3: Adapt `upload_ipc_hierarchy.py`

- Support new schema (drop `size`/`size_percent`, add new columns)
- Upload all 4 tables: `tls_ipc_hierarchy`, `tls_ipc_catchword`, `tls_ipc_concordance`, `tls_ipc_everused`
- `--dry-run` mode for preview
- Validation queries for each table

### Step 4: Upload to BigQuery and validate

- Upload with `WRITE_TRUNCATE` (replaces existing table)
- Run validation queries
- Test JOIN patterns with `tls209_appln_ipc`

## Future work (out of scope)

- Recompute `size`/`size_percent` for both `tls_ipc_hierarchy` and `tls_cpc_hierarchy` from `tls209_appln_ipc` and `tls224_appln_cpc`
- Stack additional concordance lists (older editions) to cover more deprecated symbol mappings
- Add French translations if needed
- Add warnings/reclassification status
