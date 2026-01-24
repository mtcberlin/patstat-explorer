# PATSTAT BigQuery Migration Plan

## Overview

Migration von PATSTAT Daten in eigenes BigQuery Projekt `patstat-mtc` für bessere Performance und volle Kontrolle.

## Current State

| Umgebung | Status | Performance |
|----------|--------|-------------|
| EPO BigQuery (via PatstatClient) | ✅ Funktioniert | ~86s first run, ~7s cached |
| Lokale PostgreSQL | ✅ Funktioniert | ~110s+ pro Query (sehr langsam) |
| Eigenes BigQuery (patstat-mtc) | 🔄 Setup done | Noch keine Daten |

## Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     patstat-mtc (BigQuery)                   │
├─────────────────────────────────────────────────────────────┤
│  Dataset: patstat                                            │
│  Location: EU                                                │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │ tls201_appln│  │ tls206_person│  │ tls207_pers │          │
│  │ (partitioned│  │ (clustered) │  │   _appln    │          │
│  │  by year)   │  │             │  │ (clustered) │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                              │
│  + 25 weitere PATSTAT Tabellen                               │
└─────────────────────────────────────────────────────────────┘
```

## Data Sources

CSV-Dateien lokal vorhanden (Arne's MacBook):
- Pfad: TBD
- Format: CSV mit Header
- Encoding: UTF-8 (vermutlich)

## Migration Scripts

### 1. Schema Inspection (EPO)
```bash
# In EPO Jupyter Notebook ausführen
python inspect_epo_schema.py
```

Output:
- `epo_patstat_schema_YYYYMMDD_HHMMSS.json` - Vollständiges Schema
- `create_tables_YYYYMMDD_HHMMSS.sql` - CREATE TABLE Statements

### 2. Data Migration
```bash
# Lokal auf MacBook ausführen
python migrate_to_bq.py /path/to/csvs --list      # Preview
python migrate_to_bq.py /path/to/csvs --dry-run   # Test
python migrate_to_bq.py /path/to/csvs             # Execute
```

## Table Configuration

### Key Tables mit Optimierungen

| Table | Partitioning | Clustering | Größe (ca.) |
|-------|-------------|------------|-------------|
| tls201_appln | appln_filing_year (RANGE) | appln_auth, granted | ~150 GB |
| tls206_person | - | person_ctry_code, psn_sector | ~50 GB |
| tls207_pers_appln | - | appln_id, person_id | ~80 GB |
| tls209_appln_ipc | - | appln_id | ~40 GB |
| tls211_pat_publn | publn_date (TIME) | appln_id, publn_auth | ~60 GB |
| tls212_citation | - | pat_publn_id, cited_pat_publn_id | ~100 GB |
| tls224_appln_cpc | - | appln_id | ~50 GB |

### Lookup Tables (klein)
- tls801_country
- tls803_legal_event_code
- tls901_techn_field_ipc
- tls902_ipc_nace2
- tls904_nuts

## Migration Steps

### Phase 1: Schema Export ✅
- [x] inspect_epo_schema.py erstellt
- [ ] In EPO Jupyter ausführen
- [ ] Schema JSON exportieren
- [ ] CREATE TABLE Statements generieren

### Phase 2: Dataset Setup
- [x] BigQuery Projekt erstellt (patstat-mtc)
- [ ] Dataset `patstat` in EU Region erstellen
- [ ] Service Account für Migrations-Script

### Phase 3: Data Load
- [ ] CSV Pfade identifizieren
- [ ] migrate_to_bq.py mit --dry-run testen
- [ ] Kleine Tabellen zuerst (tls801, tls901, etc.)
- [ ] Große Tabellen laden (tls201, tls206, etc.)

### Phase 4: Validation
- [ ] Row counts vergleichen mit EPO
- [ ] Test-Queries ausführen
- [ ] Performance messen

### Phase 5: App Integration
- [ ] queries_bq.py anpassen für eigenes Dataset
- [ ] Neuen BigQuery Client erstellen (ohne PatstatClient)
- [ ] Streamlit App updaten

## Queries Anpassung

Aktuell (EPO PatstatClient):
```python
from epo.tipdata.patstat import PatstatClient
patstat = PatstatClient(env='PROD')
result = patstat.sql_query(query, use_legacy_sql=False)
```

Neu (eigenes BigQuery):
```python
from google.cloud import bigquery
client = bigquery.Client(project='patstat-mtc')
result = client.query(query).to_dataframe()
```

SQL Änderung:
```sql
-- EPO (unqualifiziert)
SELECT * FROM tls201_appln

-- Eigenes BQ (voll qualifiziert)
SELECT * FROM `patstat-mtc.patstat.tls201_appln`
```

## Cost Estimation

BigQuery Pricing (EU):
- Storage: $0.02/GB/month
- Queries: $5/TB scanned

Geschätzte Kosten:
- Storage (~500GB): ~$10/month
- Queries (light usage): ~$5-20/month
- **Total: ~$15-30/month**

## Performance Expectations

| Szenario | EPO BQ | Eigenes BQ (erwartet) |
|----------|--------|----------------------|
| First run | ~86s | ~60-90s |
| Cached | ~7s | ~5-10s |
| Mit Clustering | - | ~30-50s first run |

Eigenes BQ sollte ähnlich schnell sein - die Columnar Storage Vorteile bleiben gleich.

## Rollback Plan

Falls Migration fehlschlägt:
1. EPO PatstatClient weiter nutzen (funktioniert)
2. PostgreSQL als Fallback (langsam aber funktional)

## Next Actions

1. **Arne**: CSV-Pfad identifizieren
2. **Arne**: inspect_epo_schema.py in EPO Jupyter ausführen
3. **Claude**: Schema JSON analysieren, CREATE TABLEs optimieren
4. **Arne**: migrate_to_bq.py ausführen
5. **Claude**: queries_bq.py für eigenes Dataset anpassen

## Notes

- PATSTAT wird 2x jährlich aktualisiert (Spring/Autumn Edition)
- Bei Updates: Tabellen droppen und neu laden
- Partitioning nach Year ermöglicht effizientes Laden neuer Daten
