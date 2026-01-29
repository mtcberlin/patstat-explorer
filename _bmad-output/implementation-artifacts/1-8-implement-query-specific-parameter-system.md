# Story 1.8: Implement Query-Specific Parameter System

Status: done

## Story

As a PATLIB professional,
I want each query to show only the parameters that affect its results,
so that I'm not confused by controls that don't do anything.

## Background & Context

**Why this story exists:** Story 1.7 implemented dynamic parameters with a generic "one-size-fits-all" approach. All queries received the same 3 parameters (`year_start`, `year_end`, `jurisdictions`) regardless of whether those parameters are meaningful for that specific query. This creates user confusion — parameters appear in the UI but don't logically connect to what the query does.

**Root cause:** Requirements misunderstanding — "dynamic" was interpreted as "uniform" instead of "query-specific."

**Reference:** See `_bmad-output/planning-artifacts/sprint-change-proposal-2026-01-29.md` for full analysis.

## Acceptance Criteria

1. **Given** the queries in queries_bq.py
   **When** I review the parameter definitions
   **Then** each query has a `parameters` dict defining its specific inputs
   **And** parameter types include: year_range, multiselect (jurisdiction, competitors, regions), select (tech_field), text (IPC class, applicant name)
   **And** sql_template uses only the parameters defined for that query

2. **Given** I select a query on the detail page
   **When** the parameter block renders
   **Then** only controls for that query's defined parameters are shown
   **And** controls appear in a logical order based on the query context
   **And** smart defaults are pre-filled based on query configuration

3. **Given** I select a query with NO parameters (e.g., Q05 Sample Patents)
   **When** the detail page loads
   **Then** only the "Run Analysis" button is shown
   **And** no parameter controls are displayed
   **And** explanatory text indicates "This query has no configurable parameters"

4. **Given** I run a query with my selected parameter values
   **When** the query executes
   **Then** my parameter values are correctly substituted into the SQL
   **And** results reflect my parameter choices
   **And** no regression in existing query functionality

5. **Given** all queries have been updated
   **When** I count queries by parameter configuration
   **Then** each query has an appropriate number of parameters (0-4 typically)
   **And** no query has parameters that don't affect its SQL

## Tasks / Subtasks

- [x] Task 1: Define parameter schema in queries_bq.py (AC: #1)
  - [x] Add module-level documentation for parameter schema
  - [x] Define parameter types: year_range, multiselect, select, text
  - [x] Define options references: "jurisdictions", "wipo_fields", custom arrays

- [x] Task 2: Add `parameters` dict to all queries (AC: #1, #5)
  - [x] Q01-Q05 (Overview): Analyze and add appropriate params
  - [x] Q06-Q07 (Strategic): Analyze and add appropriate params
  - [x] Q08-Q10 (Technology): Analyze and add appropriate params
  - [x] Q11-Q12 (Competitive): Analyze and add appropriate params
  - [x] Q13-Q14 (Citation): Analyze and add appropriate params
  - [x] Q15-Q17 (Regional): Analyze and add appropriate params
  - [x] Q18+ (Additional): Analyze and add appropriate params
  - [x] Mark queries with empty `parameters: {}` where no params needed

- [x] Task 3: Create dynamic parameter rendering function (AC: #2, #3)
  - [x] Create `render_query_parameters(query_id)` function in app.py
  - [x] Handle year_range type (slider)
  - [x] Handle multiselect type (st.multiselect)
  - [x] Handle select type (st.selectbox)
  - [x] Handle text type (st.text_input)
  - [x] Handle empty parameters case (no controls, just Run button)

- [x] Task 4: Update detail page to use dynamic rendering (AC: #2)
  - [x] Replace `render_parameter_block()` call with `render_query_parameters(query_id)`
  - [x] Ensure Run Analysis button always appears
  - [x] Update parameter collection to match rendered controls

- [x] Task 5: Update `run_parameterized_query()` to use query params (AC: #4)
  - [x] Read query's `parameters` config
  - [x] Only pass parameters that query defines
  - [x] Handle missing optional parameters gracefully

- [x] Task 6: Test all queries (AC: #4, #5)
  - [x] Verify each query renders correct parameter controls
  - [x] Verify each query executes with selected parameters
  - [x] Verify queries with no parameters work correctly
  - [x] Verify no regression in any existing functionality

## Dev Notes

### Parameter Schema

Add to each query in `queries_bq.py`:

```python
"parameters": {
    "param_name": {
        "type": "year_range" | "multiselect" | "select" | "text",
        "label": "Display Label",
        "options": [...] | "jurisdictions" | "wipo_fields",  # for select/multiselect
        "defaults": [...] | value,
        "default_start": int,  # for year_range only
        "default_end": int,    # for year_range only
        "required": True | False
    }
}
```

### Example Parameter Configurations

**Q01 (Database Statistics)** — Year filter only, optional:
```python
"parameters": {
    "year_range": {
        "type": "year_range",
        "label": "Filing Year Range",
        "default_start": 1980,
        "default_end": 2024,
        "required": False
    }
}
```

**Q03 (Applications by Year)** — Year + jurisdictions:
```python
"parameters": {
    "year_range": {
        "type": "year_range",
        "label": "Filing Year Range",
        "default_start": 1980,
        "default_end": 2024,
        "required": True
    },
    "jurisdictions": {
        "type": "multiselect",
        "label": "Patent Offices",
        "options": "jurisdictions",
        "defaults": ["EP", "US", "CN"],
        "required": True
    }
}
```

**Q05 (Sample Patents)** — No parameters:
```python
"parameters": {}
```

**Q12 (Competitor Filing Strategy)** — Query-specific options:
```python
"parameters": {
    "year_range": {
        "type": "year_range",
        "label": "Filing Year Range",
        "default_start": 2015,
        "default_end": 2024,
        "required": True
    },
    "jurisdictions": {
        "type": "multiselect",
        "label": "Patent Offices to Compare",
        "options": "jurisdictions",
        "defaults": ["EP", "US", "CN"],
        "required": True
    },
    "competitors": {
        "type": "multiselect",
        "label": "Competitors to Analyze",
        "options": ["Medtronic", "Johnson & Johnson", "Abbott", "Boston Scientific",
                   "Stryker", "Zimmer", "Smith & Nephew", "Edwards", "Baxter",
                   "Fresenius", "B. Braun"],
        "defaults": ["Medtronic", "Johnson & Johnson", "Abbott", "Boston Scientific"],
        "required": True
    }
}
```

### Dynamic Rendering Logic

In `app.py`, create:

```python
def render_query_parameters(query_id: str) -> dict:
    """Render parameter controls based on query's parameter configuration.

    Returns dict of parameter values collected from UI controls.
    """
    query = get_all_queries().get(query_id, {})
    params_config = query.get('parameters', {})

    if not params_config:
        st.info("This query has no configurable parameters.")
        return {}

    collected_params = {}

    with st.container(border=True):
        # Determine layout based on param count
        param_count = len(params_config)
        if param_count <= 2:
            cols = st.columns(param_count + 1)  # +1 for Run button
        else:
            cols = st.columns(4)  # Max 4 columns

        col_idx = 0
        for param_name, param_def in params_config.items():
            with cols[col_idx % len(cols)]:
                value = render_single_parameter(param_name, param_def)
                collected_params[param_name] = value
            col_idx += 1

    return collected_params


def render_single_parameter(name: str, config: dict):
    """Render a single parameter control based on its type."""
    param_type = config.get('type')
    label = config.get('label', name)

    if param_type == 'year_range':
        default_start = config.get('default_start', 2015)
        default_end = config.get('default_end', 2024)
        year_range = st.slider(label, 1990, 2024, (default_start, default_end))
        return {'year_start': year_range[0], 'year_end': year_range[1]}

    elif param_type == 'multiselect':
        options = resolve_options(config.get('options', []))
        defaults = config.get('defaults', [])
        return st.multiselect(label, options, default=defaults)

    elif param_type == 'select':
        options = resolve_options(config.get('options', []))
        default = config.get('defaults')
        return st.selectbox(label, options, index=options.index(default) if default in options else 0)

    elif param_type == 'text':
        default = config.get('defaults', '')
        placeholder = config.get('placeholder', '')
        return st.text_input(label, value=default, placeholder=placeholder)

    return None


def resolve_options(options):
    """Resolve option references to actual lists."""
    if options == 'jurisdictions':
        return JURISDICTIONS
    elif options == 'wipo_fields':
        return list(TECH_FIELDS.keys())
    elif isinstance(options, list):
        return options
    return []
```

### Query Analysis Guidelines

When adding `parameters` to each query, analyze the SQL to determine:

1. **What WHERE clauses exist?** Those indicate needed parameters
2. **What values are hardcoded?** Consider making them configurable
3. **What makes sense for the user?** Don't add params just because SQL could accept them

**Decision tree:**
- If query is "overall database stats" → minimal or no params
- If query filters by time → add year_range
- If query filters by geography → add jurisdictions
- If query is about specific entities (competitors, regions) → add entity-specific params
- If query has no meaningful filters → `parameters: {}`

### Project Structure Notes

- **queries_bq.py**: Add `parameters` dict to each query entry (lines vary by query)
- **app.py**:
  - Current `render_parameter_block()` at ~line 274 — will be replaced/modified
  - Current `run_parameterized_query()` at ~line 627 — update to use query's params
  - Detail page rendering at ~line 400+ — update to use new param rendering

### Testing Strategy

For each query:
1. Verify correct parameter controls appear
2. Verify Run Analysis button appears
3. Change parameter values and verify SQL uses them
4. Verify results change when parameters change
5. For no-param queries: verify clean UI with just Run button

### Avoid These Mistakes

- **DO NOT** add parameters to queries where they don't affect results
- **DO NOT** change the sql_template SQL — only add `parameters` metadata
- **DO NOT** break existing query execution — this is additive
- **DO NOT** use hardcoded column layouts — adapt to param count
- **DO** preserve existing default values where they make sense
- **DO** handle edge case of empty parameters gracefully

### References

- [Source: sprint-change-proposal-2026-01-29.md] Full change proposal with schema
- [Source: queries_bq.py] Current query definitions with sql_template
- [Source: app.py:274-330] Current render_parameter_block() function
- [Source: app.py:627-680] Current run_parameterized_query() function
- [Source: PRD FR11-FR15] Dynamic parameter requirements
- [Source: Story 1.7] Previous implementation of generic parameters

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5

### Debug Log References

- All 78 existing tests pass after implementation

### Completion Notes List

- Task 1: Parameter schema was already documented at top of queries_bq.py (lines 1-39)
- Task 2: Added `parameters` dict to all 42 queries (Q01-Q42); Q05 has empty `{}` as it has no configurable params
- Task 3: Created `resolve_options()`, `render_single_parameter()`, and `render_query_parameters()` functions in app.py
- Task 4: Updated `render_detail_page()` to use new `render_query_parameters(query_id)` function
- Task 5: Query-specific parameter passing implemented in detail page - only passes params defined for each query

### File List

- queries_bq.py - Added `parameters` dict to Q08-Q42 (Q01-Q07 already had them)
- app.py - Added `resolve_options()`, `render_single_parameter()`, `render_query_parameters()` functions; updated `render_detail_page()` to use query-specific parameters; added `YEAR_MIN`/`YEAR_MAX` constants; added unknown param type warning
- tests/test_query_metadata.py - Added 8 new tests for Story 1.8 parameter system validation
- _bmad-output/implementation-artifacts/sprint-status.yaml - Updated story status

### Senior Developer Review (AI)

**Reviewed:** 2026-01-29
**Reviewer:** Amelia (Dev Agent)
**Outcome:** APPROVED with minor fixes applied

**Fixes Applied:**
1. Added warning for unknown parameter types in `render_single_parameter()` (was silently returning None)
2. Added `YEAR_MIN`/`YEAR_MAX` constants to replace hardcoded values in sliders
3. Updated File List to include sprint-status.yaml

**AC Verification:**
- AC #1: ✓ All 42 queries have `parameters` dict with valid types
- AC #2: ✓ `render_query_parameters()` renders only query-relevant controls
- AC #3: ✓ Q05 has empty `{}` and shows "no configurable parameters"
- AC #4: ✓ Parameters correctly substituted in SQL execution
- AC #5: ✓ Each query has 0-4 parameters as appropriate

