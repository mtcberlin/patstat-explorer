# Archive Directory

This directory contains files that are no longer actively used in the project but kept for reference.

## PostgreSQL (Deprecated 2026-01-24)

The project migrated from PostgreSQL to BigQuery. PostgreSQL-related files are archived here.

**Archived files:**
- `postgresql/queries_pg.py` - PostgreSQL query definitions (20 queries)
- `postgresql/test_queries_pg.py` - PostgreSQL test runner
- `postgresql/.env.example` - PostgreSQL environment template

**Reason for deprecation:** BigQuery provides better performance (~7s vs 110s+), built-in caching, and alignment with EPO's PATSTAT environment.

**Restoration:** If needed, these files can be copied back to the project root, though this is not recommended.

## Migration Timeline

- **2026-01-23:** BigQuery CSV migration completed
- **2026-01-24:** PostgreSQL code archived, BigQuery migration planned
