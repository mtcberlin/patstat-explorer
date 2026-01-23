# PATSTAT Explorer

Patent analysis tools for the EPO PATSTAT database.

## Repository Structure

```
patstat/
├── app.py                 # Streamlit web application
├── queries_pg.py          # PostgreSQL queries (18 stakeholder queries)
├── test_queries_pg.py     # PostgreSQL query test runner
├── requirements.txt       # Python dependencies for Streamlit app
│
├── epo_tests/             # BigQuery tests (EPO TIP environment)
│   ├── queries_bq.py      # BigQuery queries with timing estimates
│   ├── test_queries_bq.py # BigQuery query test runner
│   └── inspect_epo_schema.py  # EPO schema inspection tool
│
└── migration/             # BigQuery migration tools
    ├── migrate_to_bq.py   # CSV to BigQuery loader
    ├── bq_migration_plan.md   # Migration documentation
    └── schemas/           # Exported EPO schemas
```

## Components

### 1. Streamlit App (Root)

Interactive web interface for exploring PATSTAT data via PostgreSQL.

```bash
# Install dependencies
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env with your PostgreSQL connection

# Run the app
streamlit run app.py
```

**Note:** PostgreSQL performance is significantly slower than BigQuery (~100x). Consider using BigQuery for production workloads.

### 2. EPO BigQuery Tests (`epo_tests/`)

Query validation and performance testing for EPO's PATSTAT BigQuery instance.

**Requirements:** Must be run in EPO TIP Jupyter environment with `PatstatClient` access.

```python
# In EPO Jupyter notebook
%run test_queries_bq.py

# Or test a single query
%run test_queries_bq.py "Overview" "Database Statistics"
```

**Performance:**
- First run: ~86s total (18 queries)
- Cached: ~7s total (12x speedup)

### 3. Migration Tools (`migration/`)

Scripts for migrating PATSTAT data to your own BigQuery project.

```bash
# Step 1: Export EPO schema (run in EPO Jupyter)
python inspect_epo_schema.py

# Step 2: Load CSVs to your BigQuery project
python migrate_to_bq.py /path/to/csvs --list      # Preview files
python migrate_to_bq.py /path/to/csvs --dry-run   # Test run
python migrate_to_bq.py /path/to/csvs             # Execute
```

See `migration/bq_migration_plan.md` for detailed migration documentation.

## Query Categories

The 18 included queries cover various stakeholder needs:

| Category | Queries | Description |
|----------|---------|-------------|
| Overview | 5 | Database statistics, filing trends, IPC distribution |
| Technology Intelligence | 3 | AI/ERP patents, medical diagnostics, technology fields |
| Competitive Intelligence | 4 | Top applicants, competitor analysis, citation networks |
| Regional Analysis | 4 | German federal states, per-capita analysis, tech specialization |
| Trend Analysis | 2 | Business method patents, emerging subclasses |

## Database Comparison

| Database | First Run | Cached | Notes |
|----------|-----------|--------|-------|
| EPO BigQuery | ~86s | ~7s | Best performance, requires EPO access |
| Own BigQuery | ~60-90s | ~5-10s | Full control, ~$15-30/month |
| PostgreSQL | ~110s+ | N/A | Very slow for analytical queries |

## EPO PATSTAT Schema

Key tables (from EPO BigQuery):

| Table | Rows | Size | Description |
|-------|------|------|-------------|
| tls201_appln | 140M | 25 GB | Patent applications |
| tls212_citation | 597M | 40 GB | Citation data |
| tls224_appln_cpc | 436M | 9 GB | CPC classifications |
| tls207_pers_appln | 408M | 12 GB | Person-Application links |
| tls209_appln_ipc | 375M | 15 GB | IPC classifications |
| tls211_pat_publn | 168M | 10 GB | Patent publications |
| tls206_person | 98M | 16 GB | Persons (applicants/inventors) |

## License

Internal use only.
