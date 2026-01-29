# Sprint Change Proposal: Query-Specific Parameter System

**Project:** PATSTAT Explorer
**Date:** 2026-01-29
**Author:** Arne (via BMad Correct Course Workflow)
**Status:** Pending Approval

---

## 1. Issue Summary

### Problem Statement

The query dynamisation system was implemented with a generic "one-size-fits-all" approach. Three fixed parameters (`year_start`, `year_end`, `jurisdictions`) are applied uniformly to ALL queries via `sql_template`, regardless of whether those parameters are meaningful for that specific query.

**The core flaw:** Parameters exist in the UI but **do not logically connect** to what each query actually does. Users can change values, but for many queries, this has no meaningful effect or creates confusion.

### Discovery Context

- **When discovered:** After completing Story 1.7 (Convert All Static Queries to Dynamic)
- **How discovered:** Manual review of implemented functionality revealed the disconnect
- **Evidence:**
  - Q01 (Database Statistics) has jurisdiction filtering, but the question asks about "overall" database stats
  - Q15-Q17 (German States) have hardcoded regional filters plus generic jurisdiction params
  - All 40+ queries share identical parameter controls regardless of query purpose

### Issue Type

**Misunderstanding of original requirements** — The implementation satisfied the letter of FR11-FR15 (dynamic parameters) but missed the intent that parameters should be meaningful and query-specific.

---

## 2. Impact Analysis

### Epic Impact

| Epic | Status | Impact Level | Description |
|------|--------|--------------|-------------|
| **Epic 1** | In Progress | **HIGH** | Story 1.7 acceptance criteria need revision; new Story 1.8 required |
| **Epic 2** | Done | LOW | Queries added may have inherited flawed pattern; review recommended |
| **Epic 3** | In Progress | **MEDIUM** | Story 3.2 (Parameter Definition) depends on query-specific param system |
| **Epic 4** | In Progress | NONE | AI Query Builder generates SQL dynamically — unaffected |
| **Epic 5** | In Progress | NONE | Training integration unaffected |

### Story Impact

| Story | Current Status | Required Action |
|-------|----------------|-----------------|
| **1.7** | Done | Update acceptance criteria to reflect query-specific intent |
| **1.8 (NEW)** | — | Create new story for parameter remediation implementation |
| **3.2** | Done | May need revision after 1.8 is complete |

### Artifact Conflicts

| Artifact | Conflict Level | Required Updates |
|----------|----------------|------------------|
| **PRD** | LOW | Clarify FR11-FR15 to specify query-specific parameters |
| **Architecture** | MEDIUM | Query data structure needs `parameters` dict per query |
| **UX Specification** | LOW | Parameter block spec needs to acknowledge adaptive layout |
| **queries_bq.py** | HIGH | Add `parameters` configuration to each of ~40 queries |
| **app.py (Frontend)** | MEDIUM | Render controls based on query's parameter config |

### Technical Impact

- **Code changes:** `queries_bq.py` (data structure) + `app.py` (rendering logic)
- **No database changes** — purely configuration and frontend
- **No API changes** — internal application logic only
- **Backward compatible** — existing queries continue to work; we're adding metadata

---

## 3. Recommended Approach

### Selected Path: Direct Adjustment

**Why this approach:**

1. **Infrastructure exists** — The parameterized query system is built and functional
2. **Configuration-centric** — Primary work is defining per-query parameters, not rebuilding
3. **Low risk** — Queries execute correctly today; we're making the UI smarter
4. **No rollback needed** — Current code is a valid foundation to build upon

### Alternatives Considered

| Option | Verdict | Reasoning |
|--------|---------|-----------|
| **Rollback** | Rejected | Unnecessary — current implementation is functional foundation |
| **MVP Reduction** | Rejected | This is refinement, not scope reduction |
| **Hybrid** | Not needed | Direct adjustment is sufficient |

### Effort Estimate

| Component | Effort | Notes |
|-----------|--------|-------|
| Query configuration (~40 queries) | **Medium** | Analyze each query, define meaningful parameters |
| Frontend parameter rendering | **Medium** | Read query config, render appropriate controls |
| Documentation updates | **Low** | PRD, Epics, UX spec — minor clarifications |
| Testing | **Low** | Verify parameter controls match query behavior |
| **Total** | **Medium** | Estimated 1-2 focused sessions |

### Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Parameter config becomes complex | Low | Keep schema simple; most queries need 1-3 params |
| Frontend rendering edge cases | Low | Handle empty params, single param, multiple params |
| Regression in existing queries | Low | Queries still work; we're adding config layer |

---

## 4. Detailed Change Proposals

### 4.1 Query Configuration (`queries_bq.py`)

**Change:** Add `parameters` dict to each query defining its specific inputs.

**Schema:**
```python
"parameters": {
    "param_name": {
        "type": "year_range" | "multiselect" | "select" | "text",
        "label": "Display Label",
        "options": [...] | "jurisdictions" | "wipo_fields",  # for select/multiselect
        "defaults": [...] | value,
        "required": True | False
    }
}
```

**Examples:**

**Q01 (Database Statistics)** — Optional year filter only:
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

**Q12 (Competitor Filing Strategy)** — Competitors and offices:
```python
"parameters": {
    "year_range": {"type": "year_range", "default_start": 2015, "default_end": 2024, "required": True},
    "filing_offices": {"type": "multiselect", "options": "jurisdictions", "defaults": ["EP", "US", "CN"]},
    "competitors": {"type": "multiselect", "options": ["Medtronic", "J&J", "Abbott", ...], "defaults": [...]}
}
```

**Q05 (Sample Patents)** — No parameters:
```python
"parameters": {}
```

### 4.2 PRD Updates

**Section:** Functional Requirements - Dynamic Parameters

**Change:** Clarify that parameters are query-specific:

> **FR11:** Users can adjust parameters relevant to the selected query. Each query defines which parameters it accepts.
>
> **FR15a (NEW):** Frontend dynamically renders only the parameter controls relevant to the selected query based on its parameter configuration.

### 4.3 Epic & Story Updates

**Story 1.7:** Update acceptance criteria to reflect query-specific intent:
- Each query defines its own `parameters` dict
- Parameters are query-specific (not uniform across all queries)
- Queries without meaningful parameters have `parameters: {}`

**Story 1.8 (NEW):** Implement Query-Specific Parameter System
- Add `parameters` config to all queries
- Frontend reads config and renders appropriate controls
- Smart defaults from query configuration

### 4.4 UX Specification Updates

**Parameter Block:**
- Change from "fixed Time → Geography → Topic → Action" layout
- To "query-adaptive layout showing only relevant controls"
- Handle 0 params, 1-2 params (single row), 3+ params (multi-row)

### 4.5 Sprint Status Updates

```yaml
# Epic 1: UI Transformation & Dynamic Queries
epic-1: in-progress
1-7-convert-all-static-queries-to-dynamic: done
1-8-implement-query-specific-parameter-system: backlog  # NEW
```

---

## 5. Implementation Handoff

### Change Scope Classification

**MINOR** — Can be implemented directly by development team.

**Rationale:**
- No strategic pivot or business model change
- No new epics or major scope additions
- Contained to specific code files and documentation
- Clear acceptance criteria defined

### Handoff Recipients

| Role | Responsibility |
|------|----------------|
| **Developer (Arne)** | Implement parameter config in queries_bq.py, update app.py rendering logic |
| **SM/PM** | Update sprint-status.yaml, track Story 1.8 |

### Implementation Sequence

1. **Update queries_bq.py** — Add `parameters` dict to each query (can be done incrementally)
2. **Update app.py** — Modify parameter block rendering to read query config
3. **Test** — Verify each query shows correct controls and executes properly
4. **Update documentation** — PRD, Epics, UX spec (minor clarifications)
5. **Mark Story 1.8 done** — Update sprint-status.yaml

### Success Criteria

- [ ] Each query in queries_bq.py has a `parameters` dict (even if empty)
- [ ] Frontend renders only controls defined in query's parameters
- [ ] Parameter values correctly substitute into SQL and affect results
- [ ] Queries with no parameters show only "Run Analysis" button
- [ ] All existing queries continue to execute without regression

---

## 6. Approval

**Proposed by:** BMad Master (Correct Course Workflow)
**Date:** 2026-01-29

**Decision:** [ ] Approved / [ ] Approved with modifications / [ ] Rejected

**Approver:** _________________ **Date:** _________________

**Notes/Conditions:**

---

*Generated by BMad Correct Course Workflow*
