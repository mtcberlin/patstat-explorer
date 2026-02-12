# PATSTAT Explorer Documentation Index

**Generated:** 2026-02-01 | **Scan Level:** Deep | **Project Type:** Data Analytics

## Project Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Monolith - Data Analytics Application (Modular Architecture) |
| **Primary Language** | Python |
| **UI Framework** | Streamlit >= 1.28.0 |
| **Database** | Google BigQuery (~450 GB) |
| **AI Integration** | Anthropic Claude (Query Builder) |
| **Data Source** | EPO PATSTAT 2025 Autumn Edition |

### Quick Reference

| Item | Value |
|------|-------|
| **Entry Point** | `app.py` (72 lines) |
| **Modules** | `modules/` (1,802 lines total) |
| **Queries** | `queries_bq.py` (42 queries, 3,893 lines) |
| **Tests** | `tests/` (5 test files) |
| **Live Demo** | [patstatexplorer.depa.tech](https://patstatexplorer.depa.tech/) |

### TIP4PATLIB Alignment

This application serves as a **bridge to TIP** for 300 PATLIB centres, delivering:
- 42 ready-to-use parameterized queries
- No-code parameter adjustment
- AI-powered query generation
- Direct export to TIP Jupyter environment

---

## Generated Documentation

### Core Documentation

| Document | Description |
|----------|-------------|
| [Project Overview](./project-overview.md) | Architecture, tech stack, deployment guide |
| [Query Design Patterns](./query-design-patterns.md) | **NEW** - How queries are structured, SQL patterns |
| [What Worked Well](./what-worked-well.md) | **NEW** - Lessons learned, key decisions |
| [Query Catalog](./query-catalog.md) | Complete reference for 42 queries |
| [BigQuery Schema](./bigquery-schema.md) | PATSTAT table definitions (27 tables) |
| [Data Loading Guide](./data-loading.md) | Loading PATSTAT data to BigQuery |

### Architecture

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
│  │  config.py │ data.py │ logic.py │ ui.py │ utils.py   │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                  │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │              queries_bq.py (42 queries)               │  │
│  └───────────────────────┬───────────────────────────────┘  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Google BigQuery │
                  │   27 tables      │
                  │   ~450 GB        │
                  └─────────────────┘
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Question-Based Navigation** | Queries presented as questions, filtered by category/stakeholder |
| **Dynamic Parameters** | Year range, jurisdictions, tech fields via UI controls |
| **AI Query Builder** | Natural language → SQL using Claude |
| **Take to TIP** | Export ready-to-run code for TIP Jupyter |
| **Visualization** | Auto-generated Altair charts |
| **Contribution** | Users can submit new queries |

---

## Query Summary

**Total:** 42 queries organized by category and stakeholder

### By Category

| Category | Count | Description |
|----------|-------|-------------|
| Trends | 12 | Time-series analysis, growth patterns |
| Competitors | 10 | Applicant rankings, market share |
| Regional | 8 | Geographic analysis, NUTS regions |
| Technology | 12 | IPC/CPC/WIPO field analysis |

### By Stakeholder

| Tag | Count | Description |
|-----|-------|-------------|
| PATLIB | 25 | Patent libraries, information centers |
| BUSINESS | 20 | Companies, industry users |
| UNIVERSITY | 15 | Researchers, academia |

---

## Module Structure

| Module | Lines | Responsibility |
|--------|-------|----------------|
| `config.py` | 123 | Constants, color palette, AI prompt |
| `data.py` | 156 | BigQuery client, query execution |
| `logic.py` | 238 | Business logic, AI, filtering |
| `ui.py` | 1,193 | All Streamlit rendering |
| `utils.py` | 84 | Pure helper functions |

---

## Development Guide

### Local Setup

```bash
git clone https://github.com/herrkrueger/patstat.git
cd patstat
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add credentials
streamlit run app.py
```

### Adding a New Query

1. Add entry to `queries_bq.py` with unique ID
2. Include metadata: title, tags, category, description
3. Define `parameters` for dynamic queries
4. Set `visualization` config for charts
5. Run `pytest tests/test_query_metadata.py`

### Testing

```bash
pytest tests/ -v
```

---

## Reference Materials

| Document | Location |
|----------|----------|
| TIP4PATLIB Specification | `context/BPM001977_Technical_Specifications__TIP4PATLIB.pdf` |
| README | `README.md` |

---

## Getting Started

### For PATLIB Users
1. Visit [patstatexplorer.depa.tech](https://patstatexplorer.depa.tech/)
2. Browse queries by category (Competitors, Trends, Regional, Technology)
3. Filter by stakeholder tag (PATLIB, BUSINESS, UNIVERSITY)
4. Run a query, adjust parameters, download results
5. Use "Take to TIP" to export to Jupyter

### For Developers
1. Read [Project Overview](./project-overview.md) for architecture
2. Study [Query Design Patterns](./query-design-patterns.md) for SQL patterns
3. Review [What Worked Well](./what-worked-well.md) for design decisions
4. Check `tests/` for validation patterns

### For New Projects
1. Copy [Query Design Patterns](./query-design-patterns.md) for query structure
2. Apply lessons from [What Worked Well](./what-worked-well.md)
3. Use query-as-data pattern for rich metadata
4. Build TIP export from day one

---

## Contact

- **Author:** Arne Krueger
- **Email:** arne@mtc.berlin
- **GitHub:** [github.com/herrkrueger/patstat](https://github.com/herrkrueger/patstat)
- **Issues:** [github.com/herrkrueger/patstat/issues](https://github.com/herrkrueger/patstat/issues)
