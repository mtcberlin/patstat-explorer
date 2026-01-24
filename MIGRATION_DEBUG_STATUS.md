# Migration Debug Status - 2026-01-24 17:20

## Problem

BigQuery autodetect interpretiert `appln_nr` als INT64, aber es muss STRING sein wegen Werten wie "278120D".

## Was NICHT funktioniert hat

1. ❌ **max_bad_records erhöhen** (10,000 → 1,000,000)
   - Würde legitime Daten verlieren
   - "278120D" ist KEIN Fehler, sondern gültiger Wert
   - In PostgreSQL wurden diese Daten erfolgreich geladen

2. ❌ **EPO-Schema laden aber trotzdem autodetect nutzen**
   - Schema geladen, aber gar nicht verwendet
   - Sinnlos - autodetect überschreibt alles

## Root Cause

**`bq load` mit `--autodetect` rät Datentypen falsch:**
- Sieht viele Zahlen in `appln_nr` → wählt INT64
- Findet "278120D" → interpretiert als Fehler
- Aber: `appln_nr` ist im EPO-Schema als STRING definiert!

## Richtige Lösung

`bq load` muss **explizites Schema** bekommen, nicht autodetect:

```bash
# FALSCH (aktuell):
bq load --autodetect table.csv

# RICHTIG:
bq load table.csv appln_id:INTEGER,appln_auth:STRING,appln_nr:STRING,...
```

## Verfügbare Ressourcen

- ✅ EPO-Schemas in `archive/migration/schemas/schema_*.json`
- ✅ Funktion `load_epo_schema()` bereits geschrieben (aber nicht genutzt!)
- ✅ Schema-Format bekannt: "col1:TYPE,col2:TYPE,..."

## Was zu tun ist

### Option A: Schema als Parameter übergeben

```python
# In load_csv_to_bq():
if is_first:
    if epo_schema:
        cmd.append(full_table)
        cmd.append(csv_file)
        cmd.append(epo_schema)  # Schema als dritter Parameter!
    else:
        cmd.append("--autodetect")
        cmd.append(full_table)
        cmd.append(csv_file)
```

### Option B: Schema-Datei erstellen

```python
# Schema in temp file schreiben
schema_file = f"/tmp/schema_{table_name}.json"
with open(schema_file, 'w') as f:
    json.dump(bq_schema_format, f)

cmd.append(f"--schema={schema_file}")
```

## Entscheidung

**Option A** ist einfacher - `bq load` akzeptiert Schema als letzten Parameter:

```
bq load [FLAGS] DESTINATION_TABLE SOURCE_FILE [SCHEMA]
```

## Test vor Full Migration

1. Manueller Test mit tls201_appln und EPO-Schema
2. Prüfen ob "278120D" erfolgreich lädt
3. Verify mit: `bq query 'SELECT appln_nr FROM table WHERE appln_nr LIKE "%D" LIMIT 10'`
4. ERST DANN alle 12 Tabellen

## Nächste Schritte

1. ❌ KEIN wildes Rumprobieren mehr
2. ✅ migrate_to_bq.py RICHTIG fixen (Schema tatsächlich nutzen)
3. ✅ Manueller Test mit einer Tabelle
4. ✅ Verify dass "D"-Werte geladen werden
5. ✅ Dann erst Batch-Migration

## Status

- **Prozesse**: Alle gestoppt
- **Script**: Kaputt - lädt Schema aber nutzt es nicht
- **Daten**: Keine Datenverluste bisher (nichts committed)
- **Nächster Schritt**: Systematisch Option A implementieren und testen
