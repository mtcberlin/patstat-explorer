# Schema Problem - Status 2026-01-24 17:25

## Das Problem

BigQuery `--autodetect` interpretiert `appln_nr` als INT64, aber es muss STRING sein.

**Beweis:**
- CSV enthält Werte wie "278120D", "10335D", etc.
- Das sind **legitime Daten**, keine Fehler
- In PostgreSQL wurden diese erfolgreich geladen
- EPO-Schema (schema_tls201_appln.json) zeigt: `appln_nr:STRING`

## Warum autodetect versagt

```bash
# CSV Inhalt:
5036189,CA,278120D,A ,9999-12-31,9999,...

# autodetect sieht:
# - Spalte 1: nur Zahlen → INT64 ✓
# - Spalte 2: CA, CH, DE → STRING ✓
# - Spalte 3: 278120, 10335, ... → INT64 ✗ FALSCH!
#   → Findet später "278120D" → Error: "Unable to parse"
```

## Was funktionieren MUSS

```bash
# FALSCH (aktuell):
bq load --autodetect patstat-mtc:patstat.tls201_appln file.csv

# RICHTIG:
bq load patstat-mtc:patstat.tls201_appln file.csv \
  appln_id:INT64,appln_auth:STRING,appln_nr:STRING,...
```

## Was ich NICHT kann

❌ Auf EPO TIP BigQuery zugreifen (Permission denied)
❌ Schemas von dort holen
❌ Das muss der User machen

## Was der User tun muss

1. **Schemas aus EPO TIP holen** (du hast Zugriff)

   ```bash
   # Für alle 12 Tabellen, die wir migrieren wollen:
   bq show --schema --format=prettyjson \
     p-epo-tip-prj-3a1f:p_epo_tip_euwe4_bqd_patstatb.tls201_appln \
     > schemas/tls201_appln_bq.json

   bq show --schema --format=prettyjson \
     p-epo-tip-prj-3a1f:p_epo_tip_euwe4_bqd_patstatb.tls206_person \
     > schemas/tls206_person_bq.json

   # etc. für alle 12 Tabellen aus retry_small_tables.sh
   ```

2. **Schemas in bq-Load-Format konvertieren**

   Ich habe ein Script geschrieben: `generate_schemas.py`

   Aber: Es braucht die echten EPO-Schemas als Input, nicht CSV-basierte Ratearbeit!

## Die 12 Tabellen (aus retry_small_tables.sh)

```
tls201_appln
tls206_person
tls209_appln_ipc
tls211_pat_publn
tls212_citation
tls214_npl_publn
tls215_citn_categ
tls222_appln_jp_class
tls224_appln_cpc
tls225_docdb_fam_cpc
tls226_person_orig
tls227_pers_publn
```

## Nächste Schritte (User)

1. Schemas aus EPO TIP holen für diese 12 Tabellen
2. In `schemas/` Ordner speichern
3. Mir sagen, dass die Schemas da sind
4. Dann kann ich migrate_to_bq.py so umbauen, dass es die Schemas lädt und verwendet

## Nächste Schritte (Claude)

1. ✅ Status dokumentiert
2. ✅ Git commit + push
3. ⏳ Warten auf User: Schemas aus EPO TIP
4. ⏳ Dann: migrate_to_bq.py fixen um Schemas zu verwenden
5. ⏳ Test mit einer Tabelle
6. ⏳ Dann erst alle 12 Tabellen

## Files im Repo

- `migrate_to_bq.py` - Migration script (derzeit kaputt, nutzt autodetect)
- `generate_schemas.py` - Schema generator (braucht EPO Schemas als Input)
- `convert_schema.py` - JSON → bq format converter
- `retry_small_tables.sh` - Bash script für 12 Tabellen
- `MIGRATION_DEBUG_STATUS.md` - Analyse des Problems
- `SCHEMA_PROBLEM_STATUS.md` - Dieser Status (was zu tun ist)

## Wichtig

**KEINE weiteren Migrations-Versuche bis Schemas vorhanden sind!**

Sonst wieder:
- Daten verlieren (mit zu hohem max_bad_records)
- Oder Fehler (mit autodetect)
