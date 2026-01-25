# PATSTAT Explorer

Patent analysis tools for the EPO PATSTAT database on Google BigQuery "patstat-mtc".

## Repository Structure
```
patstat/
├── app.py                           # Streamlit web application
├── queries_bq.py                    # BigQuery queries (18 queries, 7 categories)
├── requirements.txt                 # Python dependencies
```

## Quick Start

### Prerequisites

1. **Google Cloud Access**
   Admin account: via arne.krueger@mtc.berlin
   Service account created for sharing:
  - Email: patstat-reader@patstat-mtc.iam.gserviceaccount.com
  - Credentials: /Users/arnekrueger/patstat-reader-credentials.json
  - Permissions: Read-only access (dataViewer + jobUser)

2. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Run the App

```bash
cp .env.example .env
# Edit .env if needed (defaults work for most cases)

streamlit run app.py
```

The app will be available at http://localhost:8501
and is deployed to: https://patstat.streamlit.app/

## Query Categories

18 BigQuery queries across 7 stakeholder categories:

| Category | Queries | Description |
|----------|---------|-------------|
| **Overview** | 5 | Database stats, filing trends, IPC distribution |
| **Strategic Planning** | 2 | Country activity, green technology trends |
| **Technology Scouting** | 3 | AI/ERP patents, medical diagnostics, tech fields |
| **Competitive Intelligence** | 2 | Top applicants, geographic filing strategies |
| **Patent Prosecution** | 2 | Citation analysis, grant rates by office |
| **Regional Analysis (DE)** | 3 | Federal states, per-capita metrics, tech sectors |
| **Technology Transfer** | 1 | Fastest-growing G06Q subclasses |

## Database Architecture

**BigQuery Project:** `patstat-mtc`
**Dataset:** `patstat` (EU region)
**Tables:** 28 PATSTAT tables (~450GB total)

### Key Tables

| Table | Rows | Size | Description |
|-------|------|------|-------------|
| tls201_appln | 140M | ~25 GB | Patent applications |
| tls212_citation | 597M | ~40 GB | Citation data |
| tls224_appln_cpc | 436M | ~9 GB | CPC classifications |
| tls207_pers_appln | 408M | ~12 GB | Person-Application links |
| tls209_appln_ipc | 375M | ~15 GB | IPC classifications |
| tls211_pat_publn | 168M | ~10 GB | Publications |
| tls206_person | 98M | ~16 GB | Applicants/Inventors |

## Performance

| Metric | Value | Notes |
|--------|-------|-------|
| **First Run** | ~60-90s | All 18 queries, cold cache |
| **Cached** | ~5-10s | BigQuery query cache warm |
| **Single Query** | 0.3-7s | Depends on complexity |
| **Cost** | ~$5-10/month | Storage + query processing |

## Environment Configuration

The `.env.example` file contains:

```bash
# BigQuery Configuration
BIGQUERY_PROJECT=patstat-mtc
BIGQUERY_DATASET=patstat

# Optional: Service Account Key
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json

# Streamlit Settings
STREAMLIT_SERVER_PORT=8501
```

## Development

### Query Syntax

All queries use BigQuery SQL syntax:

```sql
-- Table names with backticks and full qualification
FROM `patstat-mtc.patstat.tls201_appln`

-- Type casting
CAST(field AS STRING)

-- Date arithmetic
DATE_DIFF(date1, date2, DAY)

-- Window functions
COUNT(*) OVER (PARTITION BY field)
```

### Adding New Queries

1. Edit `queries_bq.py`
2. Add query to appropriate category dictionary
3. Include metadata: `description`, `explanation`, `key_outputs`, `estimated_seconds_*`
4. Test in BigQuery console first
5. Update `app.py` if needed

## License

mtc Internal use only.

---

**Last Updated:** 2026-01-24
**PATSTAT Version:** 2024 Autumn Edition
**BigQuery Dataset:** `patstat-mtc.patstat`
