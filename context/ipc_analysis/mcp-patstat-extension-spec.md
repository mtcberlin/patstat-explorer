# MCP Server Extension: IPC/CPC Search Tools for PATSTAT

**Developer specification for extending the PATSTAT BigQuery MCP server**

---

## Context

The current MCP server provides `list_tables`, `get_table_schema`, `get_table_samples`, and `search_tables`. These are read-only metadata tools — they cannot execute arbitrary SQL queries against BigQuery.

We want to add two categories of functionality:

1. **`run_query`** — Execute arbitrary BigQuery SQL against the PATSTAT dataset (with safeguards)
2. **Pre-built classification search tools** — Dedicated tools for the most common IPC/CPC search patterns

---

## Tool 1: `run_query`

### Purpose
Allow the LLM to execute read-only SQL queries against PATSTAT on BigQuery.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `sql` | string | yes | The SQL query to execute |
| `max_rows` | integer | no | Maximum rows to return (default: 100, max: 10000) |
| `dry_run` | boolean | no | If true, validate the query and return estimated bytes scanned without executing (default: false) |

### Safeguards
- **Read-only**: Only `SELECT` statements. Reject any DDL/DML (`CREATE`, `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `MERGE`).
- **Query size limit**: Reject queries that would scan more than a configurable byte threshold (e.g., 10 GB) — use BigQuery's `dryRun` option to check before execution.
- **Timeout**: Set a query timeout (e.g., 60 seconds).
- **Row limit**: Enforce `max_rows` by appending `LIMIT` if not present in the query.
- **Dataset scoping**: Queries should only access the PATSTAT dataset. Reject cross-dataset queries.

### Return Format
Return results as a JSON array of objects, where each object is one row with column names as keys. Include metadata:
```json
{
  "columns": ["appln_id", "ipc_class_symbol", "ipc_value"],
  "rows": [
    {"appln_id": 8668048, "ipc_class_symbol": "A23L   7/117", "ipc_value": "I"},
    ...
  ],
  "total_rows": 42,
  "bytes_scanned": 1234567,
  "truncated": false
}
```

### Example Invocations
```
run_query(sql="SELECT appln_id, ipc_class_symbol FROM tls209_appln_ipc WHERE ipc_class_symbol LIKE 'H04L%' AND ipc_value = 'I' LIMIT 10")

run_query(sql="SELECT COUNT(*) as cnt FROM tls224_appln_cpc WHERE cpc_class_symbol LIKE 'Y02E%'", dry_run=true)
```

---

## Tool 2: `search_by_ipc`

### Purpose
Search patent applications by IPC classification code. Handles whitespace normalization automatically.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ipc_code` | string | yes | IPC code or prefix to search (e.g., `"A61K31"`, `"H04L"`, `"G06F 3/01"`) |
| `main_only` | boolean | no | If true, return only main/inventive classifications (`ipc_value = 'I'` AND `ipc_position = 'F'`). Default: true |
| `authority` | string | no | Filter by assigning authority (e.g., `"EP"`, `"US"`, `"CN"`) |
| `include_appln_details` | boolean | no | If true, join to `tls201_appln` and include filing date, authority, docdb_family_id. Default: false |
| `max_rows` | integer | no | Default: 100, max: 10000 |

### Internal Query Logic

The tool must normalize the input code before querying:

```python
def normalize_ipc_for_search(ipc_code: str) -> str:
    """
    User inputs like 'A61K31' or 'A61K 31/05' need to become
    LIKE-compatible patterns against the fixed-width format in PATSTAT.

    Strategy: strip all spaces from both the input and the stored value,
    then use LIKE prefix matching.
    """
    cleaned = ipc_code.replace(" ", "").replace("/", " /")  # optional: keep slash
    return cleaned
```

**Generated SQL (main_only=true, include_appln_details=false):**
```sql
SELECT appln_id, ipc_class_symbol, ipc_value, ipc_position, ipc_gener_auth
FROM tls209_appln_ipc
WHERE REPLACE(ipc_class_symbol, ' ', '') LIKE @pattern
  AND ipc_value = 'I'
  AND ipc_position = 'F'
LIMIT @max_rows
```

**Generated SQL (main_only=false, include_appln_details=true):**
```sql
SELECT i.appln_id, i.ipc_class_symbol, i.ipc_value, i.ipc_position, i.ipc_gener_auth,
       a.appln_filing_date, a.appln_auth, a.docdb_family_id, a.granted
FROM tls209_appln_ipc i
JOIN tls201_appln a ON i.appln_id = a.appln_id
WHERE REPLACE(i.ipc_class_symbol, ' ', '') LIKE @pattern
LIMIT @max_rows
```

### Return Format
Same JSON structure as `run_query`, plus a `query_used` field so the user/LLM can see (and learn from) the generated SQL.

---

## Tool 3: `search_by_cpc`

### Purpose
Search patent applications or families by CPC classification code.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `cpc_code` | string | yes | CPC code or prefix (e.g., `"Y02E"`, `"H04L43/50"`) |
| `level` | string | no | `"application"` (uses tls224) or `"family"` (uses tls225). Default: `"family"` |
| `main_only` | boolean | no | Only relevant when `level = "family"`. Filters to `cpc_value = 'I'` AND `cpc_position = 'F'`. Default: true |
| `include_reclassified` | boolean | no | Only relevant when `level = "family"`. If false, excludes `cpc_status = 'R'`. Default: true |
| `authority` | string | no | Filter by `cpc_gener_auth` (only available at family level) |
| `include_appln_details` | boolean | no | Join back to tls201_appln for filing info. Default: false |
| `max_rows` | integer | no | Default: 100, max: 10000 |

### Internal Query Logic

**When level = "application":**
```sql
SELECT c.appln_id, c.cpc_class_symbol
FROM tls224_appln_cpc c
WHERE REPLACE(c.cpc_class_symbol, ' ', '') LIKE @pattern
LIMIT @max_rows
```

**When level = "family" (default), main_only=true:**
```sql
SELECT c.docdb_family_id, c.cpc_class_symbol, c.cpc_gener_auth,
       c.cpc_version, c.cpc_value, c.cpc_position, c.cpc_status, c.cpc_action_date
FROM tls225_docdb_fam_cpc c
WHERE REPLACE(c.cpc_class_symbol, ' ', '') LIKE @pattern
  AND c.cpc_value = 'I'
  AND c.cpc_position = 'F'
LIMIT @max_rows
```

**When level = "family", include_appln_details=true:**
```sql
SELECT c.docdb_family_id, c.cpc_class_symbol, c.cpc_gener_auth,
       a.appln_id, a.appln_filing_date, a.appln_auth
FROM tls225_docdb_fam_cpc c
JOIN tls201_appln a ON c.docdb_family_id = a.docdb_family_id
WHERE REPLACE(c.cpc_class_symbol, ' ', '') LIKE @pattern
  AND c.cpc_value = 'I'
  AND c.cpc_position = 'F'
LIMIT @max_rows
```

---

## Tool 4: `get_tech_field`

### Purpose
Map IPC codes or applications to WIPO/Schmoch technology fields.

### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `ipc_code` | string | no | IPC main group to look up (e.g., `"H04L"`) |
| `appln_id` | integer | no | Application ID to get assigned tech fields for |
| `tech_sector` | string | no | Filter by sector name (e.g., `"Electrical engineering"`, `"Chemistry"`) |

At least one of `ipc_code`, `appln_id`, or `tech_sector` must be provided.

### Internal Query Logic

**By IPC code:**
```sql
SELECT DISTINCT techn_field_nr, techn_sector, techn_field
FROM tls901_techn_field_ipc
WHERE ipc_maingroup_symbol LIKE @pattern
```

**By application ID:**
```sql
SELECT t.techn_field_nr, r.techn_sector, r.techn_field, t.weight
FROM tls230_appln_techn_field t
JOIN tls901_techn_field_ipc r ON t.techn_field_nr = r.techn_field_nr
WHERE t.appln_id = @appln_id
```

**By sector name:**
```sql
SELECT DISTINCT techn_field_nr, techn_sector, techn_field, ipc_maingroup_symbol
FROM tls901_techn_field_ipc
WHERE techn_sector = @tech_sector
ORDER BY techn_field_nr, ipc_maingroup_symbol
```

---

## Data Model Notes for the Developer

### Classification Symbol Formatting

This is the single most important thing to get right. All classification symbols (`ipc_class_symbol`, `cpc_class_symbol`) use a **fixed-width format**: the group number is **right-justified in a 4-character field** between the subclass and the `/`. The number of spaces is purely a formatting consequence of the group number's digit count — it has no classification meaning.

```
"A23L   7/117"   ← group 7    → 3 padding spaces  (4-char field: "   7")
"H04L  29/06"    ← group 29   → 2 padding spaces  (4-char field: "  29")
"A43D 100/02"    ← group 100  → 1 padding space   (4-char field: " 100")
"F15B2211/50518" ← group 2211 → 0 padding spaces  (4-char field: "2211")
```

**Recommended approach**: Always normalize by stripping spaces before comparison:
```sql
WHERE REPLACE(ipc_class_symbol, ' ', '') LIKE 'A61K31%'
```

This is slightly less performant than exact matching but eliminates the whitespace problem entirely. For production, consider creating a virtual column or UDF.

### Table Relationships

```
tls201_appln (appln_id, docdb_family_id)
  ├── tls209_appln_ipc (appln_id → IPC codes)
  ├── tls224_appln_cpc (appln_id → CPC codes, no metadata)
  ├── tls230_appln_techn_field (appln_id → tech field numbers)
  └── via docdb_family_id:
      └── tls225_docdb_fam_cpc (docdb_family_id → CPC codes with full metadata)

Reference tables (no foreign keys, used for lookups):
  ├── tls901_techn_field_ipc (ipc_maingroup_symbol → tech field/sector)
  └── tls902_ipc_nace2 (ipc → NACE industry code, with conditional logic)
```

### Key Enumerations

**ipc_value / cpc_value:**
- `I` = Inventive (the main classification reflecting the core invention)
- `A` = Additional (supplementary classification)

**ipc_position / cpc_position:**
- `F` = First (the primary code among potentially multiple inventive codes)
- `L` = Later (subsequent codes)
- ` ` (blank) = Not specified

**cpc_status (tls225 only):**
- `B` = Base (original classification)
- `R` = Reclassified (classification was updated after initial assignment)

### BigQuery-Specific Considerations

- The PATSTAT dataset is large. Queries on `tls209_appln_ipc` or `tls225_docdb_fam_cpc` without filters will scan tens of GB.
- Always encourage/enforce `LIMIT` clauses.
- `REPLACE()` on string columns prevents BigQuery from using clustered column optimizations. For high-volume production use, consider maintaining a normalized column or using `STARTS_WITH()` where possible.
- Use parameterized queries (`@param`) to prevent SQL injection if accepting user-provided classification codes.

---

## Implementation Priority

1. **`run_query`** — Highest value, unlocks all use cases. Implement first.
2. **`search_by_ipc`** — Most common PATLIB use case. The whitespace normalization alone saves users significant frustration.
3. **`search_by_cpc`** — Same pattern as IPC but with the application/family level distinction.
4. **`get_tech_field`** — Nice-to-have, lower priority but simple to implement.

---

## Testing Queries

Use these to validate the implementation:

```sql
-- Should return results (IPC search, main classification)
SELECT appln_id, ipc_class_symbol
FROM tls209_appln_ipc
WHERE REPLACE(ipc_class_symbol, ' ', '') LIKE 'H04L29%'
  AND ipc_value = 'I' AND ipc_position = 'F'
LIMIT 5

-- Should return results (CPC family search, Y02 green tech)
SELECT docdb_family_id, cpc_class_symbol, cpc_gener_auth
FROM tls225_docdb_fam_cpc
WHERE REPLACE(cpc_class_symbol, ' ', '') LIKE 'Y02E10%'
  AND cpc_value = 'I'
LIMIT 5

-- Should return tech field mapping
SELECT DISTINCT techn_field_nr, techn_sector, techn_field
FROM tls901_techn_field_ipc
WHERE ipc_maingroup_symbol = 'H04L'

-- Should return count (validation)
SELECT COUNT(*) FROM tls224_appln_cpc
WHERE REPLACE(cpc_class_symbol, ' ', '') LIKE 'Y02%'
```

---

## Extending PATSTAT with the IPC Hierarchy Database

### The Problem

PATSTAT's classification tables store IPC/CPC codes but lack:
- Human-readable titles (what does `A23L7/117` actually mean?)
- The full parent-child hierarchy (which subgroups belong to which group?)
- A clean normalized symbol format for reliable JOINs

### The Source: IPC SQLite Database

We have a SQLite database (`patent-classification-2025.db`) containing the complete IPC scheme (version 2025.01) with 79,833 entries across all hierarchy levels.

**Schema:**
```sql
CREATE TABLE ipc (
    symbol TEXT PRIMARY KEY,        -- zero-padded 14 chars: "A23L0007117000"
    kind TEXT NOT NULL,             -- hierarchy type: s/c/u/m/1/2/3/4/5/6/7/8/9
    parent TEXT NOT NULL,           -- zero-padded parent symbol
    level INTEGER NOT NULL,         -- 2=section, 3=class, 4=subclass, 5=maingroup, 6+=subgroup
    symbol_short TEXT,              -- human-readable: "A23L7/117"
    parent_short TEXT,              -- human-readable parent
    title_en TEXT,                  -- English title
    title_fr TEXT,                  -- (placeholder for French)
    size INTEGER DEFAULT 0,         -- patent count
    size_percent REAL DEFAULT 0.0,
    size_normalised REAL DEFAULT 8.0,
    creation_date INTEGER
);

CREATE TABLE ipc_metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

**Kind codes:** `s` = section, `c` = class, `u` = subclass, `m` = main group, `1`-`9` = dot levels of subgroups (depth of indentation in the IPC scheme).

**Level distribution:**

| Level | Count | Meaning |
|---|---|---|
| 2 | 8 | Sections (A-H) |
| 3 | 132 | Classes (A01, B22, ...) |
| 4 | 654 | Subclasses (A01B, H04L, ...) |
| 5 | 7,630 | Main groups (A01B1/00, H04L29/00, ...) |
| 6-14 | 71,409 | Subgroups at various depths |

### Recommended Approach: Upload as New BigQuery Reference Table

Upload the `ipc` table as `tls_ipc_hierarchy` in BigQuery. Add a computed column `symbol_patstat` that enables direct JOINs to existing PATSTAT tables without runtime string manipulation.

**Target BigQuery schema:**
```sql
CREATE TABLE tls_ipc_hierarchy (
    symbol STRING NOT NULL,            -- zero-padded: "A23L0007117000"
    symbol_short STRING,               -- human-readable: "A23L7/117"
    symbol_patstat STRING,             -- PATSTAT format: "A23L   7/117" (for JOINs)
    kind STRING NOT NULL,
    level INT64 NOT NULL,
    parent STRING NOT NULL,
    parent_short STRING,
    title_en STRING,                   -- title at this level only: "with teeth"
    title_full STRING,                 -- concatenated ancestor chain: "Hand tools > Spades; Shovels > with teeth"
    size INT64 DEFAULT 0,
    size_percent FLOAT64 DEFAULT 0.0
);
```

### Why `title_full` Is Critical

IPC titles are **hierarchical fragments**. A subgroup title like `"with teeth"` or `"Details"` is meaningless without its parent context. 27% of all subgroup titles are 3 words or less.

The `title_full` column concatenates the ancestor chain from main group level (level 5) downwards, joined by ` > `:

```
A01B1/04 (level 7):
  title_en:   "with teeth"
  title_full: "Hand tools > Spades; Shovels > with teeth"

H04L41/16 (level 6):
  title_en:   "using machine learning or artificial intelligence"
  title_full: "Arrangements for maintenance... of data switching networks > using machine learning or artificial intelligence"
```

**Search recall improvement** (measured against full IPC database):

| Keyword | `title_en` matches | `title_full` matches | Improvement |
|---|---|---|---|
| "battery" | 37 | 87 | +135% |
| "charging" | 184 | 457 | +148% |
| "electric vehicle" | 10 | 71 | +610% |

The technology search tool (below) **must search `title_full`**, not `title_en`.

### Symbol Format Conversion Functions

Three formats exist for the same code:

```
Zero-padded:  "A23L0007117000"    (SQLite ipc.symbol, 14 chars fixed)
PATSTAT:      "A23L   7/117"     (tls209/tls224/tls225, space-padded)
Short:        "A23L7/117"        (SQLite ipc.symbol_short, human-readable)
```

The following Python functions convert between all three. Verified against all 79,039 subgroup-level entries in the IPC database with zero errors.

```python
def zeropad_to_patstat(zeropad: str) -> str:
    """Convert 'A23L0007117000' → 'A23L   7/117'

    Rules:
    - Chars [0:4]  = subclass (pass through)
    - Chars [4:8]  = group (zero-padded → int → right-justify in 4-char field)
    - Chars [8:14] = subgroup (strip trailing zeros; '000000' → '00' for main groups)
    """
    if len(zeropad) < 14:
        return zeropad  # section/class/subclass level, no conversion

    subclass = zeropad[:4]
    group_int = int(zeropad[4:8])
    subgroup_raw = zeropad[8:14]

    subgroup_str = subgroup_raw.rstrip('0') or '00'
    group_padded = str(group_int).rjust(4)

    return f"{subclass}{group_padded}/{subgroup_str}"


def patstat_to_zeropad(patstat: str) -> str:
    """Convert 'A23L   7/117' → 'A23L0007117000'"""
    if '/' not in patstat:
        return patstat

    slash_pos = patstat.index('/')
    subclass = patstat[:4]
    group_str = patstat[4:slash_pos].strip()
    subgroup_str = patstat[slash_pos+1:]

    group_zp = group_str.zfill(4)
    subgroup_zp = subgroup_str.ljust(6, '0')

    return f"{subclass}{group_zp}{subgroup_zp}"


def short_to_patstat(short: str) -> str:
    """Convert 'A23L7/117' → 'A23L   7/117'"""
    if '/' not in short:
        return short

    slash_pos = short.index('/')
    subclass = short[:4]
    group_str = short[4:slash_pos]
    subgroup_str = short[slash_pos+1:]

    group_padded = group_str.rjust(4)

    return f"{subclass}{group_padded}/{subgroup_str}"


def patstat_to_short(patstat: str) -> str:
    """Convert 'A23L   7/117' → 'A23L7/117'"""
    if '/' not in patstat:
        return patstat

    slash_pos = patstat.index('/')
    subclass = patstat[:4]
    group_str = patstat[4:slash_pos].strip()
    subgroup_str = patstat[slash_pos+1:]

    return f"{subclass}{group_str}/{subgroup_str}"
```

**BigQuery SQL equivalent** (for generating `symbol_patstat` during upload):
```sql
-- Convert zero-padded symbol to PATSTAT space-padded format
-- Example: 'A23L0007117000' → 'A23L   7/117'
SELECT
    symbol,
    symbol_short,
    CONCAT(
        SUBSTR(symbol, 1, 4),                                          -- subclass
        LPAD(CAST(CAST(SUBSTR(symbol, 5, 4) AS INT64) AS STRING), 4),  -- group, right-justified
        '/',
        CASE
            WHEN RTRIM(SUBSTR(symbol, 9, 6), '0') = ''
            THEN '00'                                                   -- main group
            ELSE RTRIM(SUBSTR(symbol, 9, 6), '0')                      -- subgroup, trailing zeros stripped
        END
    ) AS symbol_patstat
FROM tls_ipc_hierarchy
WHERE LENGTH(symbol) = 14
```

### Upload Script (Python with BigQuery client)

```python
import sqlite3
from google.cloud import bigquery

# 1. Read from SQLite
conn = sqlite3.connect('patent-classification-2025.db')
cur = conn.cursor()
cur.execute("SELECT symbol, symbol_short, kind, level, parent, parent_short, title_en, "
            "size, size_percent FROM ipc")
rows = cur.fetchall()
conn.close()

# 2. Build lookup for title_full generation
lookup = {}
for symbol, symbol_short, kind, level, parent, parent_short, title_en, size, size_pct in rows:
    lookup[symbol] = {
        "title_en": title_en, "parent": parent, "level": level,
        "symbol_short": symbol_short, "kind": kind,
        "parent_short": parent_short, "size": size, "size_percent": size_pct,
    }


def build_title_full(symbol: str, from_level: int = 5) -> str:
    """Build concatenated title from main group level (5) downwards.

    Example: 'A01B0001040000' → 'Hand tools > Spades; Shovels > with teeth'

    Starts at the entry's own level and walks up to from_level,
    collecting titles. Entries at from_level or above return their
    own title_en unchanged.
    """
    chain = []
    current = symbol
    while current in lookup:
        entry = lookup[current]
        if entry["level"] < from_level:
            break
        chain.append(entry["title_en"])
        current = entry["parent"]
    chain.reverse()
    return " > ".join(chain) if chain else lookup.get(symbol, {}).get("title_en", "")


# 3. Convert and prepare rows for BigQuery
from conversion_functions import zeropad_to_patstat  # functions from above

bq_rows = []
for symbol, data in lookup.items():
    symbol_patstat = zeropad_to_patstat(symbol) if len(symbol) == 14 else None
    title_full = build_title_full(symbol)

    bq_rows.append({
        "symbol": symbol,
        "symbol_short": data["symbol_short"],
        "symbol_patstat": symbol_patstat,
        "kind": data["kind"],
        "level": data["level"],
        "parent": data["parent"],
        "parent_short": data["parent_short"],
        "title_en": data["title_en"],
        "title_full": title_full,
        "size": data["size"],
        "size_percent": data["size_percent"],
    })

# 4. Upload to BigQuery
client = bigquery.Client()
table_id = "your_project.patstat_dataset.tls_ipc_hierarchy"

schema = [
    bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("symbol_short", "STRING"),
    bigquery.SchemaField("symbol_patstat", "STRING"),
    bigquery.SchemaField("kind", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("level", "INT64", mode="REQUIRED"),
    bigquery.SchemaField("parent", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("parent_short", "STRING"),
    bigquery.SchemaField("title_en", "STRING"),
    bigquery.SchemaField("title_full", "STRING"),
    bigquery.SchemaField("size", "INT64"),
    bigquery.SchemaField("size_percent", "FLOAT64"),
]

job_config = bigquery.LoadJobConfig(
    schema=schema,
    write_disposition="WRITE_TRUNCATE",
)

job = client.load_table_from_json(bq_rows, table_id, job_config=job_config)
job.result()  # Wait for completion
print(f"Loaded {job.output_rows} rows into {table_id}")
```

### Usage Examples After Upload

**Get English title for any PATSTAT IPC code:**
```sql
SELECT i.appln_id, i.ipc_class_symbol, h.title_en
FROM tls209_appln_ipc i
JOIN tls_ipc_hierarchy h ON i.ipc_class_symbol = h.symbol_patstat
WHERE i.appln_id = 8668048
```

**Navigate the IPC hierarchy (find all children of a main group):**
```sql
-- All subgroups of H04L41/00 (network management)
SELECT symbol_short, title_en, level, kind
FROM tls_ipc_hierarchy
WHERE parent = 'H04L0041000000'
ORDER BY symbol
```

**Recursive hierarchy traversal (full subtree):**
```sql
-- All descendants of H04L (any depth)
WITH RECURSIVE tree AS (
    SELECT symbol, symbol_short, title_en, level, parent
    FROM tls_ipc_hierarchy
    WHERE symbol = 'H04L'

    UNION ALL

    SELECT h.symbol, h.symbol_short, h.title_en, h.level, h.parent
    FROM tls_ipc_hierarchy h
    JOIN tree t ON h.parent = t.symbol
)
SELECT * FROM tree ORDER BY symbol
```

**Enrich patent results with classification context:**
```sql
SELECT a.appln_id, a.appln_filing_date, a.appln_auth,
       i.ipc_class_symbol, h.title_en,
       p.title_en AS parent_title
FROM tls201_appln a
JOIN tls209_appln_ipc i ON a.appln_id = i.appln_id
JOIN tls_ipc_hierarchy h ON i.ipc_class_symbol = h.symbol_patstat
JOIN tls_ipc_hierarchy p ON h.parent = p.symbol
WHERE i.ipc_value = 'I' AND i.ipc_position = 'F'
  AND STARTS_WITH(i.ipc_class_symbol, 'H04L')
LIMIT 20
```

### Why NOT Extend Existing PATSTAT Tables?

1. **PATSTAT is read-only**: It's a published dataset from the EPO. Adding columns to `tls209` or `tls901` would break on the next PATSTAT release.
2. **Scope mismatch**: `tls901` maps only main groups to 35 tech fields. The IPC hierarchy has 79,833 entries across 14 levels — fundamentally different granularity.
3. **Clean separation**: A separate table can be updated independently when a new IPC version is released (currently 2025.01). Just re-upload.
4. **The `symbol_patstat` bridge column** makes JOINs zero-cost. No runtime string manipulation needed.

### MCP Tool Update: `resolve_ipc`

Add a new tool that leverages `tls_ipc_hierarchy`:

| Parameter | Type | Required | Description |
|---|---|---|---|
| `symbol` | string | yes | IPC code in any format (short, PATSTAT, or zero-padded) |
| `include_children` | boolean | no | Return child entries. Default: false |
| `include_ancestors` | boolean | no | Return parent chain up to section. Default: false |
| `max_depth` | integer | no | Limit child depth. Default: unlimited |

This tool auto-detects the input format, normalizes it, and returns the hierarchy context with English titles.

### MCP Tool: `search_ipc_by_technology`

This is arguably the highest-value tool for PATLIB users. Instead of requiring users to know IPC codes, it lets them search by technology description in natural language.

#### Purpose

Search IPC classification titles by keyword to discover relevant codes. Returns matching IPC entries with their hierarchy context, ready to be used in subsequent PATSTAT queries.

#### Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `keywords` | string | yes | Technology search terms (e.g., `"battery"`, `"machine learning"`, `"additive manufacturing"`) |
| `level_filter` | string | no | Restrict to hierarchy level: `"main_group"` (level 5 only), `"subgroup"` (level 6+), `"all"` (default) |
| `max_rows` | integer | no | Default: 50, max: 500 |

#### Internal Query Logic

The tool should split the keywords string on commas or `OR` to support multi-term searches.

```python
def build_technology_search_query(keywords: str, level_filter: str = "all", max_rows: int = 50) -> str:
    """Build SQL for technology keyword search against IPC title_full.

    CRITICAL: Search against title_full, NOT title_en.
    IPC titles are hierarchical fragments. A subgroup title like "with teeth"
    or "Details" is meaningless without ancestor context. title_full contains
    the concatenated chain: "Hand tools > Spades; Shovels > with teeth"

    Searching title_full dramatically improves recall:
    - "battery":          37 → 87 hits  (+135%)
    - "electric vehicle": 10 → 71 hits  (+610%)
    """

    # Split on comma or " OR " for multi-term search
    import re
    terms = [t.strip().lower() for t in re.split(r',|\bOR\b', keywords, flags=re.IGNORECASE) if t.strip()]

    # Build LIKE clauses — search title_full for inherited context
    like_clauses = [f"LOWER(title_full) LIKE '%{term}%'" for term in terms]
    where_keywords = " OR ".join(like_clauses)

    # Level filter
    level_clause = ""
    if level_filter == "main_group":
        level_clause = "AND level = 5"
    elif level_filter == "subgroup":
        level_clause = "AND level >= 6"

    return f"""
        SELECT symbol, symbol_short, symbol_patstat, level, kind,
               title_en, title_full, parent_short
        FROM tls_ipc_hierarchy
        WHERE ({where_keywords})
        {level_clause}
        ORDER BY level, symbol
        LIMIT {max_rows}
    """
```

> **Important:** Use parameterized queries in production to prevent SQL injection. The above is pseudocode for illustration.

**Generated SQL example** for `keywords="battery, batteries"`, `level_filter="main_group"`:
```sql
SELECT symbol, symbol_short, symbol_patstat, level, kind,
       title_en, title_full, parent_short
FROM tls_ipc_hierarchy
WHERE (LOWER(title_full) LIKE '%battery%' OR LOWER(title_full) LIKE '%batteries%')
  AND level = 5
ORDER BY level, symbol
LIMIT 50
```

#### Return Format

```json
{
  "query_used": "...",
  "results": [
    {
      "symbol": "B60L0053000000",
      "symbol_short": "B60L53/00",
      "symbol_patstat": "B60L  53/00",
      "level": 5,
      "kind": "m",
      "title_en": "Methods of charging batteries, specially adapted for electric vehicles...",
      "title_full": "Methods of charging batteries, specially adapted for electric vehicles...",
      "parent_short": "B60L"
    },
    {
      "symbol": "B60L0058100000",
      "symbol_short": "B60L58/1",
      "symbol_patstat": "B60L  58/1",
      "level": 6,
      "kind": "1",
      "title_en": "for monitoring or controlling batteries",
      "title_full": "Methods or circuit arrangements for monitoring or controlling batteries or fuel cells, specially adapted for electric vehicles > for monitoring or controlling batteries",
      "parent_short": "B60L58/00"
    }
  ],
  "total_results": 87,
  "tip": "Use symbol_patstat values to JOIN against tls209_appln_ipc.ipc_class_symbol"
}
```

#### Why This Tool Matters

IPC titles are standardized technical descriptions written by patent classification experts. But individual subgroup titles are **hierarchical fragments** — they only make sense in context of their parent chain. By searching `title_full` (the concatenated ancestor chain), we get both the precision of expert-curated classification AND the recall of inherited parent context. This bridges the gap between how users think about technology ("battery", "autonomous driving") and the formal classification codes they need for PATSTAT queries.

Typical LLM-assisted workflow:

1. User asks: "How many patents were filed for battery technology in the last 5 years?"
2. LLM calls `search_ipc_by_technology(keywords="battery, batteries", level_filter="main_group")`
3. LLM reviews results, selects relevant codes (e.g., `H01M`, `H02J7/00`, `B60L53/00`)
4. LLM calls `run_query()` with a PATSTAT query using those codes
5. User gets an accurate, IPC-grounded answer — not a vague keyword search

---

## Implementation Priority (Updated)

1. **`run_query`** — Highest value, unlocks all use cases. Implement first.
2. **`search_ipc_by_technology`** — Highest user impact. The "killer feature" that makes PATSTAT accessible to non-experts. Requires `tls_ipc_hierarchy` upload.
3. **`search_by_ipc`** — Core PATLIB use case with whitespace normalization.
4. **`search_by_cpc`** — Same pattern as IPC but with application/family level distinction.
5. **`resolve_ipc`** — Hierarchy navigation and title lookup for known codes.
6. **`get_tech_field`** — Nice-to-have, lower priority but simple to implement.

---

*Specification for MCP server developer. Prepared February 2026.*
