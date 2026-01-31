---
status: in-progress
epic: 6
story: 2
name: refactor-monolithic-structure
---

# Story 6.2: Refactor Monolithic App Structure

**As a** developer,
**I want** to break down the 1,860 LOC `app.py` into modular components,
**So that** the codebase is maintainable, testable, and new features can be added safely.

## Acceptance Criteria

### 1. Module Structure Created
- **Given** the monolithic `app.py`
- **When** refactoring
- **Then** code is organized into these modules:

| Module | Purpose | Approximate LOC |
|--------|---------|-----------------|
| `modules/config.py` | Constants, configuration, reference data | ~120 |
| `modules/utils.py` | Pure helper functions (no UI, no state) | ~80 |
| `modules/data.py` | BigQuery client, query execution, data access | ~120 |
| `modules/logic.py` | Business logic, AI client, validation | ~200 |
| `modules/ui.py` | All Streamlit UI rendering functions | ~900 |
| `app.py` | Entry point, routing, page config | ~80 |

### 2. No Circular Dependencies
- **Given** the module structure
- **When** importing modules
- **Then** no circular import errors occur
- **And** dependency direction flows: `config` ← `utils` ← `data` ← `logic` ← `ui` ← `app`

### 3. All Tests Pass with Updated Imports
- **Given** the refactored modules
- **When** running `pytest tests/`
- **Then** all 89 existing tests pass
- **And** test imports use the new module paths

### 4. Application Runs Correctly
- **Given** the refactored app
- **When** running `streamlit run app.py`
- **Then** ALL features work exactly as before:
  - Landing page with search/filter
  - Detail page with parameters and execution
  - Contribution flow
  - AI Query Builder
  - TIP integration
  - Download/export

## Tasks/Subtasks

### Phase 1: Create Module Structure
- [x] Create `modules/` directory with `__init__.py`
- [x] Create `modules/config.py` with all constants (see Function Mapping below)
- [x] Create `modules/utils.py` with pure helper functions
- [x] Create `modules/data.py` with BigQuery functions
- [x] Create `modules/logic.py` with business logic
- [x] Create `modules/ui.py` with all render_* functions

### Phase 2: Update Imports in app.py
- [x] Replace inline code with imports from modules
- [x] Keep only `main()`, page config, and routing in app.py
- [x] Verify no circular imports (test with `python -c "import app"`)

### Phase 3: Update Test Imports
- [x] Update `tests/test_ai_builder.py` imports (see Test Migration Table)
- [x] Update `tests/test_ai_config.py` imports
- [x] Update `tests/test_contribution.py` imports
- [x] Update `tests/test_filter_queries.py` imports
- [x] Update `tests/test_query_metadata.py` imports
- [x] Run full test suite, fix any failures

### Phase 4: Verification
- [x] Run `pytest tests/ -v` - all 90 tests pass
- [ ] Run `streamlit run app.py` - manual smoke test
- [ ] Verify each major feature works (landing, detail, contribute, AI builder)

## Function-to-Module Mapping

### modules/config.py
```python
# Color palette
COLOR_PRIMARY, COLOR_SECONDARY, COLOR_ACCENT, COLOR_PALETTE

# Default parameter values
DEFAULT_YEAR_START, DEFAULT_YEAR_END, DEFAULT_JURISDICTIONS, DEFAULT_TECH_FIELD
YEAR_MIN, YEAR_MAX

# UI constants
CATEGORIES, STAKEHOLDER_TAGS, COMMON_QUESTIONS

# Reference data
JURISDICTIONS  # List of patent office codes
TECH_FIELDS    # Dict of WIPO technology fields

# External URLs
TIP_PLATFORM_URL, GITHUB_REPO_URL

# AI prompt
PATSTAT_SYSTEM_PROMPT
```

### modules/utils.py
```python
def format_time(seconds: float) -> str
def detect_sql_parameters(sql: str) -> list
def format_sql_for_tip(sql: str, params: dict) -> str
```

### modules/data.py
```python
def get_bigquery_client()
def run_query(client, query)
def run_parameterized_query(client, sql_template: str, params: dict)
def get_all_queries() -> dict
def resolve_options(options)
```

### modules/logic.py
```python
def filter_queries(queries, search_term, category, stakeholders) -> dict
def generate_insight_headline(df, query_info)
def validate_contribution_step1() -> list
def submit_contribution(contribution: dict) -> str
def get_claude_client()
def is_ai_available() -> bool
def generate_sql_query(user_request: str) -> dict
def parse_ai_response(response_text: str) -> dict
```

### modules/ui.py
```python
# Session state & navigation
def init_session_state()
def go_to_landing()
def go_to_detail(query_id: str)
def go_to_contribute()
def go_to_ai_builder()

# Rendering helpers
def render_tags_inline(tags: list) -> str
def render_parameter_block()
def render_single_parameter(name, config, key_prefix)
def render_query_parameters(query_id: str) -> tuple
def render_chart(df, query_info)
def render_metrics(df, query_info)
def get_contextual_spinner_message(query_info)

# Page rendering
def render_landing_page()
def render_query_list(search_term, category_filter, stakeholder_filter)
def render_detail_page(query_id: str)
def render_tip_panel(query_info, collected_params)
def render_footer()
def render_contribute_page()
def render_ai_builder_page()
```

### app.py (entry point)
```python
import streamlit as st
from modules.ui import (
    init_session_state, render_landing_page, render_detail_page,
    render_contribute_page, render_ai_builder_page, render_footer
)
from modules.data import get_bigquery_client

st.set_page_config(...)
st.title(...)
st.caption(...)

def main():
    init_session_state()
    client = get_bigquery_client()
    # ... routing logic (~30 lines)
    render_footer()

if __name__ == "__main__":
    main()
```

## Test Migration Table

| Test File | Current Imports | New Imports |
|-----------|-----------------|-------------|
| **test_ai_builder.py** | `from app import parse_ai_response, is_ai_available, PATSTAT_SYSTEM_PROMPT` | `from modules.logic import parse_ai_response, is_ai_available` + `from modules.config import PATSTAT_SYSTEM_PROMPT` |
| **test_ai_config.py** | TBD (read file) | TBD |
| **test_contribution.py** | `from app import validate_contribution_step1, detect_sql_parameters, submit_contribution, CATEGORIES, STAKEHOLDER_TAGS` | `from modules.logic import validate_contribution_step1, submit_contribution` + `from modules.utils import detect_sql_parameters` + `from modules.config import CATEGORIES, STAKEHOLDER_TAGS` |
| **test_filter_queries.py** | `from app import filter_queries, STAKEHOLDER_TAGS, CATEGORIES` | `from modules.logic import filter_queries` + `from modules.config import STAKEHOLDER_TAGS, CATEGORIES` |
| **test_query_metadata.py** | `from app import render_tags_inline, format_time` | `from modules.ui import render_tags_inline` + `from modules.utils import format_time` |

## Dev Notes

### Import Strategy
- Move functions one module at a time, starting with `config.py` (no dependencies)
- After each module, run `python -c "import app"` to check for import errors
- If circular import detected, move the problematic function to a different module

### Streamlit Session State
- `st.session_state` is accessed in `ui.py` functions - this is fine
- Functions in `logic.py` that need session state receive it as a parameter or access via `st.session_state` import

### Common Pitfalls
1. **Circular imports**: `ui.py` imports from `logic.py`, but `logic.py` must NOT import from `ui.py`
2. **Missing re-exports**: If tests import from `app`, we may need to re-export in `app.py` OR update all test imports
3. **Streamlit caching**: `@st.cache_resource` decorator on `get_bigquery_client()` - ensure it still works from module

### Verification Checklist
- [x] `python -c "from modules import config"` - no errors
- [x] `python -c "from modules import utils"` - no errors
- [x] `python -c "from modules import data"` - no errors
- [x] `python -c "from modules import logic"` - no errors
- [x] `python -c "from modules import ui"` - no errors
- [x] `python -c "import app"` - no errors
- [x] `pytest tests/ -v` - all tests pass (90 tests)
- [ ] `streamlit run app.py` - app loads and works

## Out of Scope
- Adding new tests (covered by 6.4)
- Changing any functionality
- Renaming functions
- Adding type hints (nice to have, but not required)

## File List
- app.py (modified - reduced to ~80 lines)
- modules/__init__.py (new)
- modules/config.py (new)
- modules/utils.py (new)
- modules/data.py (new)
- modules/logic.py (new)
- modules/ui.py (new)
- tests/test_ai_builder.py (modified - imports only)
- tests/test_ai_config.py (modified - imports only)
- tests/test_contribution.py (modified - imports only)
- tests/test_filter_queries.py (modified - imports only)
- tests/test_query_metadata.py (modified - imports only)

## Dev Agent Record

### Implementation Plan
- Phase 1: Create module structure (config → utils → data → logic → ui)
- Phase 2: Update app.py to use module imports
- Phase 3: Update test imports
- Phase 4: Verify all tests pass and app runs

### Completion Notes
- 2026-01-31: Phase 1 complete - all 6 modules created and verified with Python 3.13 venv
  - modules/__init__.py (re-exports all submodules)
  - modules/config.py (~120 LOC - constants, TECH_FIELDS, PATSTAT_SYSTEM_PROMPT)
  - modules/utils.py (~80 LOC - format_time, detect_sql_parameters, format_sql_for_tip)
  - modules/data.py (~140 LOC - BigQuery client, run_query, run_parameterized_query, get_all_queries)
  - modules/logic.py (~180 LOC - filter_queries, AI functions, validation)
  - modules/ui.py (~750 LOC - all render_* functions, navigation, session state)
- 2026-01-31: Phase 2 complete - app.py refactored to 67 LOC entry point
  - Replaced 1,860 LOC with imports from modules
  - No circular imports (all module imports verified)
- 2026-01-31: Phase 3 complete - all 5 test files updated
  - test_ai_builder.py: imports from modules.logic, modules.config
  - test_ai_config.py: imports from modules.logic
  - test_contribution.py: imports from modules.logic, modules.utils, modules.config
  - test_filter_queries.py: imports from modules.logic, modules.config
  - test_query_metadata.py: imports from modules.ui, modules.utils
  - Fixed monkeypatch targets for session_state mocking
- 2026-01-31: Phase 4 partial - 90 tests pass
  - Awaiting manual smoke test

## Change Log
- 2026-01-30: Story created
- 2026-01-31: Story RESET - previous "done" status was incorrect (work never performed)
- 2026-01-31: Story rewritten with detailed task breakdown, function mapping, and test migration plan
- 2026-01-31: Phase 1 complete - modules directory created with all 6 modules
- 2026-01-31: Phase 2 complete - app.py refactored to 67 LOC entry point
- 2026-01-31: Phase 3 complete - all test imports updated, 90 tests passing
