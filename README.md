# PATSTAT Explorer

Streamlit-Anwendung zur Analyse der EPO PATSTAT-Datenbank auf Google BigQuery.

**Live:** https://patstat.streamlit.app/

## Übersicht

PATSTAT Explorer bietet 18 vordefinierte SQL-Abfragen zur Patent-Analyse, organisiert in 7 Stakeholder-Kategorien:

| Kategorie | Abfragen | Beschreibung |
|-----------|----------|--------------|
| **Overview** | 5 | Datenbankstatistiken, Filing-Trends, IPC-Verteilung |
| **Strategic Planning** | 2 | Länderaktivität, Green-Tech-Trends |
| **Technology Scouting** | 3 | AI/ERP-Patente, Medizindiagnostik, Technologiefelder |
| **Competitive Intelligence** | 2 | Top-Anmelder, geografische Filing-Strategien |
| **Patent Prosecution** | 2 | Zitationsanalyse, Grant-Raten nach Amt |
| **Regional Analysis (DE)** | 3 | Bundesländer, Pro-Kopf-Metriken, Tech-Sektoren |
| **Technology Transfer** | 1 | Schnellstwachsende G06Q-Unterklassen |

## Projektstruktur

```
patstat/
├── app.py              # Streamlit Web-Anwendung
├── queries_bq.py       # 18 BigQuery-Abfragen
├── requirements.txt    # Python-Abhängigkeiten
├── .env.example        # Umgebungsvariablen-Template
└── context/            # Dokumentation & Hilfsskripte
```

## Lokale Entwicklung

### Voraussetzungen

- Python 3.9+
- Google Cloud Service Account mit BigQuery-Zugriff

### Installation

```bash
pip install -r requirements.txt
```

### Konfiguration

Erstelle eine `.env`-Datei:

```bash
# BigQuery
BIGQUERY_PROJECT=patstat-mtc
BIGQUERY_DATASET=patstat

# Service Account Credentials (JSON als einzeiliger String)
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account","project_id":"patstat-mtc",...}
```

### Starten

```bash
streamlit run app.py
```

Die App läuft unter http://localhost:8501

## Streamlit Cloud Deployment

Die App wird automatisch bei Push auf `main` deployed.

### Secrets konfigurieren

In Streamlit Cloud → App Settings → Secrets:

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

## BigQuery-Datenbank

| Projekt | Dataset | Region |
|---------|---------|--------|
| `patstat-mtc` | `patstat` | EU |

### Wichtige Tabellen (~450 GB gesamt)

| Tabelle | Zeilen | Größe | Beschreibung |
|---------|--------|-------|--------------|
| tls201_appln | 140M | ~25 GB | Patentanmeldungen |
| tls212_citation | 597M | ~40 GB | Zitationsdaten |
| tls224_appln_cpc | 436M | ~9 GB | CPC-Klassifikationen |
| tls207_pers_appln | 408M | ~12 GB | Person-Anmeldung-Verknüpfungen |
| tls209_appln_ipc | 375M | ~15 GB | IPC-Klassifikationen |
| tls211_pat_publn | 168M | ~10 GB | Veröffentlichungen |
| tls206_person | 98M | ~16 GB | Anmelder/Erfinder |

### Performance

| Metrik | Wert |
|--------|------|
| Erste Abfrage | 1-5s |
| Gecachte Abfrage | 0.3-1s |
| Geschätzte Kosten | ~$5-10/Monat |

## Entwicklung

### Neue Abfrage hinzufügen

1. `queries_bq.py` bearbeiten
2. Abfrage in passende Kategorie einfügen
3. Metadaten angeben: `description`, `explanation`, `key_outputs`, `estimated_seconds_cached`, `estimated_seconds_first_run`
4. Erst in BigQuery Console testen

### BigQuery SQL-Syntax

```sql
-- Tabellennamen ohne Prefix (Default-Dataset wird automatisch gesetzt)
SELECT * FROM tls201_appln

-- Type Casting
CAST(field AS STRING)

-- Datum-Arithmetik
DATE_DIFF(date1, date2, DAY)
```

## Zugriff

Für lokale Entwicklung werden Google Cloud Credentials benötigt.

**Credentials anfragen bei:** arne.krueger@mtc.berlin

Du erhältst eine JSON-Datei mit dem Service Account, die du in der `.env` als `GOOGLE_APPLICATION_CREDENTIALS_JSON` einträgst (siehe Konfiguration oben).

---

**PATSTAT Version:** 2024 Autumn Edition
