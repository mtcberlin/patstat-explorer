# PATSTAT Explorer

Patent analysis tools for the EPO PATSTAT database.

## Repository Structure

```
patstat/
├── app.py                    # Streamlit web application
├── queries_pg.py             # PostgreSQL queries (20 queries, 7 categories)
├── test_queries_pg.py        # PostgreSQL query test runner
├── requirements.txt          # Python dependencies
│
├── epo_tests/                # BigQuery tests (EPO TIP environment)
│   ├── queries_bq.py         # BigQuery queries (18 queries)
│   ├── test_queries_bq.py    # BigQuery test runner
│   └── inspect_epo_schema.py # Schema extraction tool
│
└── migration/                # BigQuery migration tools
    ├── migrate_to_bq.py      # CSV to BigQuery loader
    ├── bq_migration_plan.md  # Migration documentation
    ├── SETUP_MAC.md          # macOS setup guide
    └── schemas/              # Exported EPO schemas
```

## Components

### 1. Streamlit App

Interactive web interface for exploring PATSTAT data via PostgreSQL.

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your DATABASE_URL
streamlit run app.py
```

### 2. PostgreSQL Speed Tests

Test runner for all 20 queries against PostgreSQL.

```bash
python test_queries_pg.py                              # All queries
python test_queries_pg.py "Overview" "Database Tables" # Single query
```

### 3. EPO BigQuery Tests (`epo_tests/`)

Query validation and performance testing for EPO's PATSTAT BigQuery.

**Requires:** EPO TIP environment with `PatstatClient` access.

```python
%run test_queries_bq.py                                # All queries
%run test_queries_bq.py "Overview" "Database Statistics"
```

**Performance:** ~86s first run, ~7s cached (12x speedup)

### 4. Migration Tools (`migration/`)

Migrate PATSTAT data to your own BigQuery project.

```bash
# Step 1: Export EPO schema (in EPO Jupyter)
python inspect_epo_schema.py

# Step 2: Setup BigQuery (see migration/SETUP_MAC.md)

# Step 3: Load CSVs
python migrate_to_bq.py /path/to/csvs --list      # Preview
python migrate_to_bq.py /path/to/csvs --dry-run   # Test
python migrate_to_bq.py /path/to/csvs             # Execute
```

See `migration/bq_migration_plan.md` for detailed documentation.

## Query Categories

20 PostgreSQL queries across 7 stakeholder categories:

| Category | Queries | Description |
|----------|---------|-------------|
| Overview | 5 | Database stats, filing trends, IPC distribution |
| Strategic Planning | 2 | Country activity, green technology trends |
| Technology Scouting | 4 | AI/ERP patents, medical diagnostics |
| Competitive Intelligence | 4 | Top applicants, competitor analysis |
| Patent Prosecution | 2 | Lifecycle analysis, prosecution timing |
| Regional Analysis (DE) | 4 | Federal states, per-capita metrics |
| Technology Transfer | 2 | Licensing opportunities, collaborations |

## Database Performance

| Database | First Run | Cached | Notes |
|----------|-----------|--------|-------|
| EPO BigQuery | ~86s | ~7s | Best performance, requires EPO access |
| Own BigQuery | ~60-90s | ~5-10s | Full control, ~$15-30/month |
| PostgreSQL | ~110s+ | - | Slow, no query caching |

## Key Tables

| Table | Rows | Size | Description |
|-------|------|------|-------------|
| tls201_appln | 140M | 25 GB | Patent applications |
| tls212_citation | 597M | 40 GB | Citation data |
| tls224_appln_cpc | 436M | 9 GB | CPC classifications |
| tls207_pers_appln | 408M | 12 GB | Person-Application links |
| tls209_appln_ipc | 375M | 15 GB | IPC classifications |
| tls211_pat_publn | 168M | 10 GB | Publications |
| tls206_person | 98M | 16 GB | Applicants/Inventors |

## Environment

Copy `.env.example` to `.env` and configure:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/patstat
```

## License

Internal use only.
