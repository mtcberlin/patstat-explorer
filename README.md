# PATSTAT Explorer

A Streamlit application for analyzing the EPO PATSTAT patent database on Google BigQuery.

**Live Demo:** [patstat.streamlit.app](https://patstat.streamlit.app/)

## Overview

PATSTAT Explorer provides **19 predefined SQL queries** (18 static + 1 dynamic/interactive) for patent analysis, filterable by three stakeholder perspectives:

| Stakeholder | Description | Queries |
|-------------|-------------|---------|
| **PATLIB** | Patent Information Centers & Libraries | 8 |
| **BUSINESS** | Companies & Industry | 11 |
| **UNIVERSITY** | Universities & Research | 6 |

### Query Catalog

| ID | Title | Tags | Description |
|----|-------|------|-------------|
| Q01 | Database Statistics | PATLIB | Overall PATSTAT database statistics and key metrics |
| Q02 | Filing Authorities | PATLIB | Patent offices with application counts |
| Q03 | Applications by Year | PATLIB | Patent application trends over time |
| Q04 | Top IPC Classes | PATLIB | Most common IPC technology classes |
| Q05 | Sample Patents | PATLIB | Sample of 100 patent applications |
| Q06 | Country Patent Activity | PATLIB, BUSINESS | Country ranking by patent volume since 2015 |
| Q07 | Green Technology Trends | BUSINESS, UNIVERSITY | G7+China+Korea with green tech (CPC Y02) focus |
| Q08 | Most Active Technology Fields | BUSINESS, UNIVERSITY | Technology fields with family size and citation impact |
| Q09 | AI-based ERP Patent Landscape | BUSINESS | AI+ERP intersection (G06Q10 + G06N) since 2018 |
| Q10 | AI-Assisted Diagnostics Companies | BUSINESS, UNIVERSITY | Companies in AI diagnostics (A61B + G06N) |
| Q11 | Top Patent Applicants | BUSINESS | Top applicants since 2010 with portfolio profile |
| Q12 | Competitor Filing Strategy (MedTech) | BUSINESS | Where major MedTech competitors file patents |
| Q13 | Most Cited Patents (2020) | UNIVERSITY | Most influential prior art patents |
| Q14 | Diagnostic Imaging Grant Rates | BUSINESS, UNIVERSITY | A61B 6/ grant rates at EPO vs USPTO vs CNIPA |
| Q15 | German States - Medical Tech | PATLIB | German federal states in A61B diagnosis/surgery |
| Q16 | German States - Per Capita Analysis | PATLIB | A61B activity with per-capita comparison |
| Q17 | Regional Tech Sector Comparison | PATLIB | Sachsen, Bayern, Baden-Württemberg by WIPO sectors |
| Q18 | Fastest-Growing G06Q Subclasses | BUSINESS, UNIVERSITY | Growth trends in IT methods for management |
| **DQ01** | **Technology Trend Analysis** | ALL | **Interactive** analysis with customizable parameters |

## Features

- **Interactive Analysis Panel**: Dynamic query with customizable jurisdiction, technology field, and year range
- **Predefined Query Library**: 18 static queries covering database exploration, market intelligence, technology scouting, competitive analysis, citations, and regional analysis
- **Stakeholder Filtering**: Filter queries by PATLIB, BUSINESS, or UNIVERSITY perspective
- **Result Visualization**: Tables with metrics, line charts for trends
- **Export Options**: Download results as CSV
- **Query Documentation**: Each query includes explanation and key outputs
- **Performance Estimates**: Cached vs. first-run timing displayed per query

## Project Structure

```
patstat/
├── app.py                  # Streamlit web application (entry point)
├── queries_bq.py           # 19 BigQuery queries with metadata
├── test_queries.py         # Query validation and timing tests
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── docs/                   # Generated documentation
│   ├── index.md           # Documentation index
│   ├── project-overview.md # Architecture and tech stack
│   ├── query-catalog.md   # Complete query reference
│   ├── bigquery-schema.md # PATSTAT table definitions
│   └── data-loading.md    # BigQuery loading guide
└── context/                # Reference materials
    ├── load_patstat_local.py      # BigQuery data loading utility
    ├── create_patstat_tables.sql  # PostgreSQL schema (reference)
    └── Documentation_Scripts/     # EPO PATSTAT reference docs
```

## Local Development

### Prerequisites

- Python 3.9+
- Google Cloud Service Account with BigQuery access

### Installation

```bash
git clone https://github.com/herrkrueger/patstat.git
cd patstat
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```bash
# BigQuery Configuration
BIGQUERY_PROJECT=patstat-mtc
BIGQUERY_DATASET=patstat

# Service Account Credentials (JSON as single-line string)
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"patstat-mtc",...}
```

### Running Locally

```bash
streamlit run app.py
```

The app will be available at `http://localhost:8501`

### Testing

```bash
# Run all query tests with timing report
python test_queries.py
```

## Streamlit Cloud Deployment

The app is automatically deployed on push to the `main` branch.

### Configure Secrets

In Streamlit Cloud → App Settings → Secrets, add:

```toml
[gcp_service_account]
type = "service_account"
project_id = "patstat-mtc"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "patstat-reader@patstat-mtc.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
universe_domain = "googleapis.com"
```

## BigQuery Database

| Project | Dataset | Region | Size |
|---------|---------|--------|------|
| `patstat-mtc` | `patstat` | EU | ~450 GB |

### Key Tables (27 total)

| Table | Rows | Description |
|-------|------|-------------|
| tls201_appln | 140M | Patent applications (central table) |
| tls206_person | 98M | Applicants/Inventors |
| tls207_pers_appln | 408M | Person-application links |
| tls209_appln_ipc | 375M | IPC classifications |
| tls211_pat_publn | 168M | Publications |
| tls212_citation | 597M | Citation data |
| tls224_appln_cpc | 436M | CPC classifications |
| tls230_appln_techn_field | 167M | WIPO technology field assignments |
| tls801_country | 242 | Country reference data |
| tls901_techn_field_ipc | 771 | WIPO technology field definitions |
| tls904_nuts | 2,056 | NUTS regional codes |

See [docs/bigquery-schema.md](docs/bigquery-schema.md) for complete schema documentation.

### Performance

| Metric | Value |
|--------|-------|
| First query | 1-14s (depending on complexity) |
| Cached query | 0.3-1s |
| Estimated cost | ~$5-10/month |

## Development Guide

### Adding a New Query

1. Edit `queries_bq.py`
2. Add a new entry with the next ID (e.g., `Q19`)
3. Include required metadata:
   - `title`: Short query name
   - `tags`: List of stakeholder tags (`PATLIB`, `BUSINESS`, `UNIVERSITY`)
   - `description`: One-line description
   - `explanation`: Detailed explanation of what the query does
   - `key_outputs`: List of key metrics returned
   - `estimated_seconds_first_run`: Expected time for uncached query
   - `estimated_seconds_cached`: Expected time for cached query
   - `sql`: The BigQuery SQL statement
4. Test in BigQuery Console first
5. Run `python test_queries.py` to validate

See [docs/query-catalog.md](docs/query-catalog.md) for detailed query documentation and SQL patterns.

### BigQuery SQL Syntax

```sql
-- Table names without prefix (default dataset is set automatically)
SELECT * FROM tls201_appln

-- Type casting
CAST(field AS STRING)

-- Date arithmetic
DATE_DIFF(date1, date2, DAY)

-- IPC/CPC pattern matching
WHERE ipc_class_symbol LIKE 'A61B%'

-- WIPO technology field join (use weight > 0.5 for primary assignment)
JOIN tls230_appln_techn_field tf ON a.appln_id = tf.appln_id
WHERE tf.weight > 0.5
```

## Documentation

Detailed documentation is available in the `docs/` folder:

- [Documentation Index](docs/index.md) - Start here
- [Project Overview](docs/project-overview.md) - Architecture and setup
- [Query Catalog](docs/query-catalog.md) - Complete query reference with SQL
- [BigQuery Schema](docs/bigquery-schema.md) - All 27 PATSTAT tables
- [Data Loading Guide](docs/data-loading.md) - Loading PATSTAT to BigQuery

## Data Access

For local development, Google Cloud credentials are required.

**Request credentials:** arne@mtc.berlin

You will receive a JSON file with the service account. Add it to your `.env` file as `GOOGLE_APPLICATION_CREDENTIALS_JSON` (see Configuration above).

## License

All code in this project © 2026 by Arne Krueger is licensed under [CC BY 4.0 (Attribution 4.0 International)](https://creativecommons.org/licenses/by/4.0/).

When using this code, please credit as follows:

> Code authored by Arne Krueger, mtc.berlin, 2026.

## Contact

**Report bugs or request features:** [GitHub Issues](https://github.com/herrkrueger/patstat/issues)

**Email:** arne@mtc.berlin

**LinkedIn:** [linkedin.com/in/herrkrueger](https://www.linkedin.com/in/herrkrueger/)

---

**PATSTAT Version:** 2025 Autumn Edition
