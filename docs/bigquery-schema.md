# PATSTAT BigQuery Schema Reference

**Generated:** 2026-01-26 | **PATSTAT Version:** 2025 Autumn Edition | **Total Tables:** 27

## Overview

The PATSTAT database on BigQuery contains 27 tables with ~450 GB of patent data. This document provides schema definitions for each table, optimized for BigQuery with appropriate partitioning and clustering.

## Table Summary

| Table | Rows | Description |
|-------|------|-------------|
| [tls201_appln](#tls201_appln) | 140,525,582 | Patent applications (central table) |
| [tls202_appln_title](#tls202_appln_title) | 119,259,497 | Application titles |
| [tls203_appln_abstr](#tls203_appln_abstr) | 96,536,721 | Application abstracts |
| [tls204_appln_prior](#tls204_appln_prior) | 53,194,773 | Priority claims |
| [tls205_tech_rel](#tls205_tech_rel) | 4,160,592 | Technical relations |
| [tls206_person](#tls206_person) | 97,853,865 | Persons (applicants/inventors) |
| [tls207_pers_appln](#tls207_pers_appln) | 408,478,469 | Person-application links |
| [tls209_appln_ipc](#tls209_appln_ipc) | 374,559,946 | IPC classifications |
| [tls210_appln_n_cls](#tls210_appln_n_cls) | 26,217,769 | National classifications |
| [tls211_pat_publn](#tls211_pat_publn) | 167,837,244 | Patent publications |
| [tls212_citation](#tls212_citation) | 596,775,557 | Citation data |
| [tls214_npl_publn](#tls214_npl_publn) | 43,569,746 | Non-patent literature |
| [tls215_citn_categ](#tls215_citn_categ) | 1,346,861,951 | Citation categories |
| [tls216_appln_contn](#tls216_appln_contn) | 5,819,586 | Continuation applications |
| [tls222_appln_jp_class](#tls222_appln_jp_class) | 428,299,335 | Japanese classifications |
| [tls224_appln_cpc](#tls224_appln_cpc) | 436,450,350 | CPC classifications |
| [tls225_docdb_fam_cpc](#tls225_docdb_fam_cpc) | 224,464,483 | Family-level CPC |
| [tls226_person_orig](#tls226_person_orig) | 120,640,365 | Original person data |
| [tls227_pers_publn](#tls227_pers_publn) | 533,935,876 | Person-publication links |
| [tls228_docdb_fam_citn](#tls228_docdb_fam_citn) | 307,465,107 | Family-level citations |
| [tls229_appln_nace2](#tls229_appln_nace2) | 166,322,438 | NACE2 industry codes |
| [tls230_appln_techn_field](#tls230_appln_techn_field) | 166,549,096 | WIPO technology fields |
| [tls231_inpadoc_legal_event](#tls231_inpadoc_legal_event) | 498,252,938 | Legal status events |
| [tls801_country](#tls801_country) | 242 | Country reference |
| [tls803_legal_event_code](#tls803_legal_event_code) | 4,185 | Legal event codes |
| [tls901_techn_field_ipc](#tls901_techn_field_ipc) | 771 | Technology field mapping |
| [tls902_ipc_nace2](#tls902_ipc_nace2) | 863 | IPC to NACE2 mapping |
| [tls904_nuts](#tls904_nuts) | 2,056 | NUTS regional codes |

---

## Core Tables

### tls201_appln

**Central application table** - Most queries start here.

| Column | Type | Description |
|--------|------|-------------|
| `appln_id` | INTEGER | Primary key - unique application identifier |
| `appln_auth` | STRING | Filing authority (EP, US, CN, etc.) |
| `appln_nr` | STRING | Application number |
| `appln_kind` | STRING | Application kind code |
| `appln_filing_date` | DATE | Filing date |
| `appln_filing_year` | INTEGER | Filing year (partition key) |
| `appln_nr_epodoc` | STRING | EPODOC format number |
| `appln_nr_original` | STRING | Original application number |
| `ipr_type` | STRING | IPR type (PI, UM, etc.) |
| `receiving_office` | STRING | PCT receiving office |
| `internat_appln_id` | INTEGER | International application ID |
| `int_phase` | STRING | International phase flag |
| `reg_phase` | STRING | Regional phase flag |
| `nat_phase` | STRING | National phase flag |
| `earliest_filing_date` | DATE | Earliest priority date |
| `earliest_filing_year` | INTEGER | Earliest priority year |
| `earliest_filing_id` | INTEGER | Earliest priority application |
| `earliest_publn_date` | DATE | Earliest publication date |
| `earliest_publn_year` | INTEGER | Earliest publication year |
| `earliest_pat_publn_id` | INTEGER | Earliest publication ID |
| `granted` | STRING | Grant status (Y/N) |
| `docdb_family_id` | INTEGER | DOCDB family ID |
| `inpadoc_family_id` | INTEGER | INPADOC family ID |
| `docdb_family_size` | INTEGER | Family size count |
| `nb_citing_docdb_fam` | INTEGER | Number of citing families |
| `nb_applicants` | INTEGER | Number of applicants |
| `nb_inventors` | INTEGER | Number of inventors |

**BigQuery Optimization:**
- Partitioned by: `appln_filing_year` (range: 1900-2030)
- Clustered by: `appln_auth`, `docdb_family_id`, `granted`

**Common Query Patterns:**
```sql
-- Filter by authority and year range
WHERE appln_auth = 'EP' AND appln_filing_year BETWEEN 2015 AND 2023

-- Join with persons
JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
WHERE pa.applt_seq_nr > 0  -- Applicants only
```

---

### tls206_person

**Persons table** - Applicants and inventors with standardized names.

| Column | Type | Description |
|--------|------|-------------|
| `person_id` | INTEGER | Primary key |
| `person_name` | STRING | Person/company name |
| `person_name_orig_lg` | STRING | Name in original language |
| `person_address` | STRING | Address |
| `person_ctry_code` | STRING | Country code |
| `nuts` | STRING | NUTS regional code |
| `nuts_level` | INTEGER | NUTS level (0-3) |
| `doc_std_name_id` | INTEGER | Standardized name ID |
| `doc_std_name` | STRING | Standardized name |
| `psn_id` | INTEGER | PSN harmonized ID |
| `psn_name` | STRING | PSN harmonized name |
| `psn_level` | INTEGER | PSN harmonization level |
| `psn_sector` | STRING | Sector (COMPANY, INDIVIDUAL, etc.) |
| `han_id` | INTEGER | HAN harmonized ID |
| `han_name` | STRING | HAN harmonized name |
| `han_harmonized` | INTEGER | HAN harmonization flag |

**Name Harmonization Levels:**
- `doc_std_name`: Basic standardization
- `psn_name`: EPO harmonization (Level 1)
- `han_name`: Advanced harmonization (Level 2)

---

### tls207_pers_appln

**Person-Application link table** - Connects persons to applications.

| Column | Type | Description |
|--------|------|-------------|
| `person_id` | INTEGER | Foreign key to tls206_person |
| `appln_id` | INTEGER | Foreign key to tls201_appln |
| `applt_seq_nr` | INTEGER | Applicant sequence (>0 = applicant) |
| `invt_seq_nr` | INTEGER | Inventor sequence (>0 = inventor) |

**Usage:**
```sql
-- Get applicants only
WHERE applt_seq_nr > 0

-- Get inventors only
WHERE invt_seq_nr > 0

-- Get all persons (applicants and inventors)
WHERE applt_seq_nr > 0 OR invt_seq_nr > 0
```

---

## Classification Tables

### tls209_appln_ipc

**IPC (International Patent Classification)** - Technology classification.

| Column | Type | Description |
|--------|------|-------------|
| `appln_id` | INTEGER | Application ID |
| `ipc_class_symbol` | STRING | IPC symbol (e.g., "A61B 5/00") |
| `ipc_class_level` | STRING | Classification level |
| `ipc_version` | DATE | IPC version date |
| `ipc_value` | STRING | Value indicator |
| `ipc_position` | STRING | Position (F=first, L=later) |
| `ipc_gener_auth` | STRING | Generating authority |

**IPC Structure:**
```
A61B 5/00
│ │  │ └── Group/Subgroup
│ │  └──── Subclass
│ └─────── Class
└───────── Section (A-H)
```

**Pattern Matching:**
```sql
-- Medical diagnosis/surgery
WHERE ipc_class_symbol LIKE 'A61B%'

-- Specific subclass (6/ = diagnostic imaging)
WHERE ipc_class_symbol LIKE 'A61B%6/%'
```

---

### tls224_appln_cpc

**CPC (Cooperative Patent Classification)** - More granular than IPC.

| Column | Type | Description |
|--------|------|-------------|
| `appln_id` | INTEGER | Application ID |
| `cpc_class_symbol` | STRING | CPC symbol |

**Green Technology:**
```sql
-- Y02 = Climate change mitigation
WHERE cpc_class_symbol LIKE 'Y02%'

-- AI/Machine Learning
WHERE cpc_class_symbol LIKE 'G06N%'

-- Business methods
WHERE cpc_class_symbol LIKE 'G06Q%'
```

---

### tls230_appln_techn_field

**WIPO Technology Fields** - 35 standardized technology areas.

| Column | Type | Description |
|--------|------|-------------|
| `appln_id` | INTEGER | Application ID |
| `techn_field_nr` | INTEGER | Technology field number (1-35) |
| `weight` | FLOAT | Assignment weight (0-1) |

**Best Practice:**
```sql
-- Use weight > 0.5 for primary technology
WHERE tf.weight > 0.5
```

---

### tls901_techn_field_ipc

**Technology Field Definitions** - Maps IPC to WIPO technology fields.

| Column | Type | Description |
|--------|------|-------------|
| `ipc_maingroup_symbol` | STRING | IPC main group |
| `techn_field_nr` | INTEGER | Technology field number |
| `techn_sector` | STRING | Sector name |
| `techn_field` | STRING | Field name |

**Technology Sectors:**
1. Electrical engineering
2. Instruments
3. Chemistry
4. Mechanical engineering
5. Other fields

---

## Citation Tables

### tls212_citation

**Patent Citations** - Prior art references.

| Column | Type | Description |
|--------|------|-------------|
| `pat_publn_id` | INTEGER | Citing publication ID |
| `citn_replenished` | INTEGER | Replenishment flag |
| `citn_id` | INTEGER | Citation sequence |
| `citn_origin` | STRING | Citation origin |
| `cited_pat_publn_id` | INTEGER | Cited publication ID |
| `cited_appln_id` | INTEGER | Cited application ID |
| `pat_citn_seq_nr` | INTEGER | Patent citation sequence |
| `cited_npl_publn_id` | STRING | NPL publication ID |
| `npl_citn_seq_nr` | INTEGER | NPL citation sequence |
| `citn_gener_auth` | STRING | Generating authority |

---

### tls228_docdb_fam_citn

**Family-Level Citations** - Simplified citation data at family level.

| Column | Type | Description |
|--------|------|-------------|
| `docdb_family_id` | INTEGER | Citing family ID |
| `cited_docdb_family_id` | INTEGER | Cited family ID |

**Performance Tip:** Use family-level citations for faster aggregations.

---

## Publication Tables

### tls211_pat_publn

**Patent Publications** - Published documents.

| Column | Type | Description |
|--------|------|-------------|
| `pat_publn_id` | INTEGER | Primary key |
| `publn_auth` | STRING | Publication authority |
| `publn_nr` | STRING | Publication number |
| `publn_nr_original` | STRING | Original publication number |
| `publn_kind` | STRING | Kind code (A1, B1, etc.) |
| `appln_id` | INTEGER | Application ID |
| `publn_date` | DATE | Publication date |
| `publn_lg` | STRING | Publication language |
| `publn_first_grant` | STRING | First grant flag (Y/N) |
| `publn_claims` | INTEGER | Number of claims |

**Grant Date Query:**
```sql
-- Get grant date
WHERE publn_first_grant = 'Y'
```

---

## Reference Tables

### tls801_country

**Country Reference** - Country codes and metadata.

| Column | Type | Description |
|--------|------|-------------|
| `ctry_code` | STRING | 2-letter country code |
| `iso_alpha3` | STRING | 3-letter ISO code |
| `st3_name` | STRING | Country name |
| `organisation_flag` | STRING | Organization flag |
| `continent` | STRING | Continent |
| `eu_member` | STRING | EU membership |
| `epo_member` | STRING | EPO membership |
| `oecd_member` | STRING | OECD membership |
| `discontinued` | STRING | Discontinued flag |

---

### tls904_nuts

**NUTS Regional Codes** - European regional classification.

| Column | Type | Description |
|--------|------|-------------|
| `nuts` | STRING | NUTS code |
| `nuts_level` | INTEGER | Level (0-3) |
| `nuts_label` | STRING | Region name |

**German States (Level 1):**
```sql
WHERE nuts LIKE 'DE%' AND nuts_level = 1
```

---

## Legal Status Tables

### tls231_inpadoc_legal_event

**INPADOC Legal Events** - Patent lifecycle events.

| Column | Type | Description |
|--------|------|-------------|
| `event_id` | INTEGER | Primary key |
| `appln_id` | INTEGER | Application ID |
| `event_seq_nr` | INTEGER | Event sequence |
| `event_type` | STRING | Event type code |
| `event_auth` | STRING | Event authority |
| `event_code` | STRING | Event code |
| `event_filing_date` | DATE | Filing date |
| `event_publn_date` | DATE | Publication date |
| `event_effective_date` | DATE | Effective date |
| `event_text` | STRING | Event description |
| ... | ... | (Many additional columns) |

---

### tls803_legal_event_code

**Legal Event Code Reference** - Decodes event codes.

| Column | Type | Description |
|--------|------|-------------|
| `event_auth` | STRING | Authority |
| `event_code` | STRING | Event code |
| `event_descr` | STRING | Description (English) |
| `event_descr_orig` | STRING | Description (original) |
| `event_category_code` | STRING | Category code |
| `event_category_title` | STRING | Category title |

---

## Industry Mapping Tables

### tls229_appln_nace2

**NACE2 Industry Classification** - European industry codes.

| Column | Type | Description |
|--------|------|-------------|
| `appln_id` | INTEGER | Application ID |
| `nace2_code` | STRING | NACE2 code |
| `weight` | FLOAT | Assignment weight |

### tls902_ipc_nace2

**IPC to NACE2 Mapping** - Converts technology to industry.

| Column | Type | Description |
|--------|------|-------------|
| `ipc` | STRING | IPC code |
| `not_with_ipc` | STRING | Exclusion IPC |
| `unless_with_ipc` | STRING | Conditional IPC |
| `nace2_code` | STRING | NACE2 code |
| `nace2_weight` | INTEGER | Weight |
| `nace2_descr` | STRING | Industry description |

---

## Data Loading

### BigQuery Loading Script

Use `context/load_patstat_local.py` to load PATSTAT CSV files:

```bash
# Load all tables
python context/load_patstat_local.py /path/to/csv PROJECT_ID DATASET

# Dry run
python context/load_patstat_local.py /path/to/csv PROJECT_ID DATASET --dry-run

# Resume interrupted load
python context/load_patstat_local.py /path/to/csv PROJECT_ID DATASET --resume

# Verify row counts
python context/load_patstat_local.py /path/to/csv PROJECT_ID DATASET --verify
```

### PostgreSQL Reference

See `context/create_patstat_tables.sql` for PostgreSQL schema (useful for local development).

---

## External Documentation

- **EPO Data Catalog:** `context/Documentation_Scripts/DataCatalog_Global_v5.26.pdf`
- **OECD Patent Manual:** `context/Useful manuals and other docs/OECD patent statistics manual.pdf`
- **IPC-NACE Concordance:** `context/Useful manuals and other docs/IPC_NACE/`
- **NUTS Regionalisation:** `context/Useful manuals and other docs/NUTS_regionalisation/`
