# PATSTAT Explorer - Project Overview

**Generated:** 2026-01-26 | **Version:** Deep Scan | **Status:** AI-Assisted Development Reference

## Executive Summary

PATSTAT Explorer is a **Streamlit-based data analytics dashboard** for querying and visualizing the EPO PATSTAT patent database hosted on Google BigQuery. The application provides 19 predefined SQL queries (18 static + 1 dynamic) for patent analysis, filterable by three stakeholder perspectives: PATLIB, BUSINESS, and UNIVERSITY.

**Live Demo:** [patstat.streamlit.app](https://patstat.streamlit.app/)

## Project Classification

| Attribute | Value |
|-----------|-------|
| **Repository Type** | Monolith |
| **Project Type** | Data Analytics Application |
| **Primary Language** | Python 3.9+ |
| **UI Framework** | Streamlit >= 1.28.0 |
| **Database** | Google BigQuery |
| **Data Source** | EPO PATSTAT 2025 Autumn Edition |
| **Deployment** | Streamlit Cloud |

## Technology Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **UI Framework** | Streamlit | >= 1.28.0 | Interactive web dashboard |
| **Data Processing** | pandas | >= 2.0.0 | DataFrame manipulation |
| **Database Client** | google-cloud-bigquery | >= 3.13.0 | BigQuery connectivity |
| **Type Support** | db-dtypes | >= 1.2.0 | BigQuery-pandas type mapping |
| **Configuration** | python-dotenv | >= 1.0.0 | Environment variable management |

## Architecture Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                     Streamlit Cloud                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    app.py                                │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │    │
│  │  │ Interactive  │  │   Query      │  │  Stakeholder │   │    │
│  │  │   Panel      │  │   Panel      │  │    Tabs      │   │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │    │
│  │           │                │                │           │    │
│  │           └────────────────┼────────────────┘           │    │
│  │                            ▼                            │    │
│  │                 ┌──────────────────┐                    │    │
│  │                 │  queries_bq.py   │                    │    │
│  │                 │  19 SQL Queries  │                    │    │
│  │                 │  + Metadata      │                    │    │
│  │                 └────────┬─────────┘                    │    │
│  └──────────────────────────┼──────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│              ┌──────────────────────────────┐                   │
│              │  Google BigQuery Client      │                   │
│              │  (Service Account Auth)      │                   │
│              └──────────────┬───────────────┘                   │
└─────────────────────────────┼───────────────────────────────────┘
                              │
                              ▼
               ┌──────────────────────────────┐
               │     Google BigQuery          │
               │  Project: patstat-mtc        │
               │  Dataset: patstat            │
               │  Region: EU                  │
               │  ~450 GB, 27 tables          │
               └──────────────────────────────┘
```

## Data Architecture

### BigQuery Database

| Project | Dataset | Region | Total Size |
|---------|---------|--------|------------|
| `patstat-mtc` | `patstat` | EU | ~450 GB |

### Key Tables

| Table | Rows | Size | Description |
|-------|------|------|-------------|
| `tls201_appln` | 140M | ~25 GB | Patent applications (central table) |
| `tls206_person` | 98M | ~16 GB | Applicants and inventors |
| `tls207_pers_appln` | 408M | ~12 GB | Person-application links |
| `tls209_appln_ipc` | 375M | ~15 GB | IPC classifications |
| `tls211_pat_publn` | 168M | ~10 GB | Publications |
| `tls212_citation` | 597M | ~40 GB | Citation data |
| `tls224_appln_cpc` | 436M | ~9 GB | CPC classifications |
| `tls230_appln_techn_field` | 167M | - | WIPO technology field assignments |
| `tls801_country` | 242 | - | Country reference data |
| `tls901_techn_field_ipc` | 771 | - | WIPO technology field definitions |
| `tls904_nuts` | 2,056 | - | NUTS regional codes |

### Performance Characteristics

| Metric | Value |
|--------|-------|
| First query (uncached) | 1-14s |
| Cached query | 0.3-1s |
| Estimated cost | ~$5-10/month |

## Source Tree

```
patstat/
├── app.py                      # Streamlit web application (entry point)
├── queries_bq.py               # 19 BigQuery queries with metadata
├── test_queries.py             # Query validation and timing tests
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .env                        # Local configuration (gitignored)
├── .gitignore                  # Git ignore patterns
├── README.md                   # Project documentation (outdated)
├── docs/                       # Generated documentation
│   └── index.md               # Documentation index
├── context/                    # Reference materials
│   ├── load_patstat_local.py  # BigQuery data loading utility
│   ├── create_patstat_tables.sql  # PostgreSQL schema (reference)
│   └── Documentation_Scripts/  # EPO PATSTAT reference docs
│       ├── DataCatalog_Global_v5.26.pdf
│       └── Useful manuals and other docs/
├── .github/
│   └── workflows/
│       └── neon_workflow.yml  # CI/CD for Neon DB (PR preview)
└── .devcontainer/
    └── devcontainer.json      # VS Code dev container config
```

## Development Guide

### Prerequisites

- Python 3.9+
- Google Cloud Service Account with BigQuery access

### Local Setup

```bash
# Clone repository
git clone https://github.com/herrkrueger/patstat.git
cd patstat

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your BigQuery credentials

# Run locally
streamlit run app.py
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BIGQUERY_PROJECT` | Yes | GCP project ID (default: `patstat-mtc`) |
| `BIGQUERY_DATASET` | Yes | BigQuery dataset name (default: `patstat`) |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | Yes* | Service account JSON (single-line string) |

*Required for local development. On Streamlit Cloud, use Secrets instead.

### Streamlit Cloud Secrets

Configure in Streamlit Cloud → App Settings → Secrets:

```toml
[gcp_service_account]
type = "service_account"
project_id = "patstat-mtc"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "patstat-reader@patstat-mtc.iam.gserviceaccount.com"
# ... additional fields
```

## Related Documentation

- [Query Catalog](./query-catalog.md) - Complete query reference
- [BigQuery Schema](./bigquery-schema.md) - PATSTAT table definitions
- [Data Loading Guide](./data-loading.md) - Loading PATSTAT to BigQuery

## License

All code in this project by Arne Krueger is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Contact

- **Author:** Arne Krueger
- **Email:** arne@mtc.berlin
- **LinkedIn:** [linkedin.com/in/herrkrueger](https://www.linkedin.com/in/herrkrueger/)
