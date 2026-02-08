# Implementation Log: IPC 2026.01 Upgrade

**Date:** 2026-02-08
**Branch:** develop

## What was done

Upgraded the `tls_ipc_hierarchy` table from IPC 2025.01 (79,833 rows) to IPC 2026.01 (80,145 rows) and created 3 new companion tables in BigQuery (`patstat-mtc.patstat`).

## Tables uploaded

| Table | Rows | Description |
|---|---|---|
| `tls_ipc_hierarchy` | 80,145 | Core hierarchy — symbols, titles, breadcrumbs, definitions, dates |
| `tls_ipc_catchword` | 21,361 | Keyword-to-symbol search index from WIPO catchword index |
| `tls_ipc_concordance` | 1,193 | Version change mapping (2025.01 → 2026.01) |
| `tls_ipc_everused` | 92,856 | All IPC symbols ever used, with introduction/deprecation dates |

## Schema changes to `tls_ipc_hierarchy`

**Added columns:**
- `ipc_version` — edition identifier (`'20260101'`)
- `latest_version_date` — when the symbol was last modified (from valid symbols XML)
- `introduced_date` — when the symbol was first introduced (from ever-used CSV)
- `additional_content` — plain text from definitions XML (glossary, scope notes, references); available for 2,148 symbols, searchable via LIKE
- `section_title` — denormalized title of the level-2 ancestor (e.g. "HUMAN NECESSITIES")
- `class_title` — denormalized title of the level-3 ancestor
- `subclass_title` — denormalized title of the level-4 ancestor

**Dropped columns:**
- `size` — pre-computed patent count, to be recomputed later from `tls209_appln_ipc`
- `size_percent` — same

## Data sources

All from `context/ipc_analysis/ipc2026.01/` (WIPO IPC 2026.01 official release):

| Source | Used for |
|---|---|
| `EN_ipc_scheme_20260101.xml` (19.6 MB) | Hierarchy structure, titles, parent-child |
| `EN_ipc_title_list_20260101/` (8 files) | Title cross-check (0 gaps found) |
| `ipc_valid_symbols_20260101.xml` | `latest_version_date` (79,557 matched) |
| `20260101_inventory_of_IPC_ever_used_symbols.csv` | `introduced_date` + `ipc_everused` table |
| `EN_ipc_definitions_20260101.xml` | `additional_content` (2,148 symbols) |
| `EN_ipc_catchwordindex_20260101.xml` | `ipc_catchword` table (18,261 distinct keywords) |
| `ipc_concordancelist_20260101.xml` | `ipc_concordance` table (347 changed, 846 deleted) |

## Data gap analysis

Queried `tls209_appln_ipc` (374M rows, 81,336 distinct symbols):

| Category | Count | % of distinct symbols |
|---|---|---|
| Matched in `tls_ipc_hierarchy` | 69,037 | 84.9% |
| In `tls_ipc_everused` only (deprecated, no titles) | 1,769 | 2.2% |
| Unknown (not in any IPC 2026.01 source) | 10,530 | 12.9% |
| **Total coverage** | **70,806** | **87.1%** |

The 10,530 unknown symbols are deprecated IPC codes removed before the ever-used inventory tracking began. Top examples: `G06F 17/30` (497K uses, deprecated 2018), `H04L 29/06` (482K uses, deprecated 2021).

## Scripts

- `scripts/bigquery_migration/build_ipc_2026_database.py` — parses all XML/CSV sources into SQLite (`patent-classification-2026.db`, 65 KB). Runs steps 1-8 sequentially. Supports `--skip-rebuild` for incremental enrichment.
- `scripts/bigquery_migration/upload_ipc_hierarchy.py` — reads SQLite, uploads all 4 tables to BigQuery. Supports `--dry-run` and `--table` to upload individual tables.

## Validation results

All passed:
- Row counts match across SQLite and BigQuery
- Level/kind distribution: 8 sections → 132 classes → 655 subclasses → 7,668 main groups → 71,682 subgroups (14 depth levels)
- `symbol_patstat` format correct (e.g. `'A01B   1/00'`)
- JOIN with `tls209_appln_ipc` works
- Catchword search for "laser" returns relevant IPC codes (H01S, B23K26/00, A61N5/067, etc.)
- Concordance symbols resolve correctly
- 0 unresolved catchword references, 0 invalid concordance targets

## Observations

- **Title mismatches (10,770):** The title list files include cross-references in parentheses (e.g. "Hand tools (edge trimmers for lawns A01G3/06)") that the scheme XML title extraction omits. This is expected — the scheme XML gives the clean title, the title list gives the full annotated title.
- **Definitions coverage (2.7%):** Only 2,148 of 80,145 symbols have definitions. This is normal — WIPO provides definitions primarily at class/subclass level, not for individual groups.
- **Ever-used vs hierarchy gap (140):** 140 symbols in the hierarchy are not in the ever-used CSV, likely new symbols introduced in 2026.01 not yet tracked.

## Future work

- Recompute `size`/`size_percent` for `tls_ipc_hierarchy` and `tls_cpc_hierarchy` from `tls209_appln_ipc` and `tls224_appln_cpc`
- Stack older concordance lists to map more deprecated symbols
- Add French translations if needed
- Add reclassification warnings
