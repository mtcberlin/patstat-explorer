# PATSTAT MCP Server Update: IPC 2026.01 Tables

**Date:** 2026-02-08
**BigQuery project:** `patstat-mtc`, dataset: `patstat`

## Changes

### Modified table: `tls_ipc_hierarchy`

Upgraded from IPC 2025.01 (79,833 rows) to IPC 2026.01 (80,145 rows). Schema changed — old columns dropped, new columns added.

**New schema:**

| Column | Type | Mode | Description |
|---|---|---|---|
| `symbol` | STRING | REQUIRED | Full IPC symbol in canonical 14-character zero-padded format (e.g. `A01B0007000000`). Primary key. |
| `symbol_short` | STRING | NULLABLE | Human-readable short form (e.g. `A01B7/00`). |
| `symbol_patstat` | STRING | NULLABLE | PATSTAT spacing format for JOINing to `tls209_appln_ipc.ipc_class_symbol` (e.g. `A01B   7/00`). NULL for sections/classes/subclasses. |
| `kind` | STRING | REQUIRED | Classification level: `s`=section, `c`=class, `u`=subclass, `m`=main group, `1`-`9`=subgroup depth. |
| `level` | INT64 | REQUIRED | Numeric hierarchy depth: 2=section, 3=class, 4=subclass, 5=main group, 6-14=subgroup depths. |
| `parent` | STRING | REQUIRED | Symbol of the parent node (canonical format). `IPC` for top-level sections. |
| `parent_short` | STRING | NULLABLE | Human-readable short form of parent. |
| `title_en` | STRING | NULLABLE | English title of this classification entry. |
| `title_full` | STRING | NULLABLE | Full breadcrumb title joined by ` > ` from main group down (e.g. `Hand tools > Spades; Shovels > with teeth`). |
| `ipc_version` | STRING | NULLABLE | IPC edition identifier: `20260101`. |
| `latest_version_date` | STRING | NULLABLE | When symbol was last modified (YYYYMMDD format). |
| `introduced_date` | STRING | NULLABLE | When symbol was first introduced (YYYYMMDD format). |
| `additional_content` | STRING | NULLABLE | Combined plain text from WIPO definitions (glossary, scope notes, limiting references). Available for ~2,148 symbols. Searchable via LIKE. |
| `section_title` | STRING | NULLABLE | Title of the level-2 ancestor section (e.g. `HUMAN NECESSITIES`). Denormalized for convenience. |
| `class_title` | STRING | NULLABLE | Title of the level-3 ancestor class (e.g. `AGRICULTURE; FORESTRY; ANIMAL HUSBANDRY; HUNTING; TRAPPING; FISHING`). |
| `subclass_title` | STRING | NULLABLE | Title of the level-4 ancestor subclass. |

**Removed columns** (vs. previous version): `size` (INT64), `size_percent` (FLOAT64). These will be recomputed in a future update.

### New table: `tls_ipc_catchword`

21,361 rows. Keyword search index mapping natural language terms to IPC symbols. Sourced from WIPO's official catchword index.

| Column | Type | Mode | Description |
|---|---|---|---|
| `catchword` | STRING | REQUIRED | Keyword or phrase (e.g. `LASER(S)`, `CUTTING metal by laser beam`). |
| `symbol` | STRING | REQUIRED | Target IPC symbol in 14-char zero-padded format. |
| `symbol_short` | STRING | NULLABLE | Human-readable form. |
| `symbol_patstat` | STRING | NULLABLE | PATSTAT spacing format for JOINing to `tls209_appln_ipc`. |
| `parent_catchword` | STRING | NULLABLE | Parent keyword for hierarchical catchword entries. |

**Typical use:** Find IPC codes by keyword, then JOIN to patent data:
```sql
SELECT c.catchword, h.symbol_short, h.title_en
FROM tls_ipc_catchword c
JOIN tls_ipc_hierarchy h ON c.symbol = h.symbol
WHERE LOWER(c.catchword) LIKE '%laser%'
```

### New table: `tls_ipc_concordance`

1,193 rows. Maps symbol changes between IPC 2025.01 and 2026.01. Schema supports stacking future version concordances.

| Column | Type | Mode | Description |
|---|---|---|---|
| `from_symbol` | STRING | REQUIRED | Symbol in previous IPC version (14-char format). |
| `from_symbol_patstat` | STRING | NULLABLE | PATSTAT format of from_symbol. |
| `to_symbol` | STRING | REQUIRED | Symbol in new IPC version (14-char format). |
| `to_symbol_patstat` | STRING | NULLABLE | PATSTAT format of to_symbol. |
| `from_version` | STRING | REQUIRED | Source edition (e.g. `20250101`). |
| `to_version` | STRING | REQUIRED | Target edition (e.g. `20260101`). |
| `modification` | STRING | NULLABLE | `c`=changed (347 entries), `d`=deleted (846 entries). |
| `default_reclassification` | STRING | NULLABLE | `Y` if reclassification is default, `N` otherwise. |
| `revision_project` | STRING | NULLABLE | WIPO revision project code (e.g. `C529`). |

**Typical use:** Find patents affected by reclassification:
```sql
SELECT c.from_symbol_patstat, c.to_symbol_patstat, c.modification,
       COUNT(DISTINCT a.appln_id) as affected
FROM tls_ipc_concordance c
JOIN tls209_appln_ipc a ON a.ipc_class_symbol = c.from_symbol_patstat
GROUP BY 1, 2, 3 ORDER BY affected DESC
```

### New table: `tls_ipc_everused`

92,856 rows. Complete inventory of all IPC symbols ever used, with lifecycle dates. Covers 12,851 deprecated symbols not in the current hierarchy — important because these deprecated symbols are referenced by 54M patent-IPC assignments (14.5% of `tls209_appln_ipc`).

| Column | Type | Mode | Description |
|---|---|---|---|
| `symbol` | STRING | REQUIRED | IPC symbol in 14-char zero-padded format. |
| `symbol_patstat` | STRING | NULLABLE | PATSTAT format for JOINing to `tls209_appln_ipc`. |
| `introduced_date` | STRING | NULLABLE | When symbol was first introduced (YYYYMMDD). Dates range from `19680901` to `20260101`. |
| `deprecated_date` | STRING | NULLABLE | When symbol was deprecated (YYYYMMDD). NULL if still active. |
| `is_active` | BOOL | NULLABLE | TRUE if symbol is in current IPC 2026.01 edition. |

**Typical use:** Identify deprecated classifications in patent data:
```sql
SELECT e.symbol_patstat, e.deprecated_date,
       COUNT(DISTINCT a.appln_id) as patent_count
FROM tls209_appln_ipc a
JOIN tls_ipc_everused e ON a.ipc_class_symbol = e.symbol_patstat
WHERE e.is_active = FALSE
GROUP BY 1, 2 ORDER BY patent_count DESC
```

## Key relationships

- `tls_ipc_hierarchy.symbol_patstat` = `tls209_appln_ipc.ipc_class_symbol` (primary JOIN)
- `tls_ipc_catchword.symbol` = `tls_ipc_hierarchy.symbol` (keyword → hierarchy)
- `tls_ipc_concordance.from_symbol_patstat` / `to_symbol_patstat` = `tls209_appln_ipc.ipc_class_symbol`
- `tls_ipc_everused.symbol_patstat` = `tls209_appln_ipc.ipc_class_symbol` (covers deprecated symbols)
- `tls_ipc_hierarchy.symbol` links at subclass level to `tls901_techn_field_ipc.ipc_maingroup_symbol`
