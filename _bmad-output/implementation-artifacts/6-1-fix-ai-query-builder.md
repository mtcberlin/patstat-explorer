---
status: ready-for-dev
epic: 6
story: 1
name: fix-ai-query-builder
---

# Story 6.1: Fix AI Query Builder & Dependencies

**As a** developer,
**I want** the AI Query Builder to work reliably in both local and cloud environments,
**So that** the core "AI" feature of the MVP is actually functional.

## Acceptance Criteria

### 1. Dependency Management
- **Given** `requirements.txt`
- **When** checked
- **Then** the `anthropic` library is explicitly listed with a version number

### 2. Environment Configuration
- **Given** the application startup
- **When** loading the `anthropic` API key
- **Then** the app checks `st.secrets` first (Cloud)
- **And** checks `os.environ` / `.env` second (Local)
- **And** if the key is missing from both, the app does NOT crash but shows a helpful warning in the UI

### 3. Functional Verification
- **Given** a valid API key
- **When** the user sends a natural language prompt
- **Then** the app successfully imports `anthropic` and calls the API
- **And** returns a valid SQL response

## Tasks/Subtasks

- [ ] Fix Dependency: Add `anthropic` to `requirements.txt`
- [ ] Fix Configuration: Update `app.py` to robustly load API key
- [ ] Fix Implementation: Ensure `anthropic` client initialization handles missing keys gracefully
- [ ] Verify: Test locally with `.env` (Manual check)

## Dev Notes

- `app.py` currently attempts to import `anthropic` at top level, which crashes if lib is missing.
- Need to use `python-dotenv` for local env loading (already in requirements).
- `st.secrets` is the Streamlit Cloud way.

## Dev Agent Record
### Implementation Plan
- [ ]

### Completion Notes
- [ ]

## File List
- requirements.txt
- app.py

## Change Log
- 2026-01-30: Story created

