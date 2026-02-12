# Story 5.3: GitHub Repository Integration

Status: ready-for-dev

## Story

As a PATLIB professional or trainer,
I want easy access to the GitHub repository,
so that I can find documentation and additional resources.

## Acceptance Criteria

1. **Given** the footer or help section of the app
   **When** displayed
   **Then** a link to the GitHub repository is visible
   **And** the link opens in a new tab

2. **Given** the GitHub repository
   **When** a user visits it
   **Then** a comprehensive README is available
   **And** README includes: overview, query catalog, contribution guidelines

3. **Given** the README documentation
   **When** viewed on GitHub
   **Then** it serves as standalone documentation
   **And** links back to the deployed app

## Tasks / Subtasks

- [ ] Task 1: Add GitHub link to app footer/header (AC: #1)
  - [ ] Position link in footer area
  - [ ] Use GitHub icon/logo
  - [ ] Open in new tab
  - [ ] Style appropriately (subtle but visible)

- [ ] Task 2: Create/update comprehensive README (AC: #2)
  - [ ] Project overview and purpose
  - [ ] Quick start guide
  - [ ] Query catalog overview
  - [ ] How to contribute queries
  - [ ] Technical documentation links

- [ ] Task 3: Add query catalog to README (AC: #2)
  - [ ] List all queries with descriptions
  - [ ] Organize by category
  - [ ] Include example use cases

- [ ] Task 4: Write contribution guidelines (AC: #2)
  - [ ] How to submit new queries
  - [ ] SQL best practices for PATSTAT
  - [ ] Testing requirements
  - [ ] Pull request process

- [ ] Task 5: Cross-link app and repository (AC: #3)
  - [ ] README links to deployed app
  - [ ] App links to repository
  - [ ] Ensure URLs are correct

## Dev Notes

### Footer Link Placement

```python
# At end of main() or in a footer function
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(
        """
        <div style="text-align: center; padding: 10px;">
            <a href="https://github.com/YOUR_ORG/patstat-explorer" target="_blank">
                📁 View on GitHub
            </a>
            &nbsp;|&nbsp;
            <a href="https://tip.epo.org" target="_blank">
                🎓 EPO TIP Platform
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
```

### README Structure

```markdown
# PATSTAT Explorer 📊

**Patent analysis made accessible** - A Streamlit app for querying EPO PATSTAT on BigQuery.

[![PATSTAT Explorer](https://img.shields.io/badge/PATSTAT_Explorer-Live-blue)](https://patstatexplorer.depa.tech)

## Overview

PATSTAT Explorer provides 40+ validated patent analysis queries for PATLIB professionals,
researchers, and anyone interested in patent intelligence.

## Quick Start

1. Visit [patstatexplorer.depa.tech](https://patstatexplorer.depa.tech)
2. Choose a category (Competitors, Trends, Regional, Technology)
3. Select a query
4. Adjust parameters
5. Click "Run Analysis"

## Features

- **40+ Validated Queries** - From basic statistics to complex analysis
- **Dynamic Parameters** - Customize jurisdiction, year range, technology field
- **Beautiful Visualizations** - Altair charts ready for presentations
- **SQL Transparency** - See and copy the underlying SQL
- **AI Query Builder** - Describe what you need in plain English
- **TIP Integration** - Easy pathway to EPO's Jupyter environment

## Query Catalog

### Competitors
- Q06: Who leads patent filing in each country?
- Q10: Who's building AI diagnostics portfolios?
- Q11: Who are the top patent applicants?
- Q12: Where do MedTech competitors file?
...

### Trends
- Q03: How have applications changed over time?
- Q07: What's the green technology trend?
- Q13: Which patents are most cited?
- Q18: What are the fastest-growing technology areas?
...

### Regional
- Q02: Which patent offices are most active?
- Q15: How do German states compare in MedTech?
- Q16: What's the per-capita patent activity?
- Q17: How do regions compare by technology sector?
...

### Technology
- Q04: What are the most common IPC classes?
- Q08: Which technology fields are most active?
- Q09: Who's leading in AI-based ERP?
- Q14: What are grant rates by technology?
...

## For Contributors

### Submitting Queries

1. Test your query in BigQuery
2. Ensure it executes in <15 seconds
3. Add metadata (title, description, tags)
4. Submit via the in-app "Contribute Query" feature

Or submit a pull request with:
- Query added to `queries_bq.py`
- Test coverage
- Documentation updates

### SQL Guidelines

- Use BigQuery syntax
- Include appropriate LIMIT
- Handle NULLs gracefully
- Follow existing patterns in `queries_bq.py`

## Technical Details

- **Framework**: Streamlit
- **Database**: Google BigQuery
- **Data**: EPO PATSTAT 2025 Autumn
- **Hosting**: Streamlit Cloud

## Links

- [EPO PATSTAT](https://www.epo.org/searching-for-patents/business/patstat.html)
- [EPO TIP Platform](https://tip.epo.org)
- [BigQuery PATSTAT Documentation](https://cloud.google.com/bigquery/public-data/epo-patstat)

## License

MIT License - See LICENSE file

---

Built for the PATLIB community 🌍
```

### Query Catalog Generation

Can auto-generate from QUERIES dict:
```python
def generate_query_catalog_markdown():
    """Generate README query catalog from QUERIES dict."""
    categories = {}
    for qid, query in QUERIES.items():
        cat = query.get('category', 'Other')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((qid, query['title']))

    markdown = "## Query Catalog\n\n"
    for cat, queries in sorted(categories.items()):
        markdown += f"### {cat}\n"
        for qid, title in sorted(queries):
            markdown += f"- {qid}: {title}\n"
        markdown += "\n"

    return markdown
```

### GitHub Repository URL

```python
GITHUB_REPO_URL = "https://github.com/YOUR_ORG/patstat-explorer"  # Update with actual URL
```

### Project Structure Notes

- README.md at repository root
- CONTRIBUTING.md for detailed contribution guidelines
- docs/ folder for additional documentation
- Link verification after deployment

### References

- [Source: PRD FR38] GitHub repository access
- [Source: PRD NFR7] GitHub public repository integration
- [Source: docs/] Existing documentation structure
- [Source: queries_bq.py] Query catalog source

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
