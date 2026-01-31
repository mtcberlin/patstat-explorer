---
stepsCompleted: [step-01-init, step-02-discovery, step-03-success, step-04-journeys, step-05-domain, step-06-innovation, step-07-project-type, step-08-scoping, step-09-functional, step-10-nonfunctional, step-11-polish, step-12-complete]
status: complete
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief-patstat-2026-01-28.md
  - docs/project-overview.md
  - docs/query-catalog.md
documentCounts:
  briefs: 1
  research: 0
  projectDocs: 2
classification:
  projectType: web_app
  domain: scientific_edtech
  complexity: low
  projectContext: brownfield
workflowType: 'prd'
date: 2026-01-28
author: Arne
project: patstat
---

# Product Requirements Document - PATSTAT Explorer

**Author:** Arne
**Date:** 2026-01-28

---

## Executive Summary

**PATSTAT Explorer** is a TIP adoption accelerator - a Streamlit-based web app that makes EPO PATSTAT patent analytics accessible to 300+ PATLIB centres across Europe.

**Problem:** PATLIB staff face decision paralysis when delivering patent insights to clients. Proven queries exist but are trapped in code-heavy formats that exclude 90% of potential users.

**Solution:** Zero-friction web interface with 40+ validated queries, dynamic parameters, AI-assisted query building, and a clear pathway to EPO's TIP platform.

**Target Users:**
- Maria (90%) - Generalist PATLIB professional who needs client-ready insights
- Klaus (10%) - Data enthusiast who wants to share queries with peers
- Elena - EPO Academy trainer who needs engaging demo tools

**MVP Scope:** All queries dynamic, UI beautification, contribution model, AI query builder (MCP)

**Architecture:** Streamlit Cloud (permanent home) + Google BigQuery + MCP/Claude API

**Success Metric:** EPO Academy adoption + 20% "Take to TIP" conversion rate

---

## Success Criteria

### User Success

| Persona | Success Indicator | Measurement | Target |
|---------|------------------|-------------|--------|
| **Maria (Generalist - 90%)** | Client satisfaction with insights delivered | Qualitative feedback, repeat usage | Clients say "This is exactly what I needed" |
| **Klaus (Data Enthusiast - 10%)** | Queries contributed to library | Count of submitted queries | Active contribution to community |
| **Klaus (Data Enthusiast - 10%)** | Queries reused by peers | Usage count per contributed query | Queries adopted by other PATLIBs |
| **Elena (EPO Trainer)** | Training engagement scores | Post-session ratings | 4.5+/5 stars |
| **Elena (EPO Trainer)** | Post-training TIP adoption | Students who click "Take to TIP" | Within 30 days of training |

**User Success Moments:**
- Maria: "I just did in 5 minutes what used to take me a full day"
- Klaus: "I can finally share my queries with everyone"
- Elena: Students write "Finally, I can actually *do* this back at my centre"

### Business Success

#### The Gateway Strategy

PATSTAT Explorer operates as a **TIP adoption accelerator** - a free, accessible entry point that demonstrates value and funnels users toward EPO's TIP platform.

| Timeframe | Objective | Validation |
|-----------|-----------|------------|
| **3 months** | EPO Academy adopts tool for TIP4PATLIB training | Tool used in at least one training session |
| **6 months** | Measurable "Take to TIP" conversions | 20% of query executions result in TIP export |
| **12 months** | TIP usage increase attributable to Explorer users | EPO confirms adoption correlation |

#### Strategic Success

- **For EPO:** TIP adoption rises because PATLIB staff saw accessible examples first
- **For PATLIB Centres:** Staff confidently use TIP after Explorer on-ramp
- **For Project:** Positive feedback flows to EPO Academy

### Technical Success

| Metric | Target | Rationale |
|--------|--------|-----------|
| **Deployment** | Streamlit.app runs without errors | Zero infrastructure maintenance |
| **Query Performance** | <15 seconds for uncached queries | Acceptable for training demos |
| **Chart Quality** | Export-ready for presentations | End clients need beautiful visuals |
| **Uptime** | Streamlit Cloud default SLA | Not mission-critical, demo tool |

### Key Performance Indicators

| KPI | Target | Measurement Method |
|-----|--------|-------------------|
| **Query Library Growth** | 50+ queries | Count of validated queries |
| **Training Adoption** | Used in EPO Academy curriculum | EPO Academy confirmation |
| **"Take to TIP" Clicks** | 20% of executions | Button click tracking |
| **Contributor Engagement** | 10+ unique contributors | Submitted query count by author |
| **PATLIB Centre Reach** | 50+ centres | Unique centre identification |

### Leading Indicators

- Users who run >3 queries in first session (engagement)
- Users who return within 7 days (retention)
- Users who click "View SQL" (pathway to contribution/TIP)
- Training attendees who access Explorer same week (activation)

---

## Product Scope

### MVP - Minimum Viable Product

**All required for launch (EPO Academy pilot + public PATLIB rollout):**

| Feature | Current State | MVP Target |
|---------|--------------|------------|
| **Query Library** | 19 queries | ~40 queries (+21 from EPO training) |
| **Dynamic Queries** | 1 dynamic, 18 static | All 19 → dynamic/parameterized |
| **UI Quality** | Functional | Beautified for presentations |
| **Contribution Model** | None | Interface for query submission |
| **AI Query Building** | None | Natural language → SQL (MCP) |
| **TIP Gateway** | GitHub link | "Take to TIP" with clear pathway |

### Out of Scope (Intentional)

| Feature | Rationale |
|---------|-----------|
| **User Authentication** | Open access - no login barriers |
| **Query Moderation** | Trust-based contribution, no approval queue |
| **Multi-Language** | English only for initial launch |
| **Mobile Optimization** | Desktop-first (training room use case) |
| **Custom Analytics** | Rely on Streamlit Cloud built-in stats |
| **Production Architecture** | Streamlit.app is the permanent home |

### Growth Features (Post-MVP)

- Import remaining 37 EPO training queries
- Community voting on most useful queries
- Regional PATLIB customizations (local examples)

### Vision (Future)

- Integration showcases with other EPO tools
- Expanded AI capabilities (query explanation, optimization suggestions)
- PATLIB contributor recognition program

**Note:** Future features are opportunities, not commitments. MVP success determines next steps.

---

## User Journeys

### Journey 1: Maria's Query Journey (Primary Happy Path)

**Persona:** Maria, Patent Information Specialist at a regional PATLIB centre in Spain. 15 years experience with Espacenet and Orbit. Knows patent law inside out, but data analytics feels like a foreign language.

**Opening Scene:**
It's Tuesday morning. Maria's phone rings - a local SME owner who manufactures medical packaging wants to know: "Who are our main competitors filing patents in Europe, and what's their strategy?" Maria's heart sinks slightly. She knows she could spend a full day pulling individual patents from Espacenet, copying data into Excel, trying to make sense of it. Her client needs this by Thursday.

**Rising Action:**
Maria remembers the PATSTAT Explorer tool from last month's EPO Academy training. She opens patstat.streamlit.app and navigates to the "Competitor Filing Strategy" query. She selects:
- Technology field: Medical devices
- Jurisdictions: EP, US, CN
- Year range: 2018-2024

She clicks "View SQL" - not because she understands it, but because seeing the query reassures her this is real data analysis, not magic. She clicks "Run Analysis."

**Climax:**
In 8 seconds, a beautiful chart appears showing filing trends by competitor across jurisdictions. Maria sees immediately that one competitor has dramatically increased CN filings while reducing EP filings. She clicks "Export" and has a presentation-ready chart. She runs two more queries: "Top Applicants in Medical Devices" and "Technology Trend Analysis." Within 20 minutes, she has three polished charts and clear insights.

**Resolution:**
Maria emails her client the same afternoon with a professional analysis. The SME owner responds: "This is exactly what I needed. How much do I owe you?" Maria feels like a data expert - without writing a single line of code. She bookmarks PATSTAT Explorer for next time.

**Capabilities Revealed:**
- Query selection with clear descriptions
- Parameter adjustment (jurisdiction, year range, technology)
- SQL preview for transparency
- Fast query execution (<15 seconds)
- Export-ready chart generation
- Professional presentation quality

---

### Journey 2: Klaus's Contribution Journey (Query Submission)

**Persona:** Klaus, Senior Patent Analyst at a German PATLIB centre. Self-taught SQL, builds Tableau dashboards, frustrated that his queries live on his laptop where nobody else can use them.

**Opening Scene:**
Klaus has just finished a brilliant query for a local university - it identifies patent families where the university is co-applicant with industry partners, showing technology transfer success. His colleague from another PATLIB centre calls: "Klaus, how did you do that analysis? Can you send me the query?" This is the third time this month someone has asked. Klaus thinks: "There has to be a better way."

**Rising Action:**
Klaus opens PATSTAT Explorer and navigates to the "Contribute Query" section. He pastes his SQL query and fills in the metadata:
- Title: "University-Industry Co-Patenting Analysis"
- Description: "Identifies patent families with university-industry collaboration"
- Tags: UNIVERSITY, TECHNOLOGY_TRANSFER
- Parameters: university_name (text), year_start (number), year_end (number)

He clicks "Preview" and sees how his query will look to other users. The interface shows which parameters will become dropdown menus and which will be text inputs.

**Climax:**
Klaus clicks "Submit Query." A confirmation appears: "Thank you for your contribution! Your query is now available in the library." He shares the link with his colleague. Two weeks later, Klaus checks the usage stats - his query has been run 47 times by 12 different PATLIB centres. He sees a comment: "This query helped us win a regional innovation award presentation!"

**Resolution:**
Klaus feels validated. His expertise is now helping 300 PATLIB centres, not just his own. He starts thinking about which other queries he could contribute. He's become a recognized contributor in the PATLIB community.

**Capabilities Revealed:**
- Query contribution interface
- Metadata input (title, description, tags)
- Parameter definition for dynamic queries
- Preview before submission
- Usage statistics per query (via Streamlit Cloud)
- Community recognition

---

### Journey 3: Elena's Training Demo Journey (EPO Academy Session)

**Persona:** Dr. Elena Vasquez, Senior Training Officer at EPO Academy. Responsible for TIP4PATLIB curriculum. Measured by student engagement scores.

**Opening Scene:**
Elena is preparing for tomorrow's TIP4PATLIB training session. She has 25 PATLIB staff from across Europe attending virtually. Past sessions on TIP/PATSTAT got mixed reviews - students were impressed by possibilities but overwhelmed by Jupyter notebooks. Elena needs a way to show value before diving into the technical details.

**Rising Action:**
Elena opens PATSTAT Explorer and prepares her demo sequence:
1. First, she'll show "Database Statistics" - the wow factor of 140M patents
2. Then "Green Technology Trends" - timely topic, beautiful multi-country chart
3. Then the interactive query - she'll ask a student to pick their country and technology field
4. Finally, she'll click "Take to TIP" to show the bridge to deeper analysis

She rehearses the flow, noting how each query takes under 10 seconds. She prepares her talking points: "This is what you can do TODAY, without any coding. Now let me show you how to do even more in TIP..."

**Climax:**
During the live session, Elena shares her screen and runs the Technology Trend Analysis. She asks: "Who's from Spain? Maria, what technology field is important in your region?" Maria says "Medical devices." Elena selects Spain, Medical Technology, clicks Run - and in 8 seconds shows Maria's region's patent trends. The chat explodes with requests: "Can you show France?" "What about electrical engineering?"

Elena clicks "Take to TIP" and says: "This is where you can customize these queries further. Let me show you how this same query looks in a Jupyter notebook..."

**Resolution:**
Post-training survey: 4.8/5 stars. Comments include: "Finally, I can actually DO this back at my centre" and "Best PATSTAT training I've attended." Elena's manager sees the scores and asks her to run the session again next month.

**Capabilities Revealed:**
- Impressive visual demos for training
- Real-time parameter changes during presentation
- Audience engagement through personalization
- Clear "Take to TIP" transition pathway
- Fast execution for live demos
- Mobile-friendly for screen sharing

---

### Journey 4: Maria's AI Query Journey (Custom Analysis)

**Persona:** Maria again, but now with a client question that doesn't match any existing query.

**Opening Scene:**
A regional government official calls Maria: "We're writing a report on innovation in renewable energy. Can you show us which companies in our region have the most wind energy patents, and whether they're growing or declining?" Maria checks PATSTAT Explorer - there's no exact query for this. In the past, she would have said "Let me get back to you in a week" and then struggled with Jupyter notebooks.

**Rising Action:**
Maria clicks "AI Query Builder" and types in natural language: "Show me the top 10 companies in Catalonia with wind energy patents (IPC F03D), with their filing trends from 2015 to 2024, and calculate year-over-year growth rate."

The AI responds with a proposed SQL query and explains what it does: "This query will join the applications table with person data, filter for Catalonia using NUTS codes, select IPC class F03D (wind motors), and calculate growth rates..."

Maria can see the SQL but doesn't need to understand it. She clicks "Preview Results" and sees a sample.

**Climax:**
The query runs and produces exactly what the official asked for - a ranked list of regional wind energy innovators with trend lines. Maria spots something interesting: a small company she's never heard of has 400% growth. She adds this insight to her report.

**Resolution:**
Maria delivers the analysis the next day. The official is impressed: "How did you do this so quickly?" Maria smiles: "I have good tools." She saves the AI-generated query to her favorites for future use. She's gone from "I can't do custom analysis" to "I can answer almost any question."

**Capabilities Revealed:**
- Natural language query input
- AI-generated SQL with explanation
- Preview before full execution
- Custom analysis without coding
- Query saving for reuse
- Regional filtering (NUTS codes)
- Growth rate calculations

---

## Journey Requirements Summary

| Journey | Key Capabilities Required |
|---------|--------------------------|
| **Maria's Query Journey** | Query library, parameter controls, SQL preview, fast execution, chart export |
| **Klaus's Contribution** | Contribution interface, metadata input, parameter definition, usage stats |
| **Elena's Training Demo** | Visual impact, real-time interaction, "Take to TIP" pathway, fast execution |
| **Maria's AI Query** | Natural language input, AI SQL generation, explanation, preview, save |

### Capability Categories Revealed

**Core Query Execution:**
- Browse and select from query library
- Adjust parameters (jurisdiction, year, technology)
- View SQL for transparency
- Execute queries (<15 seconds)
- Display results in tables and charts

**Export & Presentation:**
- Export charts as images
- Presentation-quality visualizations
- Clean, professional layouts

**Query Contribution:**
- Submit new queries with metadata
- Define dynamic parameters
- Preview before publishing
- View usage statistics

**AI-Assisted Query Building:**
- Natural language query input
- AI-generated SQL
- Plain-language explanation
- Preview and refinement
- Save to favorites

**Training Integration:**
- "Take to TIP" button with clear pathway
- Fast execution for live demos
- Audience engagement features

---

## Web App Technical Requirements

### Architecture Overview

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Framework** | Streamlit | Rapid development, built-in components, zero frontend code |
| **Hosting** | Streamlit Cloud | Free tier, zero maintenance, instant deploys |
| **Database** | Google BigQuery | EPO PATSTAT data already loaded, ~450GB |
| **State** | Session-based | No user accounts, no persistent state needed |

### Browser Support

- **Target:** Modern desktop browsers (Chrome, Firefox, Edge, Safari)
- **Mobile:** Not optimized (desktop-first for training rooms)
- **IE11:** Not supported

### Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| **Query execution** | <15 seconds | Acceptable for demos |
| **Page load** | <3 seconds | Streamlit default |
| **Concurrent users** | ~50 | Training session size |

### Intentionally Simple

This is a **demo/training tool**, not production software:
- No SEO optimization needed (users come via direct links)
- No real-time collaboration
- No offline support
- No accessibility certification (standard Streamlit components)
- No internationalization (English only)

---

## Project Scoping & Phased Development

### MVP Strategy

**Approach:** Problem-Solving MVP - minimum viable to validate the gateway strategy and solve PATLIB decision paralysis.

**Scope Philosophy:** This is a demo/training tool. Keep it simple, ship fast, iterate based on EPO Academy feedback.

### MVP Feature Set (Phase 1)

| Feature | Effort | Priority |
|---------|--------|----------|
| Convert 18 static queries → dynamic | Medium | Must-have |
| Add ~21 queries from EPO training PDFs | Medium | Must-have |
| UI beautification | Low | Must-have |
| Query contribution interface | Low | Must-have |
| AI query builder (MCP) | Medium | Must-have |
| "Take to TIP" pathway | Already exists | Must-have |

**Core Journeys Supported:** All 4 (Maria's query, Klaus's contribution, Elena's demo, Maria's AI query)

### Post-MVP (Phase 2)

- Import remaining ~37 EPO training queries
- Community voting on queries
- Regional PATLIB customizations
- Usage analytics beyond Streamlit defaults

### Out of Scope (Intentional)

- User authentication
- Query moderation workflow
- Multi-language support
- Mobile optimization
- Production architecture migration

### Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| **EPO query extraction** | Medium | Start with highest-value queries, add incrementally |
| **MCP integration complexity** | Low | Fallback: manual query builder if AI delayed |
| **Streamlit performance at scale** | Low | Not a concern for 50 concurrent users |

### Resource Requirements

- **Team:** 1 developer (Arne)
- **Timeline:** Not estimated (per project guidelines)
- **Dependencies:** Access to EPO training PDFs, MCP/Claude API

---

## Functional Requirements

### Query Library & Discovery

- **FR1:** Users can browse all available queries in a categorized library
- **FR2:** Users can filter queries by stakeholder type (PATLIB, BUSINESS, UNIVERSITY)
- **FR3:** Users can view query descriptions explaining what each query reveals
- **FR4:** Users can see estimated execution time for each query
- **FR5:** Users can search queries by keyword or topic

### Query Execution & Results

- **FR6:** Users can execute any query from the library
- **FR7:** Users can view query results in tabular format
- **FR8:** System displays execution status and timing information
- **FR9:** Users can re-run queries with modified parameters without page refresh
- **FR10:** System caches query results for faster repeated access

### Dynamic Parameters

- **FR11:** Users can adjust parameters relevant to the selected query. Each query defines which parameters it accepts.
- **FR12:** Users can adjust year range parameters via slider or input
- **FR13:** Users can select technology field from WIPO classification list
- **FR14:** Users can select multiple values for multi-select parameters
- **FR15:** System validates parameter inputs before query execution
- **FR15a:** Frontend dynamically renders only the parameter controls relevant to the selected query based on its parameter configuration.

### Data Visualization & Export

- **FR16:** Users can view query results as interactive charts
- **FR17:** Users can switch between chart types where applicable (line, bar, etc.)
- **FR18:** Charts display with colors distinguishing multiple data series
- **FR19:** Users can export charts as images for presentations
- **FR20:** Users can download result data as CSV

### Query Transparency

- **FR21:** Users can view the SQL query before execution
- **FR22:** Users can view the SQL with parameter values substituted
- **FR23:** Users can copy SQL to clipboard for use elsewhere
- **FR24:** Each query displays explanation of data sources and methodology

### Query Contribution

- **FR25:** Users can submit new queries to the library
- **FR26:** Users can provide metadata for contributed queries (title, description, tags)
- **FR27:** Users can define dynamic parameters for contributed queries
- **FR28:** Users can preview how their contributed query will appear
- **FR29:** System validates contributed query SQL syntax before acceptance

### AI Query Building

- **FR30:** Users can describe desired analysis in natural language
- **FR31:** System generates SQL query from natural language description
- **FR32:** System explains generated query in plain language
- **FR33:** Users can preview AI-generated query results before full execution
- **FR34:** Users can refine natural language input and regenerate query
- **FR35:** Users can save AI-generated queries to favorites

### Training Integration

- **FR36:** Users can access "Take to TIP" pathway for any query
- **FR37:** System provides instructions for using queries in TIP/Jupyter
- **FR38:** Users can access GitHub repository with query documentation
- **FR39:** Queries execute fast enough for live training demonstrations (<15s)

---

## Non-Functional Requirements

### Performance

| Metric | Requirement | Rationale |
|--------|-------------|-----------|
| **Query Execution** | <15 seconds for uncached queries | Live training demo usability |
| **Cached Query** | <3 seconds | Repeat queries should feel instant |
| **Page Load** | <5 seconds initial load | Standard web expectation |
| **Chart Rendering** | <2 seconds after data load | Smooth user experience |

### Integration

| System | Requirement | Notes |
|--------|-------------|-------|
| **Google BigQuery** | Authenticated via service account | Existing, working |
| **MCP/Claude API** | API key authentication | For AI query building |
| **GitHub** | Public repository access | For "Take to TIP" pathway |

### Operational

| Aspect | Requirement | Rationale |
|--------|-------------|-----------|
| **Hosting** | Streamlit Cloud free tier | Zero maintenance |
| **Deployment** | Auto-deploy on git push | Standard Streamlit Cloud |
| **Monitoring** | Streamlit Cloud built-in analytics | No custom monitoring needed |
| **Backup** | Git repository is source of truth | No database backup needed |

### Explicitly Not Required

| Category | Status | Rationale |
|----------|--------|-----------|
| **Security/Auth** | Not required | Open access tool, no user data |
| **WCAG Compliance** | Not required | Standard Streamlit components sufficient |
| **High Availability** | Not required | Demo tool, occasional downtime acceptable |
| **Data Privacy** | Not required | Public PATSTAT data only |
| **Audit Logging** | Not required | No compliance requirements |
