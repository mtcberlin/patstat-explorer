---
stepsCompleted: [1, 2, 3, 4]
status: complete
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
date: 2026-01-28
author: Arne
project: patstat
---

# PATSTAT Explorer - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for PATSTAT Explorer, decomposing the requirements from the PRD and UX Design into implementable stories.

## Requirements Inventory

### Functional Requirements

**Query Library & Discovery**
- FR1: Users can browse all available queries in a categorized library
- FR2: Users can filter queries by stakeholder type (PATLIB, BUSINESS, UNIVERSITY)
- FR3: Users can view query descriptions explaining what each query reveals
- FR4: Users can see estimated execution time for each query
- FR5: Users can search queries by keyword or topic

**Query Execution & Results**
- FR6: Users can execute any query from the library
- FR7: Users can view query results in tabular format
- FR8: System displays execution status and timing information
- FR9: Users can re-run queries with modified parameters without page refresh
- FR10: System caches query results for faster repeated access

**Dynamic Parameters**
- FR11: Users can adjust jurisdiction parameters (country/patent office selection)
- FR12: Users can adjust year range parameters via slider or input
- FR13: Users can select technology field from WIPO classification list
- FR14: Users can select multiple values for multi-select parameters
- FR15: System validates parameter inputs before query execution

**Data Visualization & Export**
- FR16: Users can view query results as interactive charts
- FR17: Users can switch between chart types where applicable (line, bar, etc.)
- FR18: Charts display with colors distinguishing multiple data series
- FR19: Users can export charts as images for presentations
- FR20: Users can download result data as CSV

**Query Transparency**
- FR21: Users can view the SQL query before execution
- FR22: Users can view the SQL with parameter values substituted
- FR23: Users can copy SQL to clipboard for use elsewhere
- FR24: Each query displays explanation of data sources and methodology

**Query Contribution**
- FR25: Users can submit new queries to the library
- FR26: Users can provide metadata for contributed queries (title, description, tags)
- FR27: Users can define dynamic parameters for contributed queries
- FR28: Users can preview how their contributed query will appear
- FR29: System validates contributed query SQL syntax before acceptance

**AI Query Building**
- FR30: Users can describe desired analysis in natural language
- FR31: System generates SQL query from natural language description
- FR32: System explains generated query in plain language
- FR33: Users can preview AI-generated query results before full execution
- FR34: Users can refine natural language input and regenerate query
- FR35: Users can save AI-generated queries to favorites

**Training Integration**
- FR36: Users can access "Take to TIP" pathway for any query
- FR37: System provides instructions for using queries in TIP/Jupyter
- FR38: Users can access GitHub repository with query documentation
- FR39: Queries execute fast enough for live training demonstrations (<15s)

### NonFunctional Requirements

**Performance**
- NFR1: Query execution <15 seconds for uncached queries
- NFR2: Cached queries <3 seconds
- NFR3: Page load <5 seconds initial load
- NFR4: Chart rendering <2 seconds after data load

**Integration**
- NFR5: Google BigQuery authenticated via service account
- NFR6: MCP/Claude API key authentication for AI query building
- NFR7: GitHub public repository access for "Take to TIP" pathway

**Operational**
- NFR8: Hosting on Streamlit Cloud free tier
- NFR9: Auto-deploy on git push
- NFR10: Streamlit Cloud built-in analytics for monitoring

### Additional Requirements

**From UX Design Specification:**
- UX1: Landing + Detail two-phase experience (Direction B)
- UX2: Question-based navigation organized by client question types
- UX3: Insight headlines appear first, before data tables
- UX4: Metric cards with delta indicators for KPIs
- UX5: Bordered containers (`st.container(border=True)`) for visual grouping
- UX6: Wide layout (`layout="wide"`) for data-rich pages
- UX7: Contextual loading messages (not generic spinners)
- UX8: Progressive disclosure via expanders for SQL, data tables
- UX9: Altair charts for export-ready visualizations
- UX10: Color palette: Primary #1E3A5F, Secondary #0A9396, Accent #FFB703
- UX11: Parameter order: Time → Geography → Technology → Action
- UX12: "Download for presentation" and "Download data" export options

**From Technical Requirements:**
- TECH1: Streamlit framework (existing)
- TECH2: Session-based state management (no user accounts)
- TECH3: Desktop-first, modern browsers only

### FR Coverage Map

| FR | Epic | Description |
|----|------|-------------|
| FR1 | Epic 2 | Browse queries in categorized library |
| FR2 | Epic 2 | Filter by stakeholder type |
| FR3 | Epic 2 | View query descriptions |
| FR4 | Epic 2 | See estimated execution time |
| FR5 | Epic 2 | Search queries by keyword |
| FR6 | Epic 1 | Execute any query |
| FR7 | Epic 1 | View results in tabular format |
| FR8 | Epic 1 | Display execution status and timing |
| FR9 | Epic 1 | Re-run with modified parameters |
| FR10 | Epic 1 | Cache query results |
| FR11 | Epic 1 | Adjust jurisdiction parameters |
| FR12 | Epic 1 | Adjust year range via slider |
| FR13 | Epic 1 | Select technology field |
| FR14 | Epic 1 | Multi-select parameters |
| FR15 | Epic 1 | Validate parameter inputs |
| FR16 | Epic 1 | View results as interactive charts |
| FR17 | Epic 1 | Switch between chart types |
| FR18 | Epic 1 | Color-coded multi-series charts |
| FR19 | Epic 1 | Export charts as images |
| FR20 | Epic 1 | Download data as CSV |
| FR21 | Epic 1 | View SQL before execution |
| FR22 | Epic 1 | View SQL with substituted values |
| FR23 | Epic 1 | Copy SQL to clipboard |
| FR24 | Epic 1 | Query methodology explanation |
| FR25 | Epic 3 | Submit new queries |
| FR26 | Epic 3 | Provide query metadata |
| FR27 | Epic 3 | Define dynamic parameters |
| FR28 | Epic 3 | Preview contributed query |
| FR29 | Epic 3 | Validate SQL syntax |
| FR30 | Epic 4 | Natural language input |
| FR31 | Epic 4 | AI-generated SQL |
| FR32 | Epic 4 | Plain language explanation |
| FR33 | Epic 4 | Preview AI query results |
| FR34 | Epic 4 | Refine and regenerate |
| FR35 | Epic 4 | Save to favorites |
| FR36 | Epic 5 | "Take to TIP" pathway |
| FR37 | Epic 5 | TIP/Jupyter instructions |
| FR38 | Epic 5 | GitHub repository access |
| FR39 | Epic 1 | Fast execution for demos |

## Epic List

### Epic 1: UI Transformation & Dynamic Queries

**Goal:** Maria can run any query with customizable parameters and get presentation-ready results with insight headlines.

**User Value:** Transform the app from a functional tool into a polished, question-answering machine that makes Maria look like a data expert to her clients.

**What this delivers:**
- New UX design (landing + detail pages, question-based navigation)
- All 18 static queries converted to dynamic with consistent parameters
- Insight headlines appear before data
- Beautiful Altair charts with export functionality
- SQL preview and transparency features
- Performance optimization for training demos

**FRs Covered:** FR6-FR24, FR39 (20 FRs)
**UX Covered:** UX1-UX12 (all UX requirements)
**NFRs Covered:** NFR1-4 (performance)

---

### Epic 2: Query Library Expansion

**Goal:** Users can browse 40+ queries organized by question type and find exactly what they need.

**User Value:** Triple the query library with EPO-validated content, making the tool comprehensive enough for most client questions.

**What this delivers:**
- Add ~21 queries extracted from EPO training PDFs
- Search functionality by keyword
- Filter by stakeholder type (PATLIB, BUSINESS, UNIVERSITY)
- Query descriptions and estimated execution times
- Question-based organization per UX design

**FRs Covered:** FR1-FR5 (5 FRs)

---

### Epic 3: Query Contribution System

**Goal:** Klaus can submit his queries to share with 300 PATLIB centres.

**User Value:** Transform power users from consumers to contributors, creating a community-driven query library.

**What this delivers:**
- Query submission interface
- Metadata input (title, description, tags)
- Parameter definition for dynamic queries
- Preview before submission
- SQL syntax validation

**FRs Covered:** FR25-FR29 (5 FRs)

---

### Epic 4: AI Query Builder

**Goal:** Maria can describe what she needs in plain English and get a working query.

**User Value:** Enable custom analysis without coding, handling client questions that don't match existing queries.

**What this delivers:**
- Natural language input interface
- AI-generated SQL via MCP/Claude
- Plain language explanation of what the query does
- Preview and refinement workflow
- Save successful queries to favorites

**FRs Covered:** FR30-FR35 (6 FRs)
**NFRs Covered:** NFR6 (MCP/Claude API integration)

---

### Epic 5: Training & TIP Integration

**Goal:** Elena can demo effectively and students have a clear path to TIP.

**User Value:** Make PATSTAT Explorer the perfect gateway to EPO's TIP platform, driving adoption through accessible demos.

**What this delivers:**
- Enhanced "Take to TIP" button with clear instructions
- TIP/Jupyter notebook export guidance
- GitHub repository access for query documentation
- Training demo optimizations

**FRs Covered:** FR36-FR38 (3 FRs)
**NFRs Covered:** NFR7 (GitHub integration)

---

## Epic 1: UI Transformation & Dynamic Queries

**Goal:** Maria can run any query with customizable parameters and get presentation-ready results with insight headlines.

### Story 1.1: Landing Page with Question-Based Navigation

As a PATLIB professional,
I want to see queries organized by the type of question I'm trying to answer,
So that I can quickly find the right analysis without learning technical query names.

**Acceptance Criteria:**

**Given** a user opens PATSTAT Explorer
**When** the application loads
**Then** they see a landing page with the title "What do you want to know?"
**And** category pills are displayed: Competitors, Trends, Regional, Technology
**And** clicking a category pill filters the query list to that category
**And** a "Common Questions" section shows 3-5 popular queries
**And** session state tracks the current page (landing vs detail)

**Given** a user clicks on a query from the landing page
**When** they select any query
**Then** they navigate to the detail page for that query
**And** the "← Back to Questions" button is visible

---

### Story 1.2: Detail Page Layout & Parameter Block

As a PATLIB professional,
I want consistent parameter controls on every query,
So that I can adjust jurisdiction, year range, and technology without learning new interfaces.

**Acceptance Criteria:**

**Given** a user is on a query detail page
**When** the page loads
**Then** a bordered parameter container is displayed at the top
**And** parameters appear in order: Time → Geography → Technology → Action
**And** year range uses a slider with sensible defaults (e.g., 2015-2024)
**And** jurisdiction uses multiselect with defaults (e.g., EP, US, CN)
**And** technology field uses selectbox grouped by sector
**And** "Run Analysis" button is styled as primary (type="primary")

**Given** a user clicks "← Back to Questions"
**When** navigation occurs
**Then** they return to the landing page
**And** any unsaved parameter changes are discarded

---

### Story 1.3: Query Execution & Results Display

As a PATLIB professional,
I want to run queries and see results clearly,
So that I can answer my client's question quickly.

**Acceptance Criteria:**

**Given** a user has set parameters and clicks "Run Analysis"
**When** the query executes
**Then** a spinner displays with contextual message (e.g., "Finding top filers in MedTech...")
**And** execution completes within 15 seconds for uncached queries
**And** execution timing is displayed (e.g., "Completed in 8.2 seconds")

**Given** a query returns results
**When** results are displayed
**Then** results appear in wide layout below the parameter block
**And** a data table is available in an expander ("▸ View Data Table")
**And** results are cached for faster repeat access (<3 seconds)

**Given** a query returns no data
**When** the empty state displays
**Then** a warning message appears with helpful suggestions
**And** suggestions include "Try broadening the year range" or similar

---

### Story 1.4: Insight Headlines & Altair Visualization

As a PATLIB professional,
I want to see the key finding immediately with a beautiful chart,
So that I understand the answer at a glance and can impress my client.

**Acceptance Criteria:**

**Given** a query returns results
**When** the results display
**Then** an insight headline appears first, in bold (e.g., "**Medtronic leads with 2,340 patents (23% share)**")
**And** the headline is a complete sentence answering the query's question
**And** the headline appears above any chart or data

**Given** results include visualization
**When** the chart renders
**Then** Altair chart displays with consistent color palette (Primary #1E3A5F, Secondary #0A9396, etc.)
**And** chart renders within 2 seconds after data load
**And** multi-series data uses distinct colors per series
**And** chart includes proper axis labels and legend
**And** tooltips show context, not just raw values

**Given** results include KPI-style metrics
**When** metrics display
**Then** metric cards show values with delta indicators where applicable
**And** positive deltas show green, negative show red

---

### Story 1.5: Export & Download Functionality

As a PATLIB professional,
I want to export charts and data for my client,
So that I can deliver professional results without editing.

**Acceptance Criteria:**

**Given** a query has returned results with a chart
**When** user clicks "Download Chart"
**Then** the chart exports as PNG image
**And** the exported image is presentation-ready (proper sizing, readable labels)
**And** the download initiates immediately

**Given** a query has returned results with data
**When** user clicks "Download Data"
**Then** the data exports as CSV file
**And** CSV includes all columns from the result set
**And** CSV uses appropriate formatting for dates and numbers

---

### Story 1.6: SQL Transparency Features

As a data-savvy PATLIB professional (Klaus),
I want to see the SQL query behind the analysis,
So that I can learn, verify, or adapt the query for my own use.

**Acceptance Criteria:**

**Given** a query detail page is displayed
**When** user expands "▸ View SQL"
**Then** the SQL query is displayed in a code block
**And** parameter values are substituted into the SQL (not placeholders)
**And** SQL is formatted for readability

**Given** the SQL is displayed
**When** user clicks "Copy to Clipboard"
**Then** the SQL is copied to clipboard
**And** a success message confirms the copy

**Given** any query is selected
**When** methodology information is needed
**Then** each query displays a brief explanation of data sources
**And** explanation clarifies what the query measures and any limitations

---

### Story 1.7: Convert All Static Queries to Dynamic

As a PATLIB professional,
I want all 18 existing queries to work with the new parameter system,
So that I have consistent experience across the entire query library.

**Acceptance Criteria:**

**Given** the existing 18 static queries in queries_bq.py
**When** conversion is complete
**Then** all 18 queries use the new parameter pattern (jurisdictions, year_start, year_end, tech_field)
**And** each query has appropriate default values
**And** each query has a question-based title and description
**And** each query is assigned to a category (Competitors, Trends, Regional, Technology)

**Given** any converted query is executed
**When** run with various parameter combinations
**Then** query executes successfully within 15 seconds
**And** results display correctly with insight headline and chart
**And** export functions work correctly

**Given** the Interactive Analysis tab (DQ01)
**When** reviewed after conversion
**Then** it continues to work with the new UI patterns
**And** multi-jurisdiction comparison is preserved

---

## Epic 2: Query Library Expansion

**Goal:** Users can browse 40+ queries organized by question type and find exactly what they need.

### Story 2.1: Query Search and Filter

As a PATLIB professional,
I want to search and filter the query library,
So that I can quickly find the right analysis even with 40+ queries.

**Acceptance Criteria:**

**Given** a user is on the landing page
**When** they type in the search box
**Then** queries are filtered by keyword match in title or description
**And** search is case-insensitive
**And** results update as user types (debounced)

**Given** a user wants to filter by stakeholder type
**When** they select a stakeholder filter (PATLIB, BUSINESS, UNIVERSITY)
**Then** only queries tagged with that stakeholder type are shown
**And** filters can be combined with search

---

### Story 2.2: Query Metadata Display

As a PATLIB professional,
I want to see clear information about each query before running it,
So that I can choose the right analysis for my client's question.

**Acceptance Criteria:**

**Given** a query is displayed in the library
**When** the user views the query card
**Then** the query title is displayed as a question (e.g., "Who are the top filers in my field?")
**And** a brief description explains what the query reveals
**And** estimated execution time is shown (e.g., "~8 seconds")
**And** stakeholder tags are visible (PATLIB, BUSINESS, UNIVERSITY)

---

### Story 2.3: Extract and Add EPO Training Queries (Batch 1)

As a PATLIB professional,
I want access to more validated queries from EPO training materials,
So that I can answer a wider range of client questions.

**Acceptance Criteria:**

**Given** the EPO training PDFs in context/epo_patstat_training/
**When** queries are extracted and added
**Then** at least 10 new queries are added to the library
**And** each query has question-based title and description
**And** each query is categorized appropriately
**And** each query uses the standard parameter pattern
**And** each query executes successfully within 15 seconds

---

### Story 2.4: Extract and Add EPO Training Queries (Batch 2)

As a PATLIB professional,
I want the full set of ~21 additional queries from EPO training,
So that the query library reaches the MVP target of 40+ queries.

**Acceptance Criteria:**

**Given** the remaining EPO training queries not yet added
**When** extraction is complete
**Then** at least 11 more queries are added (total ~40)
**And** all queries follow the established patterns
**And** query library total reaches 40+ queries
**And** all categories have meaningful content

---

## Epic 3: Query Contribution System

**Goal:** Klaus can submit his queries to share with 300 PATLIB centres.

### Story 3.1: Query Submission Interface

As a data-savvy PATLIB professional (Klaus),
I want to submit my own SQL queries to the library,
So that I can share my expertise with 300 PATLIB centres.

**Acceptance Criteria:**

**Given** a user navigates to "Contribute Query" section
**When** the contribution form loads
**Then** a text area is available for SQL query input
**And** fields are provided for: title, description, tags
**And** the interface explains the contribution process

**Given** a user enters a SQL query
**When** they fill in the metadata
**Then** title field accepts question-style input
**And** description field accepts detailed explanation
**And** tags can be selected from existing categories (multi-select)

---

### Story 3.2: Dynamic Parameter Definition

As a data-savvy PATLIB professional (Klaus),
I want to define which parts of my query should be dynamic parameters,
So that other users can customize the query for their context.

**Acceptance Criteria:**

**Given** a user is submitting a query
**When** they define parameters
**Then** they can specify parameter name, type (text, number, select, multiselect)
**And** they can provide default values
**And** they can mark parameters as required or optional
**And** parameter placeholders in SQL use @parameter_name syntax

---

### Story 3.3: Query Preview and Validation

As a data-savvy PATLIB professional (Klaus),
I want to preview how my query will appear before submitting,
So that I can verify it looks correct for other users.

**Acceptance Criteria:**

**Given** a user has entered query and metadata
**When** they click "Preview"
**Then** they see exactly how the query will appear in the library
**And** they see how parameters will render as controls
**And** they can test the query with sample parameters

**Given** a user submits a query
**When** validation runs
**Then** SQL syntax is validated against BigQuery
**And** required fields are checked for completeness
**And** clear error messages explain any issues

---

### Story 3.4: Query Submission and Confirmation

As a data-savvy PATLIB professional (Klaus),
I want confirmation when my query is successfully added,
So that I know my contribution is available for others.

**Acceptance Criteria:**

**Given** a user has a valid query ready to submit
**When** they click "Submit Query"
**Then** the query is added to the library
**And** a confirmation message appears: "Thank you for your contribution!"
**And** a link to the new query is provided
**And** the user can share the link with colleagues

---

## Epic 4: AI Query Builder

**Goal:** Maria can describe what she needs in plain English and get a working query.

### Story 4.1: Natural Language Input Interface

As a PATLIB professional,
I want to describe my analysis need in plain English,
So that I can get custom queries without knowing SQL.

**Acceptance Criteria:**

**Given** a user navigates to "AI Query Builder"
**When** the interface loads
**Then** a text area is available for natural language input
**And** placeholder text provides an example (e.g., "Show me the top 10 companies in Germany with wind energy patents...")
**And** helpful prompts suggest what information to include

**Given** a user enters a natural language request
**When** they click "Generate Query"
**Then** a loading state indicates AI is processing
**And** the request is sent to MCP/Claude API

---

### Story 4.2: AI-Generated SQL with Explanation

As a PATLIB professional,
I want to see the generated SQL with a plain-language explanation,
So that I understand what the query does even without SQL knowledge.

**Acceptance Criteria:**

**Given** the AI has generated a SQL query
**When** the results display
**Then** the generated SQL is shown in a code block
**And** a plain-language explanation appears above the SQL
**And** the explanation describes: what data is queried, how it's filtered, what the output means

**Given** the AI cannot generate a valid query
**When** the error state displays
**Then** a helpful message explains why (e.g., "I couldn't understand the technology field. Did you mean...")
**And** suggestions are provided to refine the request

---

### Story 4.3: Query Preview and Refinement

As a PATLIB professional,
I want to preview AI-generated query results and refine if needed,
So that I can ensure the query answers my actual question.

**Acceptance Criteria:**

**Given** an AI-generated SQL query is displayed
**When** user clicks "Preview Results"
**Then** the query executes with a sample/limited result set
**And** results display using the same patterns as regular queries
**And** user can verify the output matches their intent

**Given** the results don't match expectations
**When** user wants to refine
**Then** they can modify their natural language input
**And** click "Regenerate Query" to get an updated SQL
**And** previous versions are not lost (can toggle back)

---

### Story 4.4: Save AI Query to Favorites

As a PATLIB professional,
I want to save successful AI-generated queries,
So that I can reuse them without regenerating.

**Acceptance Criteria:**

**Given** an AI-generated query produces good results
**When** user clicks "Save to Favorites"
**Then** the query is saved with a user-provided name
**And** saved queries appear in a "My Queries" section
**And** saved queries can be run like any library query
**And** saved queries persist across sessions (browser storage)

---

## Epic 5: Training & TIP Integration

**Goal:** Elena can demo effectively and students have a clear path to TIP.

### Story 5.1: Enhanced "Take to TIP" Button

As an EPO Academy trainer (Elena),
I want a clear pathway from Explorer to TIP,
So that students can continue their learning journey in the full platform.

**Acceptance Criteria:**

**Given** any query is displayed
**When** user clicks "Take to TIP"
**Then** a modal/panel opens with clear instructions
**And** instructions explain how to use the query in TIP's Jupyter environment
**And** the SQL query is prominently displayed and copyable
**And** a link to the TIP platform is provided

---

### Story 5.2: TIP/Jupyter Export Instructions

As an EPO Academy trainer (Elena),
I want detailed instructions for using queries in TIP,
So that students can successfully replicate analyses in the full platform.

**Acceptance Criteria:**

**Given** a user views "Take to TIP" instructions
**When** the instructions display
**Then** step-by-step guidance is provided for:
  - Accessing TIP and opening Jupyter
  - Creating a new notebook
  - Setting up BigQuery connection
  - Pasting and running the query
**And** instructions include screenshots or visual aids where helpful
**And** common troubleshooting tips are included

---

### Story 5.3: GitHub Repository Integration

As a PATLIB professional or trainer,
I want easy access to the GitHub repository,
So that I can find documentation and additional resources.

**Acceptance Criteria:**

**Given** the footer or help section of the app
**When** displayed
**Then** a link to the GitHub repository is visible
**And** the repository contains a comprehensive README
**And** README includes: overview, query catalog, contribution guidelines
**And** link opens in new tab

---

## Epic 6: Stabilization & Refinement

**Goal:** Ensure the MVP is production-ready, maintainable, and verified correct before expanding scope.

### Story 6.1: Fix AI Query Builder & Dependencies

As a developer,
I want the AI Query Builder to work reliably in both local and cloud environments,
So that the core "AI" feature of the MVP is actually functional.

**Acceptance Criteria:**
**Given** the project configuration
**When** checked
**Then** `anthropic` library is listed in `requirements.txt`
**And** `app.py` correctly handles API key loading from both `.env` (local) and `st.secrets` (cloud)
**And** error handling is robust (friendly message if key is missing)

### Story 6.2: Refactor Monolithic App Structure

As a developer,
I want to break down the 1,800 LOC `app.py` into modular components,
So that the codebase is maintainable and new features (Epic 7+) can be added safely.

**Acceptance Criteria:**
**Given** the current `app.py`
**When** refactored
**Then** UI components (layout, rendering) are moved to `ui/` module
**And** Query logic is isolated in `logic/` or kept in `queries_bq.py`
**And** `app.py` becomes a lightweight orchestrator (<500 lines ideally)
**And** functionality passes all regression tests (app behaves exactly the same)

### Story 6.3: UI Polish & Consistency

As a user,
I want the visual hierarchy to be consistent,
So that the interface looks professional and polished.

**Acceptance Criteria:**
**Given** the Query Detail page
**When** the Question title (e.g., "Q01: ...") is displayed
**Then** it has the **same font size** as the Execution Time (e.g., "~1.0s")
**And** visual alignment between the question and time is centered
**And** any other evident UI misalignments are corrected

### Story 6.4: Query Quality Audit

As a Product Owner,
I want to verify that every query returns meaningful, correct data,
So that we don't ship "garbage" insights to users.

**Acceptance Criteria:**
**Given** the 40+ queries in the library
**When** audited
**Then** each query is executed and results verified for logical sense
**And** queries that return confusing/empty results are fixed or flagged
**And** column names in results are user-friendly (not `f0_` style)

