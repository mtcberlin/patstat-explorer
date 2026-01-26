# PATSTAT Explorer Documentation Index

**Generated:** 2026-01-26 | **Scan Level:** Deep | **Project Type:** Data Analytics

## Project Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Monolith - Data Analytics Application |
| **Primary Language** | Python |
| **UI Framework** | Streamlit |
| **Database** | Google BigQuery (~450 GB) |
| **Data Source** | EPO PATSTAT 2025 Autumn Edition |

### Quick Reference

| Item | Value |
|------|-------|
| **Entry Point** | `app.py` |
| **Queries** | `queries_bq.py` (19 queries) |
| **Tests** | `test_queries.py` |
| **Config** | `.env` / Streamlit Secrets |
| **Live Demo** | [patstat.streamlit.app](https://patstat.streamlit.app/) |

## Generated Documentation

### Core Documentation

- [Project Overview](./project-overview.md) - Architecture, technology stack, development guide
- [Query Catalog](./query-catalog.md) - Complete reference for all 19 queries with SQL
- [BigQuery Schema](./bigquery-schema.md) - PATSTAT table definitions (27 tables)
- [Data Loading Guide](./data-loading.md) - Loading PATSTAT data to BigQuery

### Architecture

```
┌─────────────────────────────────────────┐
│           Streamlit Cloud               │
│  ┌───────────────────────────────────┐  │
│  │            app.py                 │  │
│  │  ┌─────────┐ ┌─────────┐        │  │
│  │  │Interactive│ │Query   │        │  │
│  │  │  Panel   │ │Panel   │        │  │
│  │  └────┬─────┘ └────┬────┘        │  │
│  │       └─────┬──────┘             │  │
│  │             ▼                    │  │
│  │     queries_bq.py                │  │
│  │     (19 SQL queries)             │  │
│  └─────────────┬─────────────────────┘  │
│                │                        │
│                ▼                        │
│       BigQuery Client                   │
└────────────────┬────────────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │  Google BigQuery │
        │  patstat-mtc     │
        │  ~450 GB         │
        │  27 tables       │
        └─────────────────┘
```

## Source Files

| File | Lines | Description |
|------|-------|-------------|
| `app.py` | 454 | Streamlit web application |
| `queries_bq.py` | 1031 | 19 BigQuery queries with metadata |
| `test_queries.py` | 158 | Query validation and timing tests |
| `requirements.txt` | 5 | Python dependencies |

## Query Summary

**Total:** 19 queries (18 static + 1 dynamic)

| Category | Queries | IDs |
|----------|---------|-----|
| Database Overview | 5 | Q01-Q05 |
| Strategic Intelligence | 2 | Q06-Q07 |
| Technology Scouting | 3 | Q08-Q10 |
| Competitive Intelligence | 2 | Q11-Q12 |
| Citation & Prosecution | 2 | Q13-Q14 |
| Regional Analysis (DE) | 3 | Q15-Q17 |
| Technology Transfer | 1 | Q18 |
| Dynamic/Interactive | 1 | DQ01 |

### By Stakeholder

| Tag | Count | Queries |
|-----|-------|---------|
| PATLIB | 8 | Q01-Q06, Q15-Q17 |
| BUSINESS | 11 | Q06-Q12, Q14, Q18, DQ01 |
| UNIVERSITY | 6 | Q07-Q08, Q10, Q13-Q14, Q18 |

## Database Schema

**27 Tables** organized as:

| Category | Tables | Description |
|----------|--------|-------------|
| Core | tls201, tls202, tls203 | Applications, titles, abstracts |
| Persons | tls206, tls207, tls226, tls227 | Applicants, inventors, links |
| Classifications | tls209, tls210, tls222, tls224, tls225 | IPC, CPC, JP classifications |
| Citations | tls212, tls214, tls215, tls228 | Patent and NPL citations |
| Publications | tls211 | Published documents |
| Legal Status | tls231, tls803 | INPADOC events |
| Reference | tls801, tls901, tls902, tls904 | Countries, tech fields, NUTS |
| Industry | tls229, tls230 | NACE2, WIPO tech fields |

## Development Guide

### Local Setup

```bash
# Clone and setup
git clone https://github.com/herrkrueger/patstat.git
cd patstat
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure (copy .env.example to .env, add credentials)
cp .env.example .env

# Run locally
streamlit run app.py
```

### Adding a New Query

1. Edit `queries_bq.py`
2. Add entry with ID `Q19` (or next available)
3. Include: `title`, `tags`, `description`, `explanation`, `key_outputs`, timing estimates, `sql`
4. Test in BigQuery Console
5. Run `python test_queries.py` to validate

### Testing

```bash
# Run all query tests
python test_queries.py

# Output: timing report and JSON results file
```

## Reference Materials

### EPO Documentation

| Document | Location |
|----------|----------|
| PATSTAT Data Catalog | `context/Documentation_Scripts/DataCatalog_Global_v5.26.pdf` |
| OECD Patent Manual | `context/Useful manuals and other docs/OECD patent statistics manual.pdf` |
| IPC-NACE Concordance | `context/Useful manuals and other docs/IPC_NACE/` |
| NUTS Regionalisation | `context/Useful manuals and other docs/NUTS_regionalisation/` |
| Legal Event Codes | `context/Useful manuals and other docs/Overview_legal_status_events_tls231_2024a.xlsx` |

### Utility Scripts

| Script | Purpose |
|--------|---------|
| `context/load_patstat_local.py` | Load PATSTAT CSV to BigQuery |
| `context/create_patstat_tables.sql` | PostgreSQL schema (reference) |

## Getting Started

### For New Queries

1. Review [Query Catalog](./query-catalog.md) for existing patterns
2. Check [BigQuery Schema](./bigquery-schema.md) for table structures
3. Use [Data Loading Guide](./data-loading.md) if setting up your own database

### For Feature Development

1. Read [Project Overview](./project-overview.md) for architecture understanding
2. Main entry point: `app.py`
3. Query definitions: `queries_bq.py`
4. Test with: `python test_queries.py`

### Common Patterns

```python
# BigQuery query execution (from app.py)
job_config = bigquery.QueryJobConfig(
    default_dataset=f"{project}.{dataset}"
)
result = client.query(sql, job_config=job_config).to_dataframe()

# Adding stakeholder tag filter
def get_filtered_queries(stakeholder_filter: str) -> dict:
    if stakeholder_filter == "Alle":
        return QUERIES
    return {
        qid: qinfo for qid, qinfo in QUERIES.items()
        if stakeholder_filter in qinfo.get("tags", [])
    }
```

## Contact

- **Author:** Arne Krueger
- **Email:** arne@mtc.berlin
- **LinkedIn:** [linkedin.com/in/herrkrueger](https://www.linkedin.com/in/herrkrueger/)
- **Issues:** [github.com/herrkrueger/patstat/issues](https://github.com/herrkrueger/patstat/issues)
