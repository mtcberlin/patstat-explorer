# Plan: Improve & Extend Queries with PATSTAT MCP Server

**Status:** IMPLEMENTED
**Created:** 2026-02-08
**Branch:** develop

---

## 1. Context & Motivation

We now have a **PATSTAT MCP server** with 5 new classification reference tables on BigQuery:

| New Table | Rows | What It Provides | Platform |
|-----------|------|-----------------|----------|
| `tls_ipc_hierarchy` | 80,145 | Complete IPC 2026.01 tree with titles, breadcrumbs, definitions | BigQuery only |
| `tls_ipc_catchword` | 21,361 | Keyword-to-IPC search index (natural language discovery) | BigQuery only |
| `tls_ipc_concordance` | 1,193 | IPC version change map (2025.01 -> 2026.01) | BigQuery only |
| `tls_ipc_everused` | 92,856 | All IPC symbols ever used, incl. deprecated | BigQuery only |
| `tls_cpc_hierarchy` | 254,249 | Complete CPC hierarchy tree with titles, breadcrumbs | BigQuery only |

These tables are **not available on EPO TIP** (`epo.tipdata.patstat` / `PatstatClient`). All 28 standard PATSTAT tables are available on both BigQuery and TIP.

**Goal:** Add 5 new classification queries (BigQuery only), add a `platforms` field to all queries, and conditionally show/hide "Take to TIP" based on platform support.

**Origin:** The `"todo"` on Q04 from bmad Story 6.4 ("Add IPC text description") pointed to this need. The new tables make it possible, but adding title JOINs to existing queries would break TIP compatibility. Instead, we create dedicated classification queries.

**Deferred:** Stream A (add IPC/CPC titles to existing queries) and Stream B (add context queries Q43-Q53) are parked for now. The context query files remain in `context/1_*`, `context/2_*`, `context/3_*` for future use.

---

## 2. Technical Reference: JOIN Strategies for New Tables

### 2.1 `symbol_patstat` is NULL for sections, classes, and subclasses

The `tls_ipc_hierarchy` table only populates `symbol_patstat` for **main groups and subgroups** (kind = m, 1-9). For higher levels, it is NULL:

| kind | Level | Example `symbol_short` | `symbol_patstat` | `title_en` |
|------|-------|----------------------|-----------------|-----------|
| s | Section | `A` | **NULL** | HUMAN NECESSITIES |
| c | Class | `A61` | **NULL** | MEDICAL OR VETERINARY SCIENCE |
| u | Subclass | `A61B` | **NULL** | DIAGNOSIS; SURGERY; IDENTIFICATION |
| m | Main group | `A61B6/00` | `A61B   6/00` | Apparatus for radiation diagnosis |
| 1-9 | Subgroups | `A61B6/03` | `A61B   6/03` | Computed tomography [CT] |

### 2.2 Correct JOIN Patterns

| Use Case | Correct SQL |
|----------|------------|
| **Subclass title** for 4-char code | `JOIN tls_ipc_hierarchy h ON 'A61B' = h.symbol_short AND h.kind = 'u'` |
| **Exact IPC match** (main group / subgroup) | `JOIN tls_ipc_hierarchy h ON ipc.ipc_class_symbol = h.symbol_patstat` |
| **Section title** | `JOIN tls_ipc_hierarchy h ON 'A' = h.symbol AND h.kind = 's'` |
| **CPC exact match** | `JOIN tls_cpc_hierarchy h ON cpc.cpc_class_symbol = h.symbol_patstat` |

**IMPORTANT:** `SUBSTR(ipc_class_symbol, 1, 4)` gives 4-char **subclass** codes (`kind='u'`), NOT 3-char class codes (`kind='c'`).

### 2.3 Hierarchy Traversal (Recursive CTE)

```sql
-- Find all descendants of a main group (e.g., A61B 6/00)
WITH RECURSIVE ipc_subtree AS (
    SELECT symbol, symbol_patstat, title_en
    FROM tls_ipc_hierarchy
    WHERE symbol = 'A61B0006000000'

    UNION ALL

    SELECT h.symbol, h.symbol_patstat, h.title_en
    FROM tls_ipc_hierarchy h
    JOIN ipc_subtree d ON h.parent = d.symbol
)
SELECT * FROM ipc_subtree
```

---

## 3. Implementation

### 3.1 Add `platforms` field to all queries

Add a `"platforms"` field to every query in `queries_bq.py`:

```python
# Existing queries (all 42 + DQ01):
"platforms": ["bigquery", "tip"],

# New classification queries (Q54-Q58):
"platforms": ["bigquery"],
```

### 3.2 Conditional "Take to TIP" panel

In `modules/ui.py`, the `render_tip_panel()` call (line ~827) should check:

```python
if "tip" in query_info.get("platforms", ["bigquery", "tip"]):
    render_tip_panel(query_info, collected_params)
```

Default to `["bigquery", "tip"]` for backwards compatibility with any queries missing the field.

### 3.3 Add "Classification" category

Add `"Classification"` to the category system in `modules/config.py` (or wherever categories are defined). These queries are primarily for PATLIB stakeholders exploring the classification system.

### 3.4 New Queries (Q54-Q58)

All BigQuery only. New category: "Classification".

#### Q54: "What does an IPC/CPC class mean?"

Look up any classification symbol and get its full title, breadcrumb path, hierarchy position, and WIPO definition text.

- **Tables:** `tls_ipc_hierarchy`, `tls_cpc_hierarchy`
- **Parameters:** `classification_symbol` (text), `system` (select: IPC/CPC)
- **Tags:** PATLIB
- **Key outputs:** symbol, title_en, title_full, section_title, class_title, subclass_title, additional_content, kind, level

#### Q55: "Find IPC classes by keyword"

Search the catchword index for technology terms and discover relevant IPC symbols with titles.

- **Tables:** `tls_ipc_catchword`, `tls_ipc_hierarchy`
- **Parameters:** `keyword` (text)
- **Tags:** PATLIB, BUSINESS
- **Key outputs:** catchword, symbol_short, title_en, section_title, parent_catchword

#### Q56: "What IPC codes changed in the latest revision?"

Show reclassified, deleted, and new IPC symbols between IPC versions 2025.01 and 2026.01.

- **Tables:** `tls_ipc_concordance`, `tls_ipc_hierarchy`
- **Parameters:** `modification_type` (select: all/created/deleted/modified)
- **Tags:** PATLIB
- **Key outputs:** from_symbol, to_symbol, modification type, revision_project, title of new symbol

#### Q57: "How many patents use deprecated IPC codes?"

Analyze coverage of deprecated vs. active IPC codes in patent data. Helps understand data quality and historical code usage.

- **Tables:** `tls_ipc_everused`, `tls209_appln_ipc`
- **Parameters:** `year_range`
- **Tags:** PATLIB
- **Key outputs:** active/deprecated counts, coverage percentage, top deprecated codes with patent counts

#### Q58: "What are all subclasses under an IPC/CPC class?"

Hierarchical expansion — show the entire subtree of a classification node with indented tree view.

- **Tables:** `tls_ipc_hierarchy` / `tls_cpc_hierarchy`
- **Parameters:** `parent_symbol` (text), `system` (select: IPC/CPC), `max_depth` (select: 1-5)
- **Tags:** PATLIB
- **Key outputs:** symbol_short, title_en, kind, level, depth relative to parent

---

## 4. TODO Checklist

### Infrastructure
- [x] Add `"platforms": ["bigquery", "tip"]` to all 42 existing queries + DQ01
- [x] Add conditional "Take to TIP" check in `modules/ui.py`
- [x] Add "Classification" as 5th query category
- [x] Update test suite for new platforms field and Classification category

### New Queries
- [x] **Q54**: IPC/CPC class lookup (definition, hierarchy, breadcrumb)
- [x] **Q55**: Keyword-to-IPC discovery (catchword search)
- [x] **Q56**: IPC revision changes (concordance)
- [x] **Q57**: Deprecated IPC code analysis (everused)
- [x] **Q58**: Classification subtree expansion (hierarchy)

### Documentation
- [ ] Update `docs/query-catalog.md`
- [ ] Update README query table

---

## 5. Summary

| What | Count | Platform |
|------|-------|----------|
| Existing queries get `platforms` field | 42 + DQ01 | bigquery, tip |
| New classification queries | 5 (Q54-Q58) | bigquery only |
| **Total after implementation** | **47 + DQ01** | |

The "Take to TIP" panel becomes platform-aware, and we get 5 new classification exploration queries that leverage the IPC/CPC hierarchy tables.

---

## 6. Deferred Work

These items are parked for future consideration:

- **Stream A:** Add IPC/CPC titles to ~13 existing queries (Q04, Q18, Q28, Q42, etc.) — would break TIP compatibility unless done via Python-side enrichment
- **Stream B:** Add 11 queries from context files (Q43-Q53) — generalized company analysis, technology diversification, IPC combo trends
- **Q04 todo:** "Add IPC text description, not only the symbol" — remains in code, could be resolved via Python-side lookup or as a BigQuery-only variant later
