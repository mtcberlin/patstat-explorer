# PATSTAT Explorer - Query Catalog

**Generated:** 2026-01-26 | **Total Queries:** 19 (18 static + 1 dynamic)

## Overview

PATSTAT Explorer provides predefined SQL queries for patent analysis, organized by stakeholder perspective:

| Stakeholder | Description | Query Count |
|-------------|-------------|-------------|
| **PATLIB** | Patent Information Centers & Libraries | 8 |
| **BUSINESS** | Companies & Industry | 11 |
| **UNIVERSITY** | Universities & Research | 6 |

## Query Index

| ID | Title | Tags | Est. Time |
|----|-------|------|-----------|
| [Q01](#q01-database-statistics) | Database Statistics | PATLIB | ~1s |
| [Q02](#q02-filing-authorities) | Filing Authorities | PATLIB | ~1s |
| [Q03](#q03-applications-by-year) | Applications by Year | PATLIB | ~1s |
| [Q04](#q04-top-ipc-classes) | Top IPC Classes | PATLIB | ~8s / ~1s |
| [Q05](#q05-sample-patents) | Sample Patents | PATLIB | ~1s |
| [Q06](#q06-country-patent-activity) | Country Patent Activity | PATLIB, BUSINESS | ~5s / ~1s |
| [Q07](#q07-green-technology-trends) | Green Technology Trends | BUSINESS, UNIVERSITY | ~5s / ~1s |
| [Q08](#q08-most-active-technology-fields) | Most Active Technology Fields | BUSINESS, UNIVERSITY | ~14s / ~1s |
| [Q09](#q09-ai-based-erp-patent-landscape) | AI-based ERP Patent Landscape | BUSINESS | ~4s / ~1s |
| [Q10](#q10-ai-assisted-diagnostics-companies) | AI-Assisted Diagnostics Companies | BUSINESS, UNIVERSITY | ~5s / ~1s |
| [Q11](#q11-top-patent-applicants) | Top Patent Applicants | BUSINESS | ~12s / ~1s |
| [Q12](#q12-competitor-filing-strategy-medtech) | Competitor Filing Strategy (MedTech) | BUSINESS | ~4s / ~1s |
| [Q13](#q13-most-cited-patents-2020) | Most Cited Patents (2020) | UNIVERSITY | ~10s / ~1s |
| [Q14](#q14-diagnostic-imaging-grant-rates) | Diagnostic Imaging Grant Rates | BUSINESS, UNIVERSITY | ~2s / ~1s |
| [Q15](#q15-german-states-medical-tech) | German States - Medical Tech | PATLIB | ~4s / ~1s |
| [Q16](#q16-german-states-per-capita-analysis) | German States - Per Capita Analysis | PATLIB | ~6s / ~1s |
| [Q17](#q17-regional-tech-sector-comparison) | Regional Tech Sector Comparison | PATLIB | ~3s / ~1s |
| [Q18](#q18-fastest-growing-g06q-subclasses) | Fastest-Growing G06Q Subclasses | BUSINESS, UNIVERSITY | ~5s / ~1s |
| [DQ01](#dq01-technology-trend-analysis) | Technology Trend Analysis (Dynamic) | ALL | ~8s / ~2s |

---

## Overview / Database Exploration (Q01-Q05)

### Q01: Database Statistics

**Tags:** `PATLIB`

High-level statistics about the PATSTAT database including total applications, date range, unique applicants/inventors count, and countries covered.

**Key Outputs:**
- Total patent applications
- Date range (earliest to latest filing year)
- Unique persons count
- Countries covered

**SQL:**
```sql
SELECT 'Total Applications' AS metric, CAST(COUNT(*) AS STRING) AS value FROM tls201_appln
UNION ALL
SELECT 'Earliest Filing Year', CAST(MIN(appln_filing_year) AS STRING) FROM tls201_appln WHERE appln_filing_year > 0
UNION ALL
SELECT 'Latest Filing Year', CAST(MAX(appln_filing_year) AS STRING) FROM tls201_appln
UNION ALL
SELECT 'Granted Patents', CAST(COUNT(*) AS STRING) FROM tls201_appln WHERE granted = 'Y'
UNION ALL
SELECT 'Unique Persons', CAST(COUNT(*) AS STRING) FROM tls206_person
UNION ALL
SELECT 'Countries with Applicants', CAST(COUNT(DISTINCT person_ctry_code) AS STRING) FROM tls206_person WHERE person_ctry_code IS NOT NULL
```

---

### Q02: Filing Authorities

**Tags:** `PATLIB`

Shows all patent offices/filing authorities in PATSTAT with application volumes. Helps understand which patent offices are represented and their relative importance.

**Key Outputs:**
- Filing authority codes (EP, US, CN, etc.)
- Application counts per office
- Percentage of total applications

**SQL:**
```sql
SELECT
    appln_auth AS filing_authority,
    COUNT(*) AS application_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM tls201_appln
WHERE appln_auth IS NOT NULL
GROUP BY appln_auth
ORDER BY application_count DESC
LIMIT 30
```

---

### Q03: Applications by Year

**Tags:** `PATLIB`

Distribution of patent applications across filing years. Useful for understanding data coverage and identifying trends. Note: Recent years may show lower counts due to 18-month publication delays.

**Key Outputs:**
- Applications per year
- Year-over-year changes
- Grant rates per year

**SQL:**
```sql
SELECT
    appln_filing_year,
    COUNT(*) AS applications,
    COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY appln_filing_year) AS yoy_change,
    COUNT(CASE WHEN granted = 'Y' THEN 1 END) AS granted,
    ROUND(COUNT(CASE WHEN granted = 'Y' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS grant_rate_pct
FROM tls201_appln
WHERE appln_filing_year BETWEEN 1980 AND 2024
GROUP BY appln_filing_year
ORDER BY appln_filing_year DESC
```

---

### Q04: Top IPC Classes

**Tags:** `PATLIB`

Most frequently assigned IPC (International Patent Classification) classes:
- **A:** Human Necessities (medical, agriculture)
- **B:** Operations/Transport (vehicles, printing)
- **C:** Chemistry/Metallurgy
- **D:** Textiles/Paper
- **E:** Fixed Constructions
- **F:** Mechanical Engineering
- **G:** Physics (computing, optics)
- **H:** Electricity (electronics, communication)

**Key Outputs:**
- Top IPC classes by frequency
- Application counts per class
- Technology distribution

---

### Q05: Sample Patents

**Tags:** `PATLIB`

Sample of 100 patent applications to understand data structure and available fields in `tls201_appln`.

**Key Outputs:**
- Application IDs and dates
- Filing authority codes
- Grant status
- Family information

---

## Strategic / Market Intelligence (Q06-Q07)

### Q06: Country Patent Activity

**Tags:** `PATLIB` `BUSINESS`

Analyzes patent filing activity by applicant country since 2015. Calculates total applications and grant rates to identify active countries and application quality.

**Key Outputs:**
- Country ranking by patent volume
- Grant rates by country (quality indicator)
- Total vs. granted patent counts

---

### Q07: Green Technology Trends

**Tags:** `BUSINESS` `UNIVERSITY`

Tracks patent activity in G7+China+Korea with focus on green/environmental technologies (CPC Y02 class). Y02 covers climate change mitigation technologies - useful for ESG reporting.

**Key Outputs:**
- Yearly patent trends by country
- Green technology patent counts (Y02 class)
- Green tech percentage (sustainability indicator)

---

## Technology Scouting (Q08-Q10)

### Q08: Most Active Technology Fields

**Tags:** `BUSINESS` `UNIVERSITY`

Uses WIPO technology field classifications to identify active sectors. Weight filter (>0.5) ensures only primary assignments are counted.

**Key Outputs:**
- Technology fields ranked by activity
- Average family size (geographic reach indicator)
- Average citations (impact/importance indicator)

---

### Q09: AI-based ERP Patent Landscape

**Tags:** `BUSINESS`

Patent landscape for AI-based ERP by identifying applications with both:
- **G06Q 10/**: ERP/administration/management
- **G06N**: AI/Machine Learning

**Key Outputs:**
- Top 10 applicants in AI+ERP space
- Patent counts per applicant
- Active years (innovation consistency)

---

### Q10: AI-Assisted Diagnostics Companies

**Tags:** `BUSINESS` `UNIVERSITY`

Companies active in AI-assisted diagnostics at the intersection of:
- **A61B**: Medical diagnosis
- **G06N**: Artificial intelligence

**Key Outputs:**
- Companies ranked by portfolio size
- Average time-to-grant (days and years)
- Focus on granted patents only

---

## Competitive Intelligence (Q11-Q12)

### Q11: Top Patent Applicants

**Tags:** `BUSINESS`

Most prolific patent applicants by standardized name (doc_std_name) since 2010.

**Key Outputs:**
- Top applicants ranked by volume
- Grant success rate per applicant
- Unique patent families (true innovation count)

---

### Q12: Competitor Filing Strategy (MedTech)

**Tags:** `BUSINESS`

Geographic filing patterns of major MedTech competitors using WIPO technology sector (Instruments). Competitors include: Medtronic, Johnson & Johnson, Abbott, Boston Scientific, Stryker, Zimmer, Smith & Nephew, Edwards, Baxter, Fresenius, B. Braun.

**Key Outputs:**
- Filing distribution by patent office (EP/US/CN)
- Percentage breakdown per competitor
- Patent counts per authority

---

## Citation & Prosecution (Q13-Q14)

### Q13: Most Cited Patents (2020)

**Tags:** `UNIVERSITY`

Citation network identifying most influential prior art patents. Shows which older patents remain technically relevant based on 2020 citations.

**Key Outputs:**
- Most cited patents (influence indicator)
- Citation lag in years (knowledge diffusion speed)
- Cited patent filing year

---

### Q14: Diagnostic Imaging Grant Rates

**Tags:** `BUSINESS` `UNIVERSITY`

Grant rates for diagnostic imaging patents (IPC A61B 6/) across EPO, USPTO, and CNIPA. Covers X-ray, ultrasound, MRI, and other imaging devices.

**Key Outputs:**
- Grant rates by patent office
- Total applications vs. granted patents
- Office comparison for filing strategy

---

## Regional Analysis - Germany (Q15-Q17)

### Q15: German States - Medical Tech

**Tags:** `PATLIB`

Medical technology patent activity across German federal states using NUTS codes in IPC A61B (Diagnosis/Surgery).

**Key Outputs:**
- Federal states ranked by patent activity
- Grant rates per region
- Unique applicants and patent families

---

### Q16: German States - Per Capita Analysis

**Tags:** `PATLIB`

A61B activity with per-capita comparison using population data from Statistisches Bundesamt (December 2023).

**Key Outputs:**
- German states ranked by patent count
- Patents per million inhabitants
- Rank by total vs. rank per capita

---

### Q17: Regional Tech Sector Comparison

**Tags:** `PATLIB`

Compares Sachsen, Bayern, Baden-Württemberg by WIPO technology sectors.

**Key Outputs:**
- Patent counts by region and sector
- Recent activity (2018+) highlighted
- Technology relevance weights

---

## Technology Transfer (Q18)

### Q18: Fastest-Growing G06Q Subclasses

**Tags:** `BUSINESS` `UNIVERSITY`

Fastest-growing subclasses within G06Q (IT methods for management) by comparing 2021 vs 2023 filing activity.

**Key Outputs:**
- Fastest-growing subclasses by growth rate
- Top 3 applicants driving growth
- Year-over-year comparison

---

## Dynamic Queries

### DQ01: Technology Trend Analysis

**Tags:** `PATLIB` `BUSINESS` `UNIVERSITY`

Interactive analysis with customizable parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `jurisdiction` | Select | EP | Filing jurisdiction (patent office) |
| `tech_field` | Select | 13 (Medical) | WIPO technology field (35 fields) |
| `year_range` | Slider | 2015-2023 | Filing year range |

**Key Outputs:**
- Yearly application counts
- Unique inventions (patent families) per year
- Trend visualization

**SQL Template:**
```sql
SELECT
    a.appln_filing_year AS year,
    COUNT(DISTINCT a.appln_id) AS application_count,
    COUNT(DISTINCT a.docdb_family_id) AS invention_count
FROM tls201_appln a
JOIN tls230_appln_techn_field tf ON a.appln_id = tf.appln_id
WHERE a.appln_auth = @jurisdiction
  AND tf.techn_field_nr = @tech_field
  AND a.appln_filing_year BETWEEN @year_start AND @year_end
  AND tf.weight > 0.5
GROUP BY a.appln_filing_year
ORDER BY a.appln_filing_year ASC
```

---

## Adding New Queries

1. Edit `queries_bq.py`
2. Add new entry with next ID (e.g., `Q19`)
3. Include required metadata:
   - `title`: Short query name
   - `tags`: List of stakeholder tags
   - `description`: One-line description
   - `explanation`: Detailed explanation
   - `key_outputs`: List of key metrics
   - `estimated_seconds_first_run`: Expected uncached time
   - `estimated_seconds_cached`: Expected cached time
   - `sql`: BigQuery SQL statement
4. Test in BigQuery Console first
5. Run `python test_queries.py` to validate

## BigQuery SQL Tips

```sql
-- Table names without prefix (default dataset is set automatically)
SELECT * FROM tls201_appln

-- Type casting
CAST(field AS STRING)

-- Date arithmetic
DATE_DIFF(date1, date2, DAY)

-- IPC/CPC pattern matching
WHERE ipc_class_symbol LIKE 'A61B%'

-- WIPO technology field join
JOIN tls230_appln_techn_field tf ON a.appln_id = tf.appln_id
JOIN tls901_techn_field_ipc tfi ON tf.techn_field_nr = tfi.techn_field_nr
WHERE tf.weight > 0.5  -- Primary technology assignment only
```
