# PATSTAT Explorer - Project Overview

**Last Updated:** 2026-02-01 | **Version:** 2.0 (Post Epic 6 Refactor)

## Executive Summary

PATSTAT Explorer is a **Streamlit-based web application** that enables patent information professionals (PATLIB staff) to explore EPO PATSTAT data without programming skills. It serves as a **bridge to TIP** (Technology Intelligence Platform), allowing users to:

1. **Explore** 42 ready-to-use patent analysis queries
2. **Customize** parameters (year range, jurisdictions, technology fields) via UI
3. **Visualize** results with automatic charts and insights
4. **Export** queries to TIP's Jupyter environment for advanced analysis
5. **Generate** custom queries using AI (natural language → SQL)

**Live Demo:** [patstatexplorer.depa.tech](https://patstatexplorer.depa.tech/)

### TIP4PATLIB Alignment

This application directly addresses EPO's TIP4PATLIB requirements:

| EPO Requirement | Implementation |
|-----------------|----------------|
| Ready-to-use queries without coding | 42 parameterized queries with UI controls |
| Regional, sectoral, comparative analysis | Queries organized by category (Regional, Competitors, Trends, Technology) |
| Step-by-step guidance | Query explanations, methodology, key outputs |
| Parameter adaptation without programming | Dynamic parameter UI (sliders, multiselects) |
| TIP integration | "Take to TIP" export with ready-to-run Python code |

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                Coolify (patstatexplorer.depa.tech)           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                     app.py (72 lines)                 │  │
│  │                    Entry Point + Router               │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                  │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │                   modules/ (1,802 lines)              │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐  │  │
│  │  │config.py│ │ data.py │ │logic.py │ │   ui.py     │  │  │
│  │  │Constants│ │BigQuery │ │Business │ │ Rendering   │  │  │
│  │  │ Colors  │ │ Client  │ │  Logic  │ │ Components  │  │  │
│  │  │ Config  │ │Execution│ │ AI/Filter│ │   Pages    │  │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────────┘  │  │
│  │                      ┌─────────┐                      │  │
│  │                      │utils.py │                      │  │
│  │                      │Helpers  │                      │  │
│  │                      └─────────┘                      │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                  │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │              queries_bq.py (3,893 lines)              │  │
│  │                 42 Query Definitions                   │  │
│  │          (SQL + metadata + parameters)                 │  │
│  └───────────────────────┬───────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Google BigQuery │
                  │   patstat-mtc    │
                  │    ~450 GB       │
                  │   27 tables      │
                  └─────────────────┘
```

### Module Responsibilities

| Module | Lines | Responsibility |
|--------|-------|----------------|
| `app.py` | 72 | Entry point, page routing, session state initialization |
| `modules/config.py` | 123 | Constants, color palette, tech fields, AI system prompt |
| `modules/data.py` | 156 | BigQuery client, query execution, parameter handling |
| `modules/logic.py` | 238 | Business logic, filtering, AI client, contribution flow |
| `modules/ui.py` | 1,193 | All Streamlit rendering (pages, components, charts) |
| `modules/utils.py` | 84 | Pure helper functions (formatting, SQL parsing) |
| `queries_bq.py` | 3,893 | Query definitions with metadata and SQL |

---

## Technology Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **UI Framework** | Streamlit | >= 1.28.0 | Web application framework |
| **Data Processing** | pandas | >= 2.0.0 | DataFrame operations |
| **Database** | Google BigQuery | >= 3.13.0 | PATSTAT data storage (~450 GB) |
| **Visualization** | Altair | >= 5.0.0 | Interactive charts |
| **AI Integration** | Anthropic Claude | >= 0.7.0 | Natural language → SQL |
| **Configuration** | python-dotenv | >= 1.0.0 | Environment variables |

---

## Data Architecture

### BigQuery Database

| Project | Dataset | Region | Total Size |
|---------|---------|--------|------------|
| `patstat-mtc` | `patstat` | EU | ~450 GB |

### Key Tables

| Table | Rows | Description |
|-------|------|-------------|
| `tls201_appln` | 140M | Patent applications (central table) |
| `tls206_person` | 98M | Applicants and inventors |
| `tls207_pers_appln` | 408M | Person-application links |
| `tls209_appln_ipc` | 375M | IPC classifications |
| `tls211_pat_publn` | 168M | Publications |
| `tls212_citation` | 597M | Citation data |
| `tls224_appln_cpc` | 436M | CPC classifications |
| `tls230_appln_techn_field` | 167M | WIPO technology fields |

---

## Key Features

### 1. Question-Based Navigation
- Landing page presents queries as questions ("Who...", "What...", "Which...")
- Category pills for filtering (Competitors, Trends, Regional, Technology)
- Stakeholder tags (PATLIB, BUSINESS, UNIVERSITY)

### 2. Dynamic Parameter System
- Queries define their own parameters in `parameters` dict
- UI automatically renders appropriate controls
- Supported types: `year_range`, `year_picker`, `multiselect`, `select`, `text`

### 3. AI Query Builder
- Natural language input → Claude generates BigQuery SQL
- Explanation + SQL + notes returned
- Preview results before saving
- Save to favorites for session

### 4. TIP Integration ("Take to TIP")
- Panel on every query result page
- Ready-to-run Python code for TIP's Jupyter environment
- SQL parameters substituted with actual values
- PatstatClient boilerplate included

### 5. Query Contribution
- Users can submit new queries
- SQL validation before submission
- Test query execution with preview

---

## Source Tree

```
patstat/
├── app.py                      # Entry point (72 lines)
├── queries_bq.py               # 42 queries with metadata (3,893 lines)
├── requirements.txt            # Python dependencies
├── modules/                    # Modular architecture
│   ├── __init__.py
│   ├── config.py              # Constants and configuration
│   ├── data.py                # BigQuery client and execution
│   ├── logic.py               # Business logic and AI
│   ├── ui.py                  # Streamlit UI components
│   └── utils.py               # Pure helper functions
├── tests/                      # Test suite
│   ├── test_filter_queries.py # Search and filter tests
│   ├── test_query_metadata.py # Query validation tests
│   ├── test_ai_builder.py     # AI generation tests
│   ├── test_ai_config.py      # AI configuration tests
│   └── test_contribution.py   # Contribution flow tests
├── docs/                       # Documentation
├── context/                    # Reference materials
│   └── BPM001977_Technical_Specifications__TIP4PATLIB.pdf
└── .streamlit/                 # Streamlit configuration
```

---

## Development Guide

### Local Setup

```bash
git clone https://github.com/herrkrueger/patstat.git
cd patstat
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Configure credentials
streamlit run app.py
```

### Testing

```bash
pytest tests/ -v
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BIGQUERY_PROJECT` | Yes | GCP project ID (default: `patstat-mtc`) |
| `BIGQUERY_DATASET` | Yes | BigQuery dataset name (default: `patstat`) |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | Yes* | Service account JSON |
| `ANTHROPIC_API_KEY` | No | For AI Query Builder |

---

## Related Documentation

- [Query Design Patterns](./query-design-patterns.md) - How queries are structured
- [Query Catalog](./query-catalog.md) - Complete query reference (42 queries)
- [BigQuery Schema](./bigquery-schema.md) - PATSTAT table definitions
- [What Worked Well](./what-worked-well.md) - Lessons learned

---

## License

All code by Arne Krueger is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Contact

- **Author:** Arne Krueger
- **Email:** arne@mtc.berlin
- **GitHub:** [github.com/herrkrueger/patstat](https://github.com/herrkrueger/patstat)
