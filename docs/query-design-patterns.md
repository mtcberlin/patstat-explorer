# Query Design Patterns

**Last Updated:** 2026-02-01

This document captures the query design patterns established in PATSTAT Explorer that can be reused for TIP Jupyter notebooks and future applications.

---

## Query Structure Pattern

Every query in `queries_bq.py` follows a consistent structure:

```python
"Q01": {
    # === METADATA (for UI display) ===
    "title": "What are the overall PATSTAT database statistics?",
    "tags": ["PATLIB"],
    "category": "Trends",
    "description": "Comprehensive PATSTAT database statistics...",

    # === EDUCATIONAL CONTENT ===
    "explanation": """Detailed explanation of what the query does,
    why it's useful, and how to interpret results...""",
    "key_outputs": [
        "Total patent applications",
        "Granted patents",
        "Patent families"
    ],
    "methodology": "Optional: Explain the analytical approach",

    # === PERFORMANCE HINTS ===
    "estimated_seconds_first_run": 15,
    "estimated_seconds_cached": 5,

    # === DISPLAY CONFIGURATION ===
    "display_mode": "default" | "metrics_grid" | "chart_and_table",
    "visualization": {
        "type": "bar" | "line" | "pie" | "stacked_bar",
        "x": "column_name",
        "y": "column_name",
        "color": "column_name",
        "stacked_columns": ["col1", "col2"]  # for stacked_bar
    },

    # === PARAMETERS (for dynamic queries) ===
    "parameters": {
        "year_range": {
            "type": "year_range",
            "label": "Filing Year Range",
            "default_start": 2014,
            "default_end": 2023
        }
    },

    # === SQL ===
    "sql": "SELECT ... (static SQL)",
    "sql_template": "SELECT ... WHERE year BETWEEN @year_start AND @year_end"
}
```

---

## Parameter System

### Available Parameter Types

| Type | UI Control | SQL Placeholder | Use Case |
|------|------------|-----------------|----------|
| `year_range` | Dual slider | `@year_start`, `@year_end` | Filing year range |
| `year_picker` | Two number inputs | `@year_start`, `@year_end` | Wide date ranges (1782-2024) |
| `multiselect` | Multiselect dropdown | `@jurisdictions` (ARRAY) | Multiple selections |
| `select` | Single dropdown | `@tech_sector` (STRING) | Single selection |
| `text` | Text input | `@applicant_name` (STRING) | Free text entry |

### Parameter Definition Examples

```python
# Year range with slider
"year_range": {
    "type": "year_range",
    "label": "Filing Year Range",
    "default_start": 2014,
    "default_end": 2023
}

# Multiselect with predefined options
"jurisdictions": {
    "type": "multiselect",
    "label": "Patent Offices",
    "options": "jurisdictions",  # References config.JURISDICTIONS
    "defaults": ["EP", "US", "DE"]
}

# Select with dynamic options
"tech_sector": {
    "type": "select",
    "label": "Technology Sector",
    "options": "tech_sectors",  # References unique sectors from TECH_FIELDS
    "defaults": "Electrical engineering"
}

# Text input
"applicant_name": {
    "type": "text",
    "label": "Applicant Name",
    "placeholder": "e.g., Siemens, BASF"
}
```

### SQL Template Patterns

```sql
-- Year range filter
WHERE a.appln_filing_year BETWEEN @year_start AND @year_end

-- Jurisdiction filter (ARRAY parameter)
WHERE a.appln_auth IN UNNEST(@jurisdictions)

-- Technology field filter (INT parameter)
WHERE t.techn_field_nr = @tech_field

-- Text search with LIKE
WHERE UPPER(p.person_name) LIKE CONCAT('%', UPPER(@applicant_name), '%')

-- Combined filters
WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
  AND a.appln_auth IN UNNEST(@jurisdictions)
  AND (@tech_field IS NULL OR t.techn_field_nr = @tech_field)
```

---

## Common Query Patterns

### Pattern 1: Aggregation by Year and Category

**Use case:** Trend analysis over time with breakdown

```sql
SELECT
    a.appln_filing_year AS year,
    c.st3_name AS country,
    COUNT(*) AS application_count
FROM `tls201_appln` a
JOIN `tls801_country` c ON a.appln_auth = c.ctry_code
WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
  AND a.appln_auth IN UNNEST(@jurisdictions)
GROUP BY year, country
ORDER BY year, application_count DESC
```

**Visualization config:**
```python
"visualization": {
    "type": "line",
    "x": "year",
    "y": "application_count",
    "color": "country"
}
```

### Pattern 2: Top-N Ranking

**Use case:** Identify top applicants, countries, or technology fields

```sql
SELECT
    p.doc_std_name AS applicant,
    COUNT(DISTINCT a.docdb_family_id) AS family_count
FROM `tls201_appln` a
JOIN `tls207_pers_appln` pa ON a.appln_id = pa.appln_id AND pa.applt_seq_nr > 0
JOIN `tls206_person` p ON pa.person_id = p.person_id
WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
GROUP BY applicant
ORDER BY family_count DESC
LIMIT 20
```

**Visualization config:**
```python
"visualization": {
    "type": "bar",
    "x": "applicant",
    "y": "family_count"
}
```

### Pattern 3: Technology Field Analysis

**Use case:** Analyze patents by WIPO technology field

```sql
SELECT
    tf.techn_field AS technology_field,
    tf.techn_sector AS sector,
    COUNT(*) AS patent_count
FROM `tls201_appln` a
JOIN `tls230_appln_techn_field` atf ON a.appln_id = atf.appln_id
JOIN `tls901_techn_field_ipc` tf ON atf.techn_field_nr = tf.techn_field_nr
WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
GROUP BY technology_field, sector
ORDER BY patent_count DESC
```

### Pattern 4: Regional Analysis (NUTS)

**Use case:** Analyze by German federal states or EU regions

```sql
SELECT
    n.nuts_label AS region,
    COUNT(*) AS application_count
FROM `tls201_appln` a
JOIN `tls207_pers_appln` pa ON a.appln_id = pa.appln_id AND pa.applt_seq_nr > 0
JOIN `tls206_person` p ON pa.person_id = p.person_id
JOIN `tls904_nuts` n ON p.nuts = n.nuts
WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
  AND n.nuts_level = 1  -- State level
  AND n.ctry_code = 'DE'
GROUP BY region
ORDER BY application_count DESC
```

### Pattern 5: Green Technology (CPC Y02)

**Use case:** Climate change mitigation technology analysis

```sql
SELECT
    a.appln_filing_year AS year,
    COUNT(*) AS green_patents
FROM `tls201_appln` a
JOIN `tls224_appln_cpc` cpc ON a.appln_id = cpc.appln_id
WHERE cpc.cpc_class_symbol LIKE 'Y02%'
  AND a.appln_filing_year BETWEEN @year_start AND @year_end
GROUP BY year
ORDER BY year
```

### Pattern 6: Citation Analysis

**Use case:** Find highly cited patents or citation networks

```sql
SELECT
    pub.publn_auth,
    pub.publn_nr,
    COUNT(*) AS citation_count
FROM `tls211_pat_publn` pub
JOIN `tls212_citation` c ON pub.pat_publn_id = c.cited_pat_publn_id
GROUP BY pub.publn_auth, pub.publn_nr
ORDER BY citation_count DESC
LIMIT 50
```

### Pattern 7: Grant Rate Analysis

**Use case:** Compare grant rates across jurisdictions or years

```sql
SELECT
    a.appln_filing_year AS year,
    a.appln_auth AS office,
    COUNT(*) AS total_applications,
    COUNTIF(a.granted = 'Y') AS granted,
    COUNTIF(a.granted = 'N' OR a.granted IS NULL) AS not_granted,
    ROUND(COUNTIF(a.granted = 'Y') * 100.0 / COUNT(*), 1) AS grant_rate
FROM `tls201_appln` a
WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
  AND a.appln_auth IN UNNEST(@jurisdictions)
GROUP BY year, office
ORDER BY year, office
```

**Visualization config for stacked bar:**
```python
"visualization": {
    "type": "stacked_bar",
    "x": "year",
    "y": "count",
    "stacked_columns": ["granted", "not_granted"]
}
```

### Pattern 8: Database Statistics (Metrics Grid)

**Use case:** Dashboard-style overview with multiple metrics

```sql
SELECT 'Total Applications' AS metric, CAST(COUNT(*) AS STRING) AS value
FROM `tls201_appln`
UNION ALL
SELECT 'Granted Patents', CAST(COUNT(*) AS STRING)
FROM `tls201_appln` WHERE granted = 'Y'
UNION ALL
SELECT 'Patent Families', CAST(COUNT(DISTINCT docdb_family_id) AS STRING)
FROM `tls201_appln` WHERE docdb_family_id > 0
```

**Display config:**
```python
"display_mode": "metrics_grid"
```

---

## Query Categories

| Category | Description | Example Queries |
|----------|-------------|-----------------|
| **Trends** | Time-series analysis, growth patterns | Filing trends, grant rate over time |
| **Competitors** | Applicant rankings, market share | Top filers, competitive landscape |
| **Regional** | Geographic analysis, NUTS regions | State-level analysis, country comparison |
| **Technology** | IPC/CPC/WIPO field analysis | Tech field breakdown, green tech |

---

## Stakeholder Tags

| Tag | Audience | Focus |
|-----|----------|-------|
| **PATLIB** | Patent libraries, information centers | Database overview, training queries |
| **BUSINESS** | Companies, industry | Competitor analysis, market intelligence |
| **UNIVERSITY** | Researchers, academia | Citation analysis, technology transfer |

---

## Performance Optimization Tips

1. **Use `docdb_family_id`** for unique invention counts (not `appln_id`)
2. **Filter early** with `WHERE` before `JOIN` when possible
3. **Limit results** with `LIMIT` for large datasets
4. **Use `COUNTIF`** instead of `SUM(CASE WHEN...)`
5. **Cache awareness:** First run 2-15s, cached 0.3-2s
6. **Avoid `SELECT *`** - specify only needed columns

---

## TIP Compatibility

When exporting to TIP, the `format_sql_for_tip()` function:

1. **Removes backticks** from table names (TIP doesn't need them)
2. **Substitutes parameters** with actual values
3. **Converts UNNEST(@array)** to `IN ('val1', 'val2', ...)`

Example transformation:
```sql
-- BigQuery with parameters
WHERE a.appln_auth IN UNNEST(@jurisdictions)
  AND a.appln_filing_year BETWEEN @year_start AND @year_end

-- TIP-ready SQL
WHERE a.appln_auth IN ('EP', 'US', 'DE')
  AND a.appln_filing_year BETWEEN 2014 AND 2023
```

---

## Adding a New Query

1. Add entry to `queries_bq.py` with unique ID (e.g., `Q43`)
2. Include all required metadata fields
3. Define parameters if query should be dynamic
4. Set appropriate `display_mode` and `visualization`
5. Test query in BigQuery Console
6. Run `pytest tests/test_query_metadata.py` to validate structure
