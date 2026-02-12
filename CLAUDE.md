# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PATSTAT Explorer is a Streamlit web app that lets patent information professionals explore EPO PATSTAT data (450 GB, 27+ tables on BigQuery) through 47 pre-built parameterized queries, without writing SQL. It also supports AI-generated queries via Claude or AbraQ, and export to EPO's TIP platform as Jupyter notebooks.

**Live:** patstatexplorer.depa.tech | **License:** MIT

## Commands

```bash
# Run the app locally
streamlit run app.py

# Run all unit tests
pytest tests/ -v

# Run a single test file or class
pytest tests/test_filter_queries.py -v
pytest tests/test_filter_queries.py::TestFilterQueriesSearch -v

# Run integration test (requires BigQuery credentials)
python test_queries_bq.py

# Install dependencies
pip install -r requirements.txt
```

## Architecture

**Entry point:** `app.py` — Streamlit page config, session state init, page routing.

**Module layer (`modules/`):**

| Module | Responsibility |
|--------|---------------|
| `config.py` | Constants only: colors, year ranges, jurisdictions, WIPO fields, Claude system prompt. No imports from other modules. |
| `data.py` | BigQuery client creation (cached via `@st.cache_resource`), query execution (`run_query`, `run_parameterized_query`), query merging with user contributions. |
| `logic.py` | Business logic: query filtering, AI client initialization (Claude/AbraQ), SQL generation, AI response parsing, contribution validation. |
| `ui.py` | All Streamlit rendering: landing page, detail page, contribute page, AI builder page, footer. Session state management lives here. |
| `utils.py` | Pure functions: time formatting, SQL parameter detection, TIP SQL formatting. |
| `abra_q_client.py` | Alternative AI provider client with token management. |

**Import hierarchy:** `config` ← `utils` ← `data` ← `logic` ← `ui` ← `app`. No circular dependencies.

**Query definitions:** `queries_bq.py` (4,400 lines) — single `QUERIES` dict holding all 47 queries with metadata, SQL templates, parameter definitions, and visualization config. This is the single source of truth; the UI auto-generates controls from parameter definitions.

## Key Patterns

**Query-as-Data:** Each query in `QUERIES` is a dict with `title`, `tags`, `category`, `description`, `explanation`, `sql`, `sql_template`, `parameters`, `visualization`, `platforms`, and timing estimates. Adding a new query means adding a new entry to this dict.

**Parameter types:** `year_range` (dual slider → `@year_start`/`@year_end` as INT64), `multiselect` (dropdown → `@param` as `ARRAY<STRING>`, used with `IN UNNEST(@param)`), `select` (single dropdown → STRING), `text` (input → STRING).

**Session state routing:** Navigation is driven by `st.session_state['current_page']` with values `landing`, `detail`, `contribute`, `ai_builder`. The selected query ID is in `st.session_state['selected_query']`.

**AI provider pattern:** `QUERY_PROVIDER` env var selects `claude` or `abra-q`. Both providers are accessed through `generate_sql_query()` in `logic.py`.

**Platform field:** Queries have `platforms: ["bigquery", "tip"]` or `["bigquery"]` — controls whether "Take to TIP" export is offered.

## BigQuery Schema

The app queries EPO PATSTAT 2025 Autumn tables in `patstat-mtc.patstat`. Key tables: `tls201_appln` (applications), `tls206_person` (applicants/inventors), `tls207_pers_appln` (person-application links), `tls209_appln_ipc` (IPC classifications), `tls224_appln_cpc` (CPC classifications), `tls230_appln_techn_field` (WIPO fields), `tls211_pat_publn` (publications), `tls212_citation` (citations).

New classification hierarchy tables: `tls_ipc_hierarchy`, `tls_ipc_catchword`, `tls_ipc_concordance`, `tls_ipc_everused`, `tls_cpc_hierarchy`.

## Configuration

Local dev uses `.env` (see `.env.example`). Streamlit Cloud uses `st.secrets` (TOML format in dashboard). `data.py` checks both sources. Key vars: `BIGQUERY_PROJECT`, `BIGQUERY_DATASET`, `GOOGLE_APPLICATION_CREDENTIALS_JSON`, `ANTHROPIC_API_KEY`, `QUERY_PROVIDER`.

## Testing Notes

- Unit tests use simplified `SAMPLE_QUERIES` dicts, not the real query data (except metadata validation tests which import `QUERIES` directly).
- No database mocking — integration tests require real BigQuery credentials.
- Tests add the parent directory to `sys.path` for imports.
- Query metadata tests validate structural completeness of all 47 queries (required fields, valid categories, valid parameter types).

## Deployment

Self-hosted on Coolify (Hetzner) at `patstatexplorer.depa.tech`. Auto-deploys from `main` branch. The `develop` branch is used for active development. GCP service account credentials are mounted via `.streamlit/gcp-sa.json` in the Coolify deployment.
