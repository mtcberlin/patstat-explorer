# Searching IPC and CPC Classifications in PATSTAT on BigQuery

**A practical guide for PATLIB staff**

---

## 1. Overview: Classification Tables in PATSTAT

PATSTAT stores classification data across several tables. Understanding which table to use — and what metadata each provides — is the key to getting reliable results.

| Table | Level | Classification | Columns | Use when... |
|---|---|---|---|---|
| `tls209_appln_ipc` | Application | IPC | 7 | You need IPC codes with full metadata (main vs. additional, version, assigning authority) |
| `tls224_appln_cpc` | Application | CPC | 2 | You need a quick CPC lookup per application (no metadata) |
| `tls225_docdb_fam_cpc` | DOCDB Family | CPC | 9 | You need CPC codes with full metadata (version, status, reclassification history) |
| `tls230_appln_techn_field` | Application | Derived | 3 | You want pre-computed broad technology fields (based on IPC) |
| `tls901_techn_field_ipc` | Reference | IPC → Tech field | 4 | You want to map IPC main groups to the 35 WIPO/Schmoch technology fields |
| `tls902_ipc_nace2` | Reference | IPC → NACE | 6 | You want to map IPC codes to industry sectors (with conditional logic) |

---

## 2. Understanding Classification Code Formatting

**Critical:** Classification symbols in PATSTAT use **fixed-width formatting with internal spaces**.

```
IPC example:  "A23L   7/117"    (not "A23L7/117")
CPC example:  "B22C  17/00"     (not "B22C17/00")
```

This means exact-match queries will fail if you don't account for the spacing. Always use `LIKE` patterns or `TRIM`/`REPLACE` functions.

---

## 3. IPC Table: tls209_appln_ipc (Detail)

This is the richest classification table. Each row assigns one IPC code to one application.

### Column Reference

| Column | Type | Values | Meaning |
|---|---|---|---|
| `appln_id` | INT64 | — | Foreign key to `tls201_appln` |
| `ipc_class_symbol` | STRING | `"H04L  29/06"` | The IPC code (fixed-width, with spaces) |
| `ipc_class_level` | STRING | `A`, `C`, `S`, ... | Hierarchical level of the code. In practice, most rows contain `A` (advanced/subgroup level). Other values represent coarser levels (section, class, subclass). For most search use cases, you can ignore this column. |
| `ipc_version` | DATE | `2006-01-01`, `2016-01-01` | Which edition of the IPC was applied |
| `ipc_value` | STRING | `I` / `A` | **I** = Inventive (main classification), **A** = Additional |
| `ipc_position` | STRING | `F` / `L` / ` ` | **F** = First listed, **L** = Later, blank = unspecified |
| `ipc_gener_auth` | STRING | `EP`, `US`, `CN`, `JP`, ... | Patent office that assigned this code |

### Key Filter Patterns

**Get only the primary IPC classification:**
```sql
SELECT appln_id, ipc_class_symbol
FROM tls209_appln_ipc
WHERE ipc_value = 'I'
  AND ipc_position = 'F'
```

**Search by IPC class (e.g., all H04L applications):**
```sql
SELECT appln_id, ipc_class_symbol
FROM tls209_appln_ipc
WHERE ipc_class_symbol LIKE 'H04L%'
```

**Search by IPC subclass and group:**
```sql
-- All applications in A61K 31/xx (pharmaceutical preparations with organic active ingredients)
SELECT appln_id, ipc_class_symbol
FROM tls209_appln_ipc
WHERE ipc_class_symbol LIKE 'A61K  31%'
```

> **Warning:** Note the double space in `'A61K  31%'`. The number of spaces depends on the digit count of the group number. When in doubt, use: `WHERE REPLACE(ipc_class_symbol, ' ', '') LIKE 'A61K31%'`

**Search across IPC versions:**
```sql
-- Find applications classified under IPC8 (2006+) only
SELECT appln_id, ipc_class_symbol
FROM tls209_appln_ipc
WHERE ipc_class_symbol LIKE 'H01M  10%'
  AND ipc_version >= '2006-01-01'
```

---

## 4. CPC Tables: tls224 vs. tls225

### tls224_appln_cpc — The Flat Index

Only two columns: `appln_id` and `cpc_class_symbol`. No metadata at all.

```sql
-- Simple CPC lookup per application
SELECT appln_id, cpc_class_symbol
FROM tls224_appln_cpc
WHERE cpc_class_symbol LIKE 'Y02E%'
```

This is useful for quick counts and joins, but you cannot distinguish main from additional classifications, and you have no version or reclassification history.

### tls225_docdb_fam_cpc — The Full Picture

This table operates at **DOCDB family level** (not individual application) and carries rich metadata.

| Column | Values | Meaning |
|---|---|---|
| `docdb_family_id` | INT64 | DOCDB patent family (join to `tls201_appln.docdb_family_id`) |
| `cpc_class_symbol` | STRING | CPC code (fixed-width with spaces) |
| `cpc_gener_auth` | `EP`, `US`, `KR` | Office that assigned the code |
| `cpc_version` | DATE | CPC scheme version used |
| `cpc_position` | `F` / `L` | First / Later |
| `cpc_value` | `I` / `A` | Inventive (main) / Additional |
| `cpc_action_date` | DATE | When the classification action happened |
| `cpc_status` | `B` / `R` | **B** = Original (base), **R** = Reclassified |
| `cpc_data_source` | `H` | Data source identifier |

### Key Filter Patterns

**Get only the primary CPC for each family:**
```sql
SELECT docdb_family_id, cpc_class_symbol
FROM tls225_docdb_fam_cpc
WHERE cpc_value = 'I'
  AND cpc_position = 'F'
```

**Find reclassified families (classification has been updated):**
```sql
SELECT docdb_family_id, cpc_class_symbol, cpc_action_date
FROM tls225_docdb_fam_cpc
WHERE cpc_status = 'R'
  AND cpc_class_symbol LIKE 'H04L%'
ORDER BY cpc_action_date DESC
```

**CPC search with join back to applications:**
```sql
SELECT a.appln_id, a.appln_filing_date, c.cpc_class_symbol
FROM tls201_appln a
JOIN tls225_docdb_fam_cpc c
  ON a.docdb_family_id = c.docdb_family_id
WHERE c.cpc_class_symbol LIKE 'Y02E  10%'
  AND c.cpc_value = 'I'
```

---

## 5. Bridging to Technology Fields and Industry Sectors

### IPC → 35 WIPO Technology Fields (Schmoch concordance)

PATSTAT provides two ways to get technology fields:

**Option A: Pre-computed (recommended for most use cases)**
```sql
SELECT a.appln_id, t.techn_field_nr, r.techn_field, r.techn_sector, t.weight
FROM tls230_appln_techn_field t
JOIN tls901_techn_field_ipc r
  ON t.techn_field_nr = r.techn_field_nr
JOIN tls201_appln a
  ON t.appln_id = a.appln_id
WHERE r.techn_sector = 'Electrical engineering'
```

The `weight` column in `tls230` reflects fractional counting: if an application has IPC codes spanning multiple tech fields, the weight distributes accordingly (e.g., 0.33 for each of three fields).

**Option B: Direct lookup via IPC main group**
```sql
SELECT DISTINCT techn_field_nr, techn_sector, techn_field
FROM tls901_techn_field_ipc
WHERE ipc_maingroup_symbol LIKE 'H04L%'
```

### IPC → NACE Rev. 2 Industry Sectors

The `tls902_ipc_nace2` concordance has conditional logic:

- `not_with_ipc`: If these IPC codes are also present on the same application, this mapping does NOT apply
- `unless_with_ipc`: This mapping only applies IF these IPC codes are also present

Many IPC codes map to no NACE sector (empty rows with weight 0). This is expected — not every patent technology maps cleanly to an industry.

---

## 6. Common Pitfalls

### Whitespace in classification symbols
Always use `LIKE` or strip spaces. Never assume a specific number of spaces.

### IPC vs. CPC scope
IPC is assigned by virtually all patent offices worldwide. CPC is primarily assigned by EPO, USPTO, and a few others (KIPO). If your analysis covers non-EP/US jurisdictions, IPC coverage will be broader.

### Application level vs. family level
`tls224_appln_cpc` gives you CPC per application but with zero metadata. `tls225_docdb_fam_cpc` gives you full metadata but at family level. Be clear about what unit of analysis you need.

### Multiple classifications per application
A single application typically has 3–10 IPC codes and potentially more CPC codes. Always decide upfront: are you counting by first/main classification only (`ipc_value = 'I' AND ipc_position = 'F'`), or do you want all classifications? This dramatically affects result counts.

### CPC-only codes (Y sections)
CPC has sections that don't exist in IPC, notably **Y02** (climate change mitigation) and **Y04** (nuclear energy). These are CPC-exclusive and extremely useful for green technology analysis.

---

## 7. Enhanced Setup: IPC Hierarchy Table

Standard PATSTAT does not include human-readable titles or the full parent-child hierarchy of the IPC. If your BigQuery instance has been extended with `tls_ipc_hierarchy` (uploaded from the official IPC XML scheme), you gain several powerful capabilities.

The hierarchy table contains 79,833 entries across 14 hierarchy levels, from sections (A–H) down to the deepest subgroups. It uses a `symbol_patstat` column pre-formatted for direct JOINs — no `REPLACE()` needed.

### Get English titles for classification codes

```sql
SELECT i.appln_id, i.ipc_class_symbol, h.title_en
FROM tls209_appln_ipc i
JOIN tls_ipc_hierarchy h ON i.ipc_class_symbol = h.symbol_patstat
WHERE i.ipc_value = 'I' AND i.ipc_position = 'F'
  AND STARTS_WITH(i.ipc_class_symbol, 'A61K')
LIMIT 10
```

### Navigate the IPC tree

Find all subgroups of a main group:
```sql
SELECT symbol_short, title_en, level
FROM tls_ipc_hierarchy
WHERE parent = 'H04L0041000000'
ORDER BY symbol
```

---

## 8. Technology Search by IPC Description

This is one of the most powerful features of the hierarchy table. Instead of memorizing IPC codes, you search by technology keywords in the English titles — then use the results to build your PATSTAT queries.

### Important: Search `title_full`, not `title_en`

IPC titles are **hierarchical fragments**. A subgroup title like `"with teeth"` or `"Details"` is meaningless on its own — it only makes sense in the context of its parent chain. The `title_full` column concatenates the ancestor titles from main group level downwards:

```
A01B1/04:
  title_en:   "with teeth"
  title_full: "Hand tools > Spades; Shovels > with teeth"
```

27% of all subgroup titles are 3 words or less. Searching `title_full` instead of `title_en` dramatically improves recall:

| Keyword | `title_en` hits | `title_full` hits | Improvement |
|---|---|---|---|
| "battery" | 37 | 87 | +135% |
| "charging" | 184 | 457 | +148% |
| "electric vehicle" | 10 | 71 | +610% |

**Always use `title_full` for keyword searches.** Use `title_en` only for display at a specific level.

### Step 1: Find relevant IPC codes by keyword

```sql
-- Find all IPC entries related to "battery" technology
SELECT symbol_short, level, kind, title_full
FROM tls_ipc_hierarchy
WHERE LOWER(title_full) LIKE '%battery%' OR LOWER(title_full) LIKE '%batteries%'
ORDER BY level, symbol
```

This returns results across all hierarchy levels — from subclasses like `H01M` (batteries for direct energy conversion) down to specific subgroups. Because `title_full` inherits parent context, you also find subgroups whose own `title_en` doesn't mention "battery" but whose parent chain does.

### Step 2: Use the codes in a PATSTAT patent search

```sql
-- Count patents per battery-related IPC code, last 5 years
SELECT h.symbol_short, h.title_full, COUNT(DISTINCT a.docdb_family_id) AS family_count
FROM tls209_appln_ipc i
JOIN tls201_appln a ON i.appln_id = a.appln_id
JOIN tls_ipc_hierarchy h ON i.ipc_class_symbol = h.symbol_patstat
WHERE (LOWER(h.title_full) LIKE '%battery%' OR LOWER(h.title_full) LIKE '%batteries%')
  AND i.ipc_value = 'I'
  AND a.appln_filing_year >= 2020
GROUP BY h.symbol_short, h.title_full
ORDER BY family_count DESC
LIMIT 20
```

### Practical examples

**Machine learning / AI:**
```sql
SELECT symbol_short, level, title_full
FROM tls_ipc_hierarchy
WHERE LOWER(title_full) LIKE '%machine learning%'
   OR LOWER(title_full) LIKE '%neural network%'
   OR LOWER(title_full) LIKE '%deep learning%'
ORDER BY level, symbol
```
Returns codes like `G06N20/00` (Machine learning), `G06N3/02` (Neural networks), and domain-specific entries like `H04L41/16` (ML for network management) or `G06V10/82` (neural networks for image recognition).

**Additive manufacturing / 3D printing:**
```sql
SELECT symbol_short, level, title_full
FROM tls_ipc_hierarchy
WHERE LOWER(title_full) LIKE '%additive manufactur%'
   OR LOWER(title_full) LIKE '%3d print%'
ORDER BY level, symbol
```
Returns the full B33 class (Additive Manufacturing Technology), plus cross-references in B22F (metal powder), B29C (plastics), and G06F (CAD for additive manufacturing).

**Electric vehicles (showcases the `title_full` advantage):**
```sql
SELECT symbol_short, level, title_full
FROM tls_ipc_hierarchy
WHERE LOWER(title_full) LIKE '%electric vehicle%'
ORDER BY level, symbol
```
With `title_en`, this would return only 10 subgroups. With `title_full`, it returns 71 — including detailed hybrid architectures under `B60K6` (whose own `title_en` says "Series-parallel type" but whose `title_full` includes "electric vehicles" from the parent chain).

### The two-step workflow: Discover → Count

This pattern works for any technology area. The key insight: IPC titles are standardized technical descriptions written by patent classification experts, and `title_full` inherits context from the full parent chain. A keyword search across 79,833 concatenated titles is effectively a curated technology taxonomy lookup — far more precise than free-text patent search, and it gives you the exact codes to filter on.

**Typical workflow for a technology landscape study:**

1. **Discover** relevant IPC codes via `title_full` keyword search
2. **Review** the results — filter by hierarchy level (`level = 5` for main groups gives a broad view; `level >= 6` adds specificity)
3. **Build** your PATSTAT query using the discovered `symbol_patstat` values as JOIN keys
4. **Refine** by combining IPC search with applicant names, filing countries, or date ranges

> **Tip:** Use `kind = 'm'` to restrict results to main groups only. This gives the broadest technology categories without drowning in subgroup-level detail. Expand to subgroups only after you've identified the right main groups.

---

## 9. Quick Reference: Which Table For What?

| I want to... | Use this table |
|---|---|
| Find patents by IPC code with full metadata | `tls209_appln_ipc` |
| Quick CPC lookup per application | `tls224_appln_cpc` |
| CPC analysis with version/reclassification tracking | `tls225_docdb_fam_cpc` |
| Map patents to 35 WIPO technology fields | `tls230_appln_techn_field` + `tls901_techn_field_ipc` |
| Map patents to industry sectors | `tls902_ipc_nace2` |
| Find Y02/Y04 climate-related patents | `tls224_appln_cpc` or `tls225_docdb_fam_cpc` |
| Compare classification across patent offices | `tls209_appln_ipc` (use `ipc_gener_auth`) or `tls225_docdb_fam_cpc` (use `cpc_gener_auth`) |
| Get English titles for IPC codes | `tls_ipc_hierarchy` (extended setup) |
| Navigate IPC parent-child hierarchy | `tls_ipc_hierarchy` (extended setup) |
| Search IPC by keyword in title | `tls_ipc_hierarchy` (extended setup) |

---

*Guide prepared for PATLIB staff. Based on PATSTAT Global on BigQuery, Spring 2025 edition. Section 7 requires the IPC hierarchy extension (IPC scheme version 2025.01).*
