import streamlit as st
import pandas as pd
import altair as alt
from google.cloud import bigquery
from google.oauth2 import service_account
import os
from dotenv import load_dotenv
import time
import json
from queries_bq import QUERIES, DYNAMIC_QUERIES

# =============================================================================
# COLOR PALETTE (Story 1.4 - UX Design Spec)
# =============================================================================
COLOR_PRIMARY = "#1E3A5F"
COLOR_SECONDARY = "#0A9396"
COLOR_ACCENT = "#FFB703"
COLOR_PALETTE = [COLOR_PRIMARY, COLOR_SECONDARY, COLOR_ACCENT, "#E63946", "#457B9D"]

# Load environment variables
load_dotenv()


# =============================================================================
# SESSION STATE & NAVIGATION (Story 1.1)
# =============================================================================

# Default parameter values (DRY - single source of truth)
DEFAULT_YEAR_START = 2014
DEFAULT_YEAR_END = 2023
DEFAULT_JURISDICTIONS = ["EP", "US", "DE"]
DEFAULT_TECH_FIELD = None

# Year range bounds for sliders
YEAR_MIN = 1990
YEAR_MAX = 2024


def init_session_state():
    """Initialize session state for page navigation and parameters.

    Sets default values only if keys don't already exist.
    Navigation state:
    - current_page: 'landing', 'detail', 'contribute', or 'ai_builder'
    - selected_query: query ID when on detail page
    - selected_category: preserves category filter across navigation

    Parameter state (Story 1.2):
    - year_start, year_end: year range for queries
    - jurisdictions: list of patent office codes
    - tech_field: WIPO technology field code or None

    Search/Filter state (Story 2.1):
    - search_term: text search for queries
    - selected_stakeholders: stakeholder tag filters
    """
    # Navigation state
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = 'landing'
    if 'selected_query' not in st.session_state:
        st.session_state['selected_query'] = None
    if 'selected_category' not in st.session_state:
        st.session_state['selected_category'] = None

    # Parameter state (Story 1.2)
    if 'year_start' not in st.session_state:
        st.session_state['year_start'] = DEFAULT_YEAR_START
    if 'year_end' not in st.session_state:
        st.session_state['year_end'] = DEFAULT_YEAR_END
    if 'jurisdictions' not in st.session_state:
        st.session_state['jurisdictions'] = DEFAULT_JURISDICTIONS.copy()
    if 'tech_field' not in st.session_state:
        st.session_state['tech_field'] = DEFAULT_TECH_FIELD

    # Search/Filter state (Story 2.1)
    if 'search_term' not in st.session_state:
        st.session_state['search_term'] = ''
    if 'selected_stakeholders' not in st.session_state:
        st.session_state['selected_stakeholders'] = []

    # Contribution state (Story 3.1)
    if 'contribution' not in st.session_state:
        st.session_state['contribution'] = {
            'title': '',
            'description': '',
            'tags': [],
            'category': '',
            'sql': '',
            'parameters': [],
            'explanation': ''
        }
    if 'contribution_step' not in st.session_state:
        st.session_state['contribution_step'] = 1

    # AI Builder state (Story 4.1)
    if 'ai_request' not in st.session_state:
        st.session_state['ai_request'] = ''
    if 'ai_generation' not in st.session_state:
        st.session_state['ai_generation'] = None
    if 'ai_query_versions' not in st.session_state:
        st.session_state['ai_query_versions'] = []

    # Favorites state (Story 4.4)
    if 'favorites' not in st.session_state:
        st.session_state['favorites'] = []

    # Contributed queries (Story 3.4)
    if 'contributed_queries' not in st.session_state:
        st.session_state['contributed_queries'] = {}


def go_to_landing():
    """Navigate to landing page, preserving category selection (AC #5).

    Resets parameter state to defaults (Story 1.2 AC #2).
    """
    st.session_state['current_page'] = 'landing'
    st.session_state['selected_query'] = None
    # Keep selected_category for state restoration

    # Reset parameter state to defaults (Story 1.2 AC #2)
    st.session_state['year_start'] = DEFAULT_YEAR_START
    st.session_state['year_end'] = DEFAULT_YEAR_END
    st.session_state['jurisdictions'] = DEFAULT_JURISDICTIONS.copy()
    st.session_state['tech_field'] = DEFAULT_TECH_FIELD

    st.rerun()


def go_to_detail(query_id: str):
    """Navigate to detail page for a specific query (AC #4).

    Args:
        query_id: Must be a valid key in QUERIES or contributed_queries dict
    """
    all_queries = get_all_queries()
    if query_id not in all_queries:
        return  # Invalid query_id, don't navigate
    st.session_state['current_page'] = 'detail'
    st.session_state['selected_query'] = query_id
    st.rerun()


def go_to_contribute():
    """Navigate to contribute query page (Story 3.1)."""
    st.session_state['current_page'] = 'contribute'
    st.session_state['contribution_step'] = 1
    st.rerun()


def go_to_ai_builder():
    """Navigate to AI query builder page (Story 4.1)."""
    st.session_state['current_page'] = 'ai_builder'
    st.rerun()


# Category definitions for landing page pills (AC #1)
CATEGORIES = ["Competitors", "Trends", "Regional", "Technology"]

# Stakeholder tags for filtering (Story 2.1)
STAKEHOLDER_TAGS = ["PATLIB", "BUSINESS", "UNIVERSITY"]


def filter_queries(queries: dict, search_term: str = None, category: str = None,
                   stakeholders: list = None) -> dict:
    """Filter queries by search term, category, and stakeholder tags (Story 2.1).

    Args:
        queries: The QUERIES dict to filter
        search_term: Text to search in title, description, and tags
        category: Category filter (Competitors, Trends, Regional, Technology)
        stakeholders: List of stakeholder tags to filter by (AND logic within)

    Returns:
        Filtered dict of queries
    """
    filtered = queries

    # Search filter - match title, description, or tags
    if search_term and search_term.strip():
        search_lower = search_term.lower().strip()
        filtered = {
            qid: q for qid, q in filtered.items()
            if search_lower in q.get('title', '').lower()
            or search_lower in q.get('description', '').lower()
            or any(search_lower in tag.lower() for tag in q.get('tags', []))
            or search_lower in qid.lower()
        }

    # Category filter
    if category:
        filtered = {
            qid: q for qid, q in filtered.items()
            if q.get('category') == category
        }

    # Stakeholder filter - must have at least one of selected stakeholders
    if stakeholders:
        filtered = {
            qid: q for qid, q in filtered.items()
            if any(s in q.get('tags', []) for s in stakeholders)
        }

    return filtered


def get_all_queries() -> dict:
    """Get all queries including contributed ones (Story 3.4)."""
    all_queries = QUERIES.copy()
    # Add contributed queries from session
    contributed = st.session_state.get('contributed_queries', {})
    all_queries.update(contributed)
    return all_queries


def render_tags_inline(tags: list) -> str:
    """Render colored tag pills as HTML (Story 2.2)."""
    tag_colors = {
        "PATLIB": "#1f77b4",
        "BUSINESS": "#2ca02c",
        "UNIVERSITY": "#9467bd"
    }
    return " ".join([
        f'<span style="background-color: {tag_colors.get(t, "#666")}; '
        f'color: white; padding: 2px 8px; border-radius: 10px; '
        f'font-size: 0.75em; margin-right: 4px;">{t}</span>'
        for t in tags
    ])

# =============================================================================
# PARAMETER REFERENCE DATA (Story 1.2)
# =============================================================================

# Available jurisdictions for multiselect
JURISDICTIONS = ["EP", "US", "CN", "JP", "KR", "DE", "FR", "GB", "WO"]

# WIPO Technology Fields with sector grouping
# Source: WIPO IPC-Technology Concordance
TECH_FIELDS = {
    1: ("Electrical machinery, apparatus, energy", "Electrical engineering"),
    2: ("Audio-visual technology", "Electrical engineering"),
    3: ("Telecommunications", "Electrical engineering"),
    4: ("Digital communication", "Electrical engineering"),
    5: ("Basic communication processes", "Electrical engineering"),
    6: ("Computer technology", "Electrical engineering"),
    7: ("IT methods for management", "Electrical engineering"),
    8: ("Semiconductors", "Electrical engineering"),
    9: ("Optics", "Instruments"),
    10: ("Measurement", "Instruments"),
    11: ("Analysis of biological materials", "Instruments"),
    12: ("Control", "Instruments"),
    13: ("Medical technology", "Instruments"),
    14: ("Organic fine chemistry", "Chemistry"),
    15: ("Biotechnology", "Chemistry"),
    16: ("Pharmaceuticals", "Chemistry"),
    17: ("Macromolecular chemistry, polymers", "Chemistry"),
    18: ("Food chemistry", "Chemistry"),
    19: ("Basic materials chemistry", "Chemistry"),
    20: ("Materials, metallurgy", "Chemistry"),
    21: ("Surface technology, coating", "Chemistry"),
    22: ("Micro-structural and nano-technology", "Chemistry"),
    23: ("Chemical engineering", "Chemistry"),
    24: ("Environmental technology", "Chemistry"),
    25: ("Handling", "Mechanical engineering"),
    26: ("Machine tools", "Mechanical engineering"),
    27: ("Engines, pumps, turbines", "Mechanical engineering"),
    28: ("Textile and paper machines", "Mechanical engineering"),
    29: ("Other special machines", "Mechanical engineering"),
    30: ("Thermal processes and apparatus", "Mechanical engineering"),
    31: ("Mechanical elements", "Mechanical engineering"),
    32: ("Transport", "Mechanical engineering"),
    33: ("Furniture, games", "Other fields"),
    34: ("Other consumer goods", "Other fields"),
    35: ("Civil engineering", "Other fields"),
}


def render_parameter_block():
    """Render the parameter block with Time → Geography → Technology → Action order.

    Returns:
        tuple: (year_start, year_end, jurisdictions, tech_field, run_clicked)
    """
    with st.container(border=True):
        # Use columns for horizontal layout: Time | Geography | Technology | Action
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

        with col1:
            # Time: Year range slider
            year_range = st.slider(
                "Year Range",
                min_value=YEAR_MIN,
                max_value=YEAR_MAX,
                value=(st.session_state.get('year_start', DEFAULT_YEAR_START),
                       st.session_state.get('year_end', DEFAULT_YEAR_END)),
                help="Select the filing year range for analysis"
            )
            year_start, year_end = year_range

        with col2:
            # Geography: Jurisdiction multiselect
            jurisdictions = st.multiselect(
                "Jurisdictions",
                options=JURISDICTIONS,
                default=st.session_state.get('jurisdictions', DEFAULT_JURISDICTIONS),
                help="Select patent offices to include"
            )
            # Validation: warn if no jurisdictions selected
            if not jurisdictions:
                st.warning("Select at least one jurisdiction")

        with col3:
            # Technology: Tech field selectbox with sector grouping
            tech_options = [None] + list(TECH_FIELDS.keys())
            current_tech = st.session_state.get('tech_field', DEFAULT_TECH_FIELD)
            default_index = 0 if current_tech is None else tech_options.index(current_tech)

            tech_field = st.selectbox(
                "Technology Field",
                options=tech_options,
                index=default_index,
                format_func=lambda x: "All fields" if x is None else f"{TECH_FIELDS[x][0]} ({TECH_FIELDS[x][1]})",
                help="Filter by WIPO technology field"
            )

        with col4:
            # Action: Run button (with vertical spacing to align)
            st.write("")  # Spacing to align with other controls
            run_clicked = st.button("Run Analysis", type="primary", use_container_width=True)

    # Update session state
    st.session_state['year_start'] = year_start
    st.session_state['year_end'] = year_end
    st.session_state['jurisdictions'] = jurisdictions
    st.session_state['tech_field'] = tech_field

    return year_start, year_end, jurisdictions, tech_field, run_clicked


def resolve_options(options):
    """Resolve option references to actual lists (Story 1.8).

    Args:
        options: Either a list of options, or a string reference like "jurisdictions"

    Returns:
        List of option values
    """
    if options == 'jurisdictions':
        return JURISDICTIONS
    elif options == 'wipo_fields':
        return list(TECH_FIELDS.keys())
    elif options == 'tech_sectors':
        # Unique WIPO technology sectors
        return sorted(set(field[1] for field in TECH_FIELDS.values()))
    elif options == 'medtech_competitors':
        # Major MedTech competitors for competitive analysis (Q12)
        return [
            "Medtronic", "Johnson & Johnson", "Abbott", "Boston Scientific",
            "Stryker", "Zimmer Biomet", "Smith & Nephew", "Edwards Lifesciences",
            "Baxter", "Fresenius", "B. Braun", "Philips", "Siemens Healthineers",
            "GE Healthcare", "Becton Dickinson"
        ]
    elif isinstance(options, list):
        return options
    return []


def render_single_parameter(name: str, config: dict, key_prefix: str = ""):
    """Render a single parameter control based on its type (Story 1.8).

    Args:
        name: Parameter name
        config: Parameter configuration dict with type, label, defaults, etc.
        key_prefix: Optional prefix for Streamlit widget keys

    Returns:
        The value from the rendered control
    """
    param_type = config.get('type')
    label = config.get('label', name)
    key = f"{key_prefix}_{name}" if key_prefix else name

    if param_type == 'year_range':
        default_start = config.get('default_start', DEFAULT_YEAR_START)
        default_end = config.get('default_end', DEFAULT_YEAR_END)
        year_range = st.slider(
            label,
            min_value=YEAR_MIN,
            max_value=YEAR_MAX,
            value=(default_start, default_end),
            key=key
        )
        return {'year_start': year_range[0], 'year_end': year_range[1]}

    elif param_type == 'multiselect':
        options = resolve_options(config.get('options', []))
        defaults = config.get('defaults', options[:3] if options else [])
        # Ensure defaults are valid options
        valid_defaults = [d for d in defaults if d in options]
        return st.multiselect(label, options, default=valid_defaults, key=key)

    elif param_type == 'select':
        options = resolve_options(config.get('options', []))
        default = config.get('defaults')
        default_index = options.index(default) if default in options else 0
        return st.selectbox(label, options, index=default_index, key=key)

    elif param_type == 'text':
        default = config.get('defaults', '')
        placeholder = config.get('placeholder', '')
        return st.text_input(label, value=default, placeholder=placeholder, key=key)

    # Unknown parameter type - warn and return None
    if param_type:
        st.warning(f"Unknown parameter type '{param_type}' for {name}")
    return None


def render_query_parameters(query_id: str) -> tuple:
    """Render parameter controls based on query's parameter configuration (Story 1.8).

    Reads the query's 'parameters' dict and renders only the controls
    defined for that specific query.

    Args:
        query_id: Query ID to get parameter config for

    Returns:
        tuple: (collected_params dict, run_clicked bool)
    """
    query = get_all_queries().get(query_id, {})
    params_config = query.get('parameters', {})

    if not params_config:
        # No parameters defined for this query
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info("This query has no configurable parameters.")
            with col2:
                st.write("")  # Spacing
                run_clicked = st.button("Run Analysis", type="primary", use_container_width=True)
        return {}, run_clicked

    collected_params = {}
    key_prefix = f"param_{query_id}"

    with st.container(border=True):
        # Determine layout based on parameter count
        param_count = len(params_config)
        if param_count == 1:
            cols = st.columns([3, 1])
        elif param_count == 2:
            cols = st.columns([2, 2, 1])
        else:
            cols = st.columns([2, 2, 2, 1])

        col_idx = 0
        for param_name, param_def in params_config.items():
            with cols[col_idx % (len(cols) - 1)]:  # Last column reserved for button
                value = render_single_parameter(param_name, param_def, key_prefix)

                # Handle year_range which returns a dict
                if param_def.get('type') == 'year_range':
                    collected_params['year_start'] = value['year_start']
                    collected_params['year_end'] = value['year_end']
                else:
                    collected_params[param_name] = value
            col_idx += 1

        # Run button in last column
        with cols[-1]:
            st.write("")  # Spacing to align with other controls
            run_clicked = st.button("Run Analysis", type="primary", use_container_width=True)

    return collected_params, run_clicked


# =============================================================================
# INSIGHT & VISUALIZATION (Story 1.4)
# =============================================================================

def generate_insight_headline(df, query_info):
    """Generate an insight headline based on query results (Story 1.4).

    Returns a bold sentence summarizing the key finding.
    """
    if df.empty:
        return None

    category = query_info.get("category", "")
    title = query_info.get("title", "")

    # Generate headline based on data shape and category
    if len(df) == 1 and len(df.columns) == 2:
        # Single metric result
        return f"**{df.iloc[0, 0]}: {df.iloc[0, 1]}**"

    if "count" in df.columns[-1].lower() or "total" in df.columns[-1].lower():
        # Ranking/count data - highlight top result
        top_row = df.iloc[0]
        top_name = top_row.iloc[0]
        top_value = top_row.iloc[-1]
        if isinstance(top_value, (int, float)):
            return f"**{top_name} leads with {top_value:,.0f}**"

    if "year" in df.columns[0].lower():
        # Time series - show trend
        if len(df) > 1:
            first_val = df.iloc[0, -1] if pd.notna(df.iloc[0, -1]) else 0
            last_val = df.iloc[-1, -1] if pd.notna(df.iloc[-1, -1]) else 0
            if first_val > 0:
                change = ((last_val - first_val) / first_val) * 100
                trend = "increased" if change > 0 else "decreased"
                return f"**{title}: {trend} by {abs(change):.1f}% over the period**"

    # Default: row count summary
    return f"**Found {len(df):,} results for {title}**"


def render_chart(df, query_info):
    """Render an Altair chart based on query results (Story 1.4, 1.9).

    Supports optional visualization config for explicit control:
        "visualization": {
            "x": "column_name",      # x-axis column
            "y": "column_name",      # y-axis column
            "color": "column_name",  # optional color grouping
            "type": "bar|line"       # chart type (default: auto-detect)
        }

    Falls back to auto-detection if no config provided.
    """
    if df.empty or len(df.columns) < 2:
        return None

    # Get visualization config or use empty dict for auto-detection
    viz_config = query_info.get('visualization', {})

    # Determine columns - use config or auto-detect
    x_col = viz_config.get('x', df.columns[0])
    y_col = viz_config.get('y', df.columns[-1] if len(df.columns) > 1 else df.columns[0])
    color_col = viz_config.get('color')
    chart_type = viz_config.get('type')  # bar, line, or None for auto

    # Auto-detect color if not specified and we have 3+ columns
    if color_col is None and len(df.columns) >= 3:
        potential_color = df.columns[1]
        if df[potential_color].nunique() <= 10:
            color_col = potential_color

    # Auto-detect chart type if not specified
    if chart_type is None:
        is_temporal = "year" in x_col.lower() or "date" in x_col.lower()
        chart_type = "line" if is_temporal and len(df) > 1 else "bar"

    try:
        color_encoding = (
            alt.Color(f"{color_col}:N", scale=alt.Scale(range=COLOR_PALETTE))
            if color_col else alt.value(COLOR_PRIMARY)
        )

        if chart_type == "line":
            # Line chart for time series
            chart = alt.Chart(df).mark_line(point=True).encode(
                x=alt.X(f"{x_col}:O", title=x_col.replace("_", " ").title()),
                y=alt.Y(f"{y_col}:Q", title=y_col.replace("_", " ").title()),
                color=color_encoding,
                tooltip=list(df.columns)
            ).properties(height=400)
        else:
            # Bar chart for categorical data
            chart = alt.Chart(df.head(20)).mark_bar().encode(
                x=alt.X(f"{x_col}:N", title=x_col.replace("_", " ").title(), sort="-y"),
                y=alt.Y(f"{y_col}:Q", title=y_col.replace("_", " ").title()),
                color=color_encoding,
                tooltip=list(df.columns)
            ).properties(height=400)

        return chart
    except Exception:
        return None


def render_metrics(df, query_info):
    """Render metric cards with delta indicators (Story 1.4)."""
    if df.empty:
        return

    # For single-row metric results, display as metric cards
    if len(df) <= 5 and len(df.columns) == 2:
        cols = st.columns(len(df))
        for i, (_, row) in enumerate(df.iterrows()):
            with cols[i]:
                label = str(row.iloc[0])
                value = row.iloc[1]
                if isinstance(value, (int, float)):
                    st.metric(label=label, value=f"{value:,.0f}")
                else:
                    st.metric(label=label, value=str(value))


def get_contextual_spinner_message(query_info):
    """Generate contextual spinner message based on query (Story 1.3)."""
    category = query_info.get("category", "")
    title = query_info.get("title", "")

    messages = {
        "Competitors": f"Finding competitive intelligence...",
        "Trends": f"Analyzing patent trends...",
        "Regional": f"Gathering regional data...",
        "Technology": f"Scanning technology landscape...",
    }
    return messages.get(category, f"Running {title}...")


# Popular queries for "Common Questions" section (AC #3)
# Selection criteria: One query per category for balanced representation
# - Q06: Competitors (Country Patent Activity)
# - Q07: Trends (Green Technology Trends)
# - Q08: Technology (Most Active Technology Fields)
# - Q11: Competitors (Top Patent Applicants)
# - Q15: Regional (German States - Medical Tech)
COMMON_QUESTIONS = ["Q06", "Q07", "Q08", "Q11", "Q15"]


def render_landing_page():
    """Render the landing page with search, filters, and query list (Stories 1.1, 2.1, 2.2).

    Displays:
    - Title with search box
    - Category pills for filtering
    - Stakeholder tag filters
    - Favorites section (if any)
    - Common Questions section with popular queries
    - Full query list filtered by search, category, and stakeholders
    """
    all_queries = get_all_queries()

    # Header row with title and search (Story 2.1)
    col_title, col_search = st.columns([2, 1])
    with col_title:
        st.header("What do you want to know?")
    with col_search:
        search_term = st.text_input(
            "Search",
            value=st.session_state.get('search_term', ''),
            placeholder="Search queries...",
            label_visibility="collapsed",
            key="search_input"
        )
        st.session_state['search_term'] = search_term

    # Action buttons for advanced features (Stories 3.1, 4.1)
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🤖 AI Query Builder", use_container_width=True):
            go_to_ai_builder()
    with col3:
        if st.button("📝 Contribute Query", use_container_width=True):
            go_to_contribute()

    ''  # Spacing

    # Category pills (AC #1, #2)
    selected_category = st.pills(
        "Categories",
        options=CATEGORIES,
        default=st.session_state.get('selected_category'),
        selection_mode="single",
        key="category_pills"
    )

    # Update session state if category changed
    if selected_category != st.session_state.get('selected_category'):
        st.session_state['selected_category'] = selected_category

    # Stakeholder filter pills (Story 2.1)
    selected_stakeholders = st.pills(
        "Stakeholders",
        options=STAKEHOLDER_TAGS,
        default=st.session_state.get('selected_stakeholders', []),
        selection_mode="multi",
        key="stakeholder_pills"
    )
    st.session_state['selected_stakeholders'] = selected_stakeholders if selected_stakeholders else []

    ''  # Spacing

    # Show active filter summary and clear button
    active_filters = []
    if search_term:
        active_filters.append(f'"{search_term}"')
    if selected_category:
        active_filters.append(selected_category)
    if selected_stakeholders:
        active_filters.extend(selected_stakeholders)

    if active_filters:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.caption(f"Filtering by: {', '.join(active_filters)}")
        with col2:
            if st.button("Clear filters", type="secondary", use_container_width=True):
                st.session_state['search_term'] = ''
                st.session_state['selected_category'] = None
                st.session_state['selected_stakeholders'] = []
                st.rerun()

    # Favorites section (Story 4.4)
    favorites = st.session_state.get('favorites', [])
    if favorites:
        st.subheader("⭐ My Saved Queries")
        fav_cols = st.columns(min(len(favorites), 3))
        for i, fav in enumerate(favorites[:3]):
            with fav_cols[i % 3]:
                if st.button(f"⭐ {fav.get('name', 'Saved Query')}", key=f"fav_{i}", use_container_width=True):
                    # Load favorite query
                    st.session_state['selected_query'] = fav.get('id')
                    st.session_state['current_page'] = 'detail'
                    st.rerun()
        if len(favorites) > 3:
            st.caption(f"+{len(favorites) - 3} more saved queries")
        st.divider()

    # Common Questions section (AC #3) - only show if no active filters
    if not search_term and not selected_category and not selected_stakeholders:
        st.subheader("Common Questions")

        cols = st.columns(len(COMMON_QUESTIONS))
        for i, query_id in enumerate(COMMON_QUESTIONS):
            if query_id in all_queries:
                query_info = all_queries[query_id]
                with cols[i]:
                    if st.button(
                        query_info['title'],
                        key=f"common_{query_id}",
                        use_container_width=True
                    ):
                        go_to_detail(query_id)

        ''  # Spacing
        st.divider()

    # Full query list with filtering (Stories 2.1, 2.2)
    render_query_list(search_term, selected_category, selected_stakeholders)


def render_query_list(search_term: str = None, category_filter: str = None,
                      stakeholder_filter: list = None):
    """Render query list with enhanced cards and filtering (Stories 2.1, 2.2).

    Args:
        search_term: Text search filter
        category_filter: Category name to filter by
        stakeholder_filter: List of stakeholder tags to filter by
    """
    all_queries = get_all_queries()

    # Apply filters
    filtered_queries = filter_queries(
        all_queries,
        search_term=search_term,
        category=category_filter,
        stakeholders=stakeholder_filter
    )

    # Handle empty results (Story 2.1 AC #3)
    if not filtered_queries:
        st.info("No queries match your search criteria.")
        st.markdown("**Suggestions:**")
        st.markdown("- Try different keywords")
        st.markdown("- Remove some filters")
        st.markdown("- Check spelling")
        return

    # Show result count
    st.caption(f"Showing {len(filtered_queries)} queries")

    # Display enhanced query cards (Story 2.2)
    for query_id, query_info in filtered_queries.items():
        with st.container(border=True):
            # Query card layout
            col1, col2 = st.columns([4, 1])

            with col1:
                # Title as clickable button
                if st.button(
                    f"**{query_id}:** {query_info['title']}",
                    key=f"query_{query_id}",
                    use_container_width=True
                ):
                    go_to_detail(query_id)

                # Description snippet
                description = query_info.get('description', '')
                if len(description) > 120:
                    description = description[:117] + "..."
                st.caption(description)

                # Tags as colored pills
                tags_html = render_tags_inline(query_info.get('tags', []))
                st.markdown(tags_html, unsafe_allow_html=True)

            with col2:
                # Estimated time and category
                est_time = query_info.get('estimated_seconds_cached', 5)
                st.metric("", f"~{format_time(est_time)}", label_visibility="collapsed")
                st.caption(query_info.get('category', ''))


def render_detail_page(query_id: str):
    """Render detail page for a specific query (Stories 1.1, 1.2, 2.2, 5.1).

    Displays:
    - Back button to return to landing page
    - Parameter block with Time → Geography → Technology → Action (Story 1.2)
    - Query title, description, and metadata (Story 2.2)
    - Query execution and results
    - Take to TIP button (Story 5.1)

    Args:
        query_id: The ID of the query to display (e.g., 'Q01')
    """
    all_queries = get_all_queries()

    # Back button (AC #4, #5)
    if st.button("← Back to Questions", key="back_to_landing"):
        go_to_landing()
        return  # Exit early since we're navigating

    # Get query info first to check validity
    if query_id not in all_queries:
        st.error(f"Query '{query_id}' not found.")
        return

    query_info = all_queries[query_id]

    # Header with ID and title
    st.header(f"{query_id}: {query_info['title']}")

    # Tags as pills
    tag_colors = {"PATLIB": "#1f77b4", "BUSINESS": "#2ca02c", "UNIVERSITY": "#9467bd"}
    tags_html = " ".join([
        f'<span style="background-color: {tag_colors.get(t, "#666")}; '
        f'color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.85em; margin-right: 6px;">{t}</span>'
        for t in query_info.get("tags", [])
    ])
    st.markdown(tags_html, unsafe_allow_html=True)
    st.markdown("")

    # Query description
    st.markdown(f"**{query_info.get('description', '')}**")

    ''  # Spacing

    # Parameter block - use query-specific parameters (Story 1.8)
    collected_params, run_clicked = render_query_parameters(query_id)

    # Extract common params for display and backwards compatibility
    year_start = collected_params.get('year_start', DEFAULT_YEAR_START)
    year_end = collected_params.get('year_end', DEFAULT_YEAR_END)
    jurisdictions = collected_params.get('jurisdictions', DEFAULT_JURISDICTIONS)
    tech_field = collected_params.get('tech_field')

    ''  # Spacing

    # Show explanation in an expander
    if "explanation" in query_info:
        with st.expander("Details", expanded=False):
            st.markdown(query_info["explanation"])

            if "key_outputs" in query_info:
                st.markdown("**Key Outputs:**")
                for output in query_info["key_outputs"]:
                    st.markdown(f"- {output}")

    # Show estimated time
    estimated_cached = query_info.get("estimated_seconds_cached", 0)
    estimated_first = query_info.get("estimated_seconds_first_run", estimated_cached)
    if estimated_first > 0:
        if estimated_first != estimated_cached:
            st.caption(f"Estimated: ~{format_time(estimated_cached)} (cached) / ~{format_time(estimated_first)} (first run)")
        else:
            st.caption(f"Estimated: ~{format_time(estimated_cached)}")

    # Show the SQL query with parameter substitution (Story 1.6)
    with st.expander("View SQL Query", expanded=False):
        # Display SQL with current parameter values substituted for clarity
        display_sql = query_info["sql"]
        # Build parameter context from collected params
        params_config = query_info.get('parameters', {})
        if params_config:
            param_parts = []
            if 'year_range' in params_config:
                param_parts.append(f"Years {year_start}-{year_end}")
            if 'jurisdictions' in params_config:
                param_parts.append(f"Offices: {', '.join(jurisdictions) if jurisdictions else 'None'}")
            if 'tech_field' in params_config:
                param_parts.append(f"Tech Field: {tech_field or 'All'}")
            param_context = " | ".join(param_parts) if param_parts else "No parameters"
        else:
            param_context = "No configurable parameters"
        st.caption(f"Parameters: {param_context}")
        st.code(display_sql.strip(), language="sql")

    # Methodology note if available (Story 1.6)
    if "methodology" in query_info:
        with st.expander("Methodology", expanded=False):
            st.markdown(query_info["methodology"])

    st.divider()

    # Execute when Run Analysis clicked (from parameter block)
    if run_clicked:
        # Get or create client
        client = get_bigquery_client()
        if client is None:
            st.error("Could not connect to BigQuery.")
            return

        # Contextual spinner message (Story 1.3)
        spinner_msg = get_contextual_spinner_message(query_info)
        estimated_seconds = query_info.get("estimated_seconds_cached", 1)

        with st.spinner(f"{spinner_msg} (~{format_time(estimated_seconds)})"):
            try:
                # Use parameterized query if sql_template is available (Story 1.7, 1.8)
                if "sql_template" in query_info:
                    # Build params from collected values - only include what the query uses
                    params = {}
                    params_config = query_info.get('parameters', {})
                    if 'year_range' in params_config:
                        params['year_start'] = year_start
                        params['year_end'] = year_end
                    if 'jurisdictions' in params_config:
                        params['jurisdictions'] = jurisdictions if jurisdictions else None
                    if 'tech_field' in params_config:
                        params['tech_field'] = tech_field
                    # Query-specific parameters (Story 1.8)
                    if 'tech_sector' in params_config:
                        params['tech_sector'] = collected_params.get('tech_sector')
                    if 'applicant_name' in params_config:
                        params['applicant_name'] = collected_params.get('applicant_name', '')
                    if 'competitors' in params_config:
                        params['competitors'] = collected_params.get('competitors')
                    if 'ipc_class' in params_config:
                        params['ipc_class'] = collected_params.get('ipc_class', '')
                    df, execution_time = run_parameterized_query(client, query_info["sql_template"], params)
                else:
                    # Fallback to static SQL for queries not yet converted
                    df, execution_time = run_query(client, query_info["sql"])

                # Empty results handling (Story 1.3)
                if df.empty:
                    st.warning("No results found for your query.")
                    st.info("**Suggestions:** Try broadening the year range or selecting different jurisdictions.")
                    return

                # Insight headline (Story 1.4) - appears FIRST
                headline = generate_insight_headline(df, query_info)
                if headline:
                    st.markdown(headline)
                    ''  # Spacing

                # Execution metrics row
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Results", f"{len(df):,} rows")
                with col2:
                    st.metric("Execution", format_time(execution_time))
                with col3:
                    if estimated_seconds > 0:
                        diff = execution_time - estimated_seconds
                        delta_str = f"{'+' if diff > 0 else ''}{format_time(abs(diff))}"
                        st.metric("vs. Est.", delta_str,
                                 delta=f"{'slower' if diff > 0 else 'faster'}",
                                 delta_color="inverse")

                ''  # Spacing

                # Chart visualization (Story 1.4)
                chart = render_chart(df, query_info)
                if chart:
                    st.altair_chart(chart, use_container_width=True)

                # Metric cards for small datasets (Story 1.4)
                if len(df) <= 5 and len(df.columns) == 2:
                    render_metrics(df, query_info)

                # Data table in expander (Story 1.3)
                with st.expander("View Data Table", expanded=False):
                    st.dataframe(df, use_container_width=True, height=400)

                st.divider()

                # Download buttons (Story 1.5)
                col1, col2 = st.columns(2)
                timestamp = time.strftime("%Y%m%d")
                base_filename = f"{query_id}_{query_info['title'].lower().replace(' ', '_').replace('-', '_')}"

                with col1:
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Data (CSV)",
                        data=csv,
                        file_name=f"{base_filename}_{timestamp}.csv",
                        mime="text/csv",
                        key="download_csv"
                    )

                with col2:
                    # Chart download as HTML (Altair interactive)
                    if chart:
                        chart_html = chart.to_html()
                        st.download_button(
                            label="📊 Download Chart (HTML)",
                            data=chart_html,
                            file_name=f"{base_filename}_{timestamp}_chart.html",
                            mime="text/html",
                            key="download_chart"
                        )

                # Take to TIP button (Story 5.1)
                st.divider()
                render_tip_panel(query_info, collected_params)

            except Exception as e:
                st.error(f"Error: {str(e)}")

# Page config
st.set_page_config(
    page_title="PATSTAT Explorer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 PATSTAT Explorer")
st.caption("Patent Analysis Platform - EPO PATSTAT 2025 Autumn on BigQuery by mtc")


@st.cache_resource
def get_bigquery_client():
    """Create and cache BigQuery client."""
    project = os.getenv("BIGQUERY_PROJECT", "patstat-mtc")

    # Check for Streamlit Cloud secrets first
    try:
        if "gcp_service_account" in st.secrets:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"]
            )
            return bigquery.Client(credentials=credentials, project=project)
    except FileNotFoundError:
        pass  # No secrets.toml file, try other methods

    # Check for service account JSON in environment (local dev or Streamlit Cloud)
    service_account_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    if service_account_json:
        credentials = service_account.Credentials.from_service_account_info(
            json.loads(service_account_json)
        )
        return bigquery.Client(credentials=credentials, project=project)

    # Fall back to Application Default Credentials
    return bigquery.Client(project=project)


def run_query(client, query):
    """Execute a query and return results as DataFrame with execution time."""
    project = os.getenv("BIGQUERY_PROJECT", "patstat-mtc")
    dataset = os.getenv("BIGQUERY_DATASET", "patstat")

    # Set default dataset so queries don't need fully qualified table names
    job_config = bigquery.QueryJobConfig(
        default_dataset=f"{project}.{dataset}"
    )

    start_time = time.time()
    result = client.query(query, job_config=job_config).to_dataframe()
    execution_time = time.time() - start_time
    return result, execution_time


def run_parameterized_query(client, sql_template: str, params: dict):
    """Execute a parameterized query with BigQuery query parameters.

    Args:
        client: BigQuery client
        sql_template: SQL with @param placeholders
        params: Dict with parameter values:
            - year_start: int
            - year_end: int
            - jurisdictions: list[str]
            - tech_field: int or None
            - tech_sector: str or None (Q08)
            - applicant_name: str or None (Q11)
            - competitors: list[str] or None (Q12)
            - ipc_class: str or None (Q14, Q15, Q16)

    Returns:
        tuple: (DataFrame, execution_time in seconds)
    """
    project = os.getenv("BIGQUERY_PROJECT", "patstat-mtc")
    dataset = os.getenv("BIGQUERY_DATASET", "patstat")

    # Build query parameters
    query_params = []

    # Common parameters
    if "year_start" in params and params["year_start"] is not None:
        query_params.append(bigquery.ScalarQueryParameter("year_start", "INT64", params["year_start"]))

    if "year_end" in params and params["year_end"] is not None:
        query_params.append(bigquery.ScalarQueryParameter("year_end", "INT64", params["year_end"]))

    if "jurisdictions" in params and params["jurisdictions"]:
        query_params.append(bigquery.ArrayQueryParameter("jurisdictions", "STRING", params["jurisdictions"]))

    if "tech_field" in params and params["tech_field"] is not None:
        query_params.append(bigquery.ScalarQueryParameter("tech_field", "INT64", params["tech_field"]))

    # Query-specific parameters (Story 1.8)
    if "tech_sector" in params and params["tech_sector"] is not None:
        query_params.append(bigquery.ScalarQueryParameter("tech_sector", "STRING", params["tech_sector"]))

    if "applicant_name" in params and params["applicant_name"] is not None:
        query_params.append(bigquery.ScalarQueryParameter("applicant_name", "STRING", params["applicant_name"]))

    if "competitors" in params and params["competitors"]:
        query_params.append(bigquery.ArrayQueryParameter("competitors", "STRING", params["competitors"]))

    if "ipc_class" in params and params["ipc_class"] is not None:
        query_params.append(bigquery.ScalarQueryParameter("ipc_class", "STRING", params["ipc_class"]))

    # Set job config with parameters
    job_config = bigquery.QueryJobConfig(
        default_dataset=f"{project}.{dataset}",
        query_parameters=query_params
    )

    start_time = time.time()
    result = client.query(sql_template, job_config=job_config).to_dataframe()
    execution_time = time.time() - start_time
    return result, execution_time


def format_time(seconds: float) -> str:
    """Format seconds into human-readable string."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"


# =============================================================================
# TIP INTEGRATION (Stories 5.1, 5.2)
# =============================================================================

TIP_PLATFORM_URL = "https://tip.epo.org"
GITHUB_REPO_URL = "https://github.com/mtc-20/patstat-explorer"


def format_sql_for_tip(sql: str, params: dict) -> str:
    """Format SQL for use in TIP by substituting actual parameter values.

    TIP uses PatstatClient which executes raw SQL directly, so we need to
    replace @param placeholders with actual values.
    """
    import re

    formatted_sql = sql

    # Remove backticks from table names (TIP doesn't need them)
    formatted_sql = re.sub(r'`([^`]+)`', r'\1', formatted_sql)

    # Substitute year parameters
    if params.get('year_start') is not None:
        formatted_sql = formatted_sql.replace('@year_start', str(params['year_start']))
    if params.get('year_end') is not None:
        formatted_sql = formatted_sql.replace('@year_end', str(params['year_end']))

    # Substitute jurisdictions array - convert UNNEST(@jurisdictions) to IN ('EP', 'US', 'DE')
    if params.get('jurisdictions'):
        jurisdiction_list = ", ".join([f"'{j}'" for j in params['jurisdictions']])
        # Replace UNNEST(@jurisdictions) pattern with IN clause
        formatted_sql = re.sub(
            r'IN\s+UNNEST\s*\(\s*@jurisdictions\s*\)',
            f"IN ({jurisdiction_list})",
            formatted_sql,
            flags=re.IGNORECASE
        )

    # Substitute tech_field (integer)
    if params.get('tech_field') is not None:
        formatted_sql = formatted_sql.replace('@tech_field', str(params['tech_field']))

    # Substitute tech_sector (string)
    if params.get('tech_sector') is not None:
        formatted_sql = formatted_sql.replace('@tech_sector', f"'{params['tech_sector']}'")

    # Substitute applicant_name (string)
    if params.get('applicant_name') is not None:
        # Escape single quotes in the name
        safe_name = params['applicant_name'].replace("'", "''")
        formatted_sql = formatted_sql.replace('@applicant_name', f"'{safe_name}'")

    # Substitute ipc_class (string)
    if params.get('ipc_class') is not None:
        formatted_sql = formatted_sql.replace('@ipc_class', f"'{params['ipc_class']}'")

    # Substitute competitors array
    if params.get('competitors'):
        competitors_list = ", ".join([f"'{c}'" for c in params['competitors']])
        formatted_sql = re.sub(
            r'UNNEST\s*\(\s*@competitors\s*\)',
            f"({competitors_list})",
            formatted_sql,
            flags=re.IGNORECASE
        )

    # Clean up whitespace
    formatted_sql = formatted_sql.strip()

    return formatted_sql


def render_tip_panel(query_info: dict, collected_params: dict):
    """Render the Take to TIP panel (Stories 5.1, 5.2).

    Args:
        query_info: Query metadata dict
        collected_params: All collected parameters from the UI
    """
    with st.expander("🎓 Take to TIP - Use in EPO's Jupyter Environment", expanded=False):
        st.markdown("""
        **TIP (Technology & Innovation Portal)** lets you run this query in EPO's
        Jupyter environment with full PATSTAT access.
        """)

        # Get SQL template and substitute parameters
        sql = query_info.get('sql_template', query_info.get('sql', ''))
        tip_sql = format_sql_for_tip(sql, collected_params)

        st.markdown("**📋 Ready-to-run SQL Query:**")
        st.code(tip_sql, language="sql")

        # Python code template for TIP
        jupyter_code = f'''from epo.tipdata.patstat import PatstatClient
import pandas as pd
import time

# Connect to PATSTAT
patstat = PatstatClient(env='PROD')

def timed_query(query):
    """Execute query and return DataFrame with timing."""
    start = time.time()
    res = patstat.sql_query(query, use_legacy_sql=False)
    print(f"Query took {{time.time() - start:.2f}}s ({{len(res)}} rows)")
    return pd.DataFrame(res)

# Run the query
df = timed_query("""
{tip_sql}
""")

# Display results
df'''

        st.markdown("**📄 Complete TIP Notebook Code:**")
        st.code(jupyter_code, language="python")

        # Quick start instructions
        with st.expander("📝 How to use in TIP"):
            st.markdown("""
            1. **Login** to [TIP](https://tip.epo.org) with your EPO account
            2. **Open** JupyterLab from the TIP dashboard
            3. **Create** a new Python 3 notebook
            4. **Copy** the code above into a cell
            5. **Run** with Shift+Enter

            **Tips:**
            - First query may take longer (cold start)
            - Add `LIMIT 100` for testing large queries
            - Results are returned as a list of dicts, converted to DataFrame
            """)

        # Link to TIP
        st.link_button("🎓 Open TIP Platform", TIP_PLATFORM_URL)


def render_footer():
    """Render app footer with GitHub and TIP links (Story 5.3)."""
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            f"""
            <div style="text-align: center; padding: 10px; color: #666;">
                <a href="{GITHUB_REPO_URL}" target="_blank" style="text-decoration: none; color: #1E3A5F;">
                    📁 View on GitHub
                </a>
                &nbsp;|&nbsp;
                <a href="{TIP_PLATFORM_URL}" target="_blank" style="text-decoration: none; color: #1E3A5F;">
                    🎓 EPO TIP Platform
                </a>
                <br><br>
                <span style="font-size: 0.8em;">
                    PATSTAT Explorer - Built for the PATLIB community
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )


# =============================================================================
# CONTRIBUTION SYSTEM (Stories 3.1-3.4)
# =============================================================================

def validate_contribution_step1() -> list:
    """Validate basic query information (Story 3.3)."""
    contrib = st.session_state.get('contribution', {})
    errors = []
    if not contrib.get('title', '').strip():
        errors.append("Title is required")
    if not contrib.get('description', '').strip():
        errors.append("Description is required")
    if not contrib.get('sql', '').strip():
        errors.append("SQL query is required")
    if not contrib.get('tags', []):
        errors.append("Select at least one stakeholder tag")
    if not contrib.get('category', ''):
        errors.append("Select a category")
    return errors


def detect_sql_parameters(sql: str) -> list:
    """Extract @parameter names from SQL (Story 3.2)."""
    import re
    pattern = r'@(\w+)'
    return list(set(re.findall(pattern, sql)))


def submit_contribution(contribution: dict) -> str:
    """Add contribution to queries and return new query ID (Story 3.4)."""
    # Generate next available ID
    existing_ids = [int(qid[1:]) for qid in QUERIES.keys()
                    if qid.startswith('Q') and qid[1:].isdigit()]
    next_num = max(existing_ids, default=0) + 1
    new_id = f"Q{next_num:02d}"

    # Format as QUERIES entry
    new_query = {
        'title': contribution['title'],
        'tags': contribution['tags'],
        'category': contribution['category'],
        'description': contribution['description'],
        'explanation': contribution.get('explanation', ''),
        'key_outputs': contribution.get('key_outputs', []),
        'estimated_seconds_first_run': 5,
        'estimated_seconds_cached': 2,
        'sql': contribution['sql'],
        'contributed': True,
    }

    # Store in session state (persists during session)
    if 'contributed_queries' not in st.session_state:
        st.session_state['contributed_queries'] = {}
    st.session_state['contributed_queries'][new_id] = new_query

    return new_id


def render_contribute_page():
    """Render the contribution flow (Stories 3.1-3.4)."""
    if st.button("← Back to Questions", key="back_from_contribute"):
        go_to_landing()
        return

    st.header("Contribute a Query")
    st.markdown("Share your SQL expertise with 300 PATLIB centres!")

    # Contribution guidelines
    with st.expander("📋 Contribution Guidelines"):
        st.markdown("""
        **What makes a good query:**
        - Clear question-style title (e.g., "Who are the top filers in X?")
        - Brief description explaining what the query reveals
        - SQL that executes in under 15 seconds
        - Appropriate stakeholder tags

        **SQL Best Practices:**
        - Use BigQuery syntax
        - Include LIMIT for large result sets
        - Use `@parameter` syntax for dynamic values
        - Test your query before submitting
        """)

    step = st.session_state.get('contribution_step', 1)
    contrib = st.session_state.get('contribution', {})

    if step == 1:
        # Step 1: Basic info
        st.subheader("Step 1: Query Details")

        contrib['title'] = st.text_input(
            "Title (question format)",
            value=contrib.get('title', ''),
            placeholder="Who are the top patent filers in...?"
        )

        contrib['description'] = st.text_area(
            "Description",
            value=contrib.get('description', ''),
            placeholder="Briefly explain what this query reveals...",
            height=100
        )

        contrib['category'] = st.selectbox(
            "Category",
            options=[""] + CATEGORIES,
            index=CATEGORIES.index(contrib['category']) + 1 if contrib.get('category') in CATEGORIES else 0
        )

        contrib['tags'] = st.multiselect(
            "Stakeholder Tags",
            options=STAKEHOLDER_TAGS,
            default=contrib.get('tags', [])
        )

        contrib['sql'] = st.text_area(
            "SQL Query",
            value=contrib.get('sql', ''),
            placeholder="SELECT ...\nFROM tls201_appln a\nWHERE ...",
            height=200
        )

        contrib['explanation'] = st.text_area(
            "Detailed Explanation (optional)",
            value=contrib.get('explanation', ''),
            placeholder="Additional context about the query...",
            height=100
        )

        st.session_state['contribution'] = contrib

        # Detect parameters
        if contrib.get('sql'):
            params = detect_sql_parameters(contrib['sql'])
            if params:
                st.info(f"Detected parameters: {', '.join(['@' + p for p in params])}")

        col1, col2 = st.columns(2)
        with col2:
            if st.button("Preview Query →", type="primary"):
                errors = validate_contribution_step1()
                if errors:
                    for error in errors:
                        st.error(error)
                else:
                    st.session_state['contribution_step'] = 2
                    st.rerun()

    elif step == 2:
        # Step 2: Preview
        st.subheader("Step 2: Preview Your Query")

        st.markdown("**Query Card Preview:**")
        with st.container(border=True):
            st.markdown(f"**Q??: {contrib['title']}**")
            st.caption(contrib['description'])
            tags_html = render_tags_inline(contrib.get('tags', []))
            st.markdown(tags_html, unsafe_allow_html=True)

        st.markdown("**SQL:**")
        st.code(contrib['sql'], language="sql")

        # Test query button
        if st.button("🧪 Test Query"):
            client = get_bigquery_client()
            if client:
                with st.spinner("Testing query..."):
                    try:
                        # Add LIMIT if not present for safety
                        test_sql = contrib['sql']
                        if 'LIMIT' not in test_sql.upper():
                            test_sql = test_sql.rstrip().rstrip(';') + ' LIMIT 100'
                        df, exec_time = run_query(client, test_sql)
                        st.success(f"Query executed successfully in {format_time(exec_time)} - {len(df)} rows")
                        with st.expander("View Results"):
                            st.dataframe(df.head(20))
                    except Exception as e:
                        st.error(f"Query error: {str(e)}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("← Edit"):
                st.session_state['contribution_step'] = 1
                st.rerun()
        with col3:
            if st.button("Submit Query →", type="primary"):
                new_id = submit_contribution(contrib)
                st.session_state['contribution_step'] = 3
                st.session_state['submitted_query_id'] = new_id
                st.rerun()

    elif step == 3:
        # Step 3: Confirmation
        new_id = st.session_state.get('submitted_query_id', 'Q??')
        st.success("🎉 Query Submitted Successfully!")
        st.markdown(f"""
        Your query has been added to the library:

        **Query ID:** {new_id}
        **Title:** {contrib['title']}
        **Category:** {contrib['category']}
        """)

        st.info("Note: Your query is available for this session. Persistent storage coming in a future update.")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("View Your Query"):
                go_to_detail(new_id)
        with col2:
            if st.button("Contribute Another"):
                st.session_state['contribution'] = {}
                st.session_state['contribution_step'] = 1
                st.rerun()


# =============================================================================
# AI QUERY BUILDER (Stories 4.1-4.4)
# =============================================================================

def get_claude_client():
    """Get Claude API client if configured (Story 4.1).

    Checks st.secrets first (Cloud), then os.getenv (Local).
    """
    try:
        import anthropic
        
        # 1. Try Streamlit Secrets (Cloud / .streamlit/secrets.toml)
        try:
            api_key = st.secrets.get("ANTHROPIC_API_KEY")
        except (FileNotFoundError, AttributeError):
            api_key = None
            
        # 2. Try Environment Variable (Local .env)
        if not api_key:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            
        if api_key:
            return anthropic.Anthropic(api_key=api_key)
            
    except ImportError:
        pass
    except Exception as e:
        # Catch other initialization errors but don't crash
        print(f"Error initializing Claude client: {e}")
        pass
        
    return None


def is_ai_available() -> bool:
    """Check if AI features are available."""
    return get_claude_client() is not None


PATSTAT_SYSTEM_PROMPT = """You are an expert SQL query writer for EPO PATSTAT on BigQuery.

You have access to these main tables:
- tls201_appln: Patent applications (main table) - columns: appln_id, appln_auth, appln_filing_year, granted, docdb_family_id, docdb_family_size
- tls206_person: Applicants and inventors - columns: person_id, person_name, person_ctry_code, psn_sector, doc_std_name
- tls207_pers_appln: Links persons to applications - columns: person_id, appln_id, applt_seq_nr, invt_seq_nr
- tls209_appln_ipc: IPC classifications - columns: appln_id, ipc_class_symbol
- tls224_appln_cpc: CPC classifications - columns: appln_id, cpc_class_symbol
- tls211_pat_publn: Publications - columns: pat_publn_id, appln_id, publn_date, publn_first_grant
- tls212_citation: Citation data - columns: pat_publn_id, cited_pat_publn_id
- tls230_appln_techn_field: WIPO technology fields - columns: appln_id, techn_field_nr, weight
- tls901_techn_field_ipc: Technology field definitions - columns: techn_field_nr, techn_field, techn_sector
- tls801_country: Country codes - columns: ctry_code, st3_name

Generate BigQuery-compatible SQL that:
1. Uses proper table names with backticks
2. Includes appropriate JOINs
3. Has sensible LIMIT (default 50)
4. Handles NULLs appropriately
5. Returns results within 15 seconds typically

Respond in this exact format:
EXPLANATION:
[2-3 sentences explaining what the query does in plain language]

SQL:
```sql
[Your SQL query here]
```

NOTES:
[Any warnings or suggestions, or "None" if the query is straightforward]"""


def generate_sql_query(user_request: str) -> dict:
    """Generate SQL from natural language using Claude (Story 4.2)."""
    client = get_claude_client()
    if not client:
        return {'success': False, 'error': 'AI not configured'}

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=PATSTAT_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Generate a BigQuery SQL query for this request:\n\n{user_request}"
            }]
        )

        return parse_ai_response(response.content[0].text)
    except Exception as e:
        return {'success': False, 'error': str(e)}


def parse_ai_response(response_text: str) -> dict:
    """Parse structured response from Claude (Story 4.2)."""
    result = {
        'explanation': '',
        'sql': '',
        'notes': '',
        'success': True,
        'error': None
    }

    try:
        # Extract explanation
        if 'EXPLANATION:' in response_text:
            explanation_start = response_text.index('EXPLANATION:') + len('EXPLANATION:')
            explanation_end = response_text.index('SQL:') if 'SQL:' in response_text else len(response_text)
            result['explanation'] = response_text[explanation_start:explanation_end].strip()

        # Extract SQL
        if '```sql' in response_text:
            sql_start = response_text.index('```sql') + 6
            sql_end = response_text.index('```', sql_start)
            result['sql'] = response_text[sql_start:sql_end].strip()
        elif '```' in response_text:
            sql_start = response_text.index('```') + 3
            sql_end = response_text.index('```', sql_start)
            result['sql'] = response_text[sql_start:sql_end].strip()

        # Extract notes
        if 'NOTES:' in response_text:
            notes_start = response_text.index('NOTES:') + len('NOTES:')
            result['notes'] = response_text[notes_start:].strip()

        if not result['sql']:
            result['success'] = False
            result['error'] = 'Could not extract SQL from response'

    except Exception as e:
        result['success'] = False
        result['error'] = f"Could not parse AI response: {str(e)}"

    return result


def render_ai_builder_page():
    """Render the AI Query Builder (Stories 4.1-4.4)."""
    if st.button("← Back to Questions", key="back_from_ai"):
        go_to_landing()
        return

    st.header("🤖 AI Query Builder")
    st.markdown("Describe what you want to analyze in plain English. Our AI will generate the SQL query for you.")

    if not is_ai_available():
        st.warning("""
        **AI features not configured**

        To enable AI query generation:
        1. Get an API key from [Anthropic](https://console.anthropic.com)
        2. Set `ANTHROPIC_API_KEY` in your environment or Streamlit secrets
        """)
        return

    # Tips expander
    with st.expander("💡 Tips for better results"):
        st.markdown("""
        **Be specific about:**
        - **Technology**: Use IPC codes if you know them (e.g., "F03D for wind motors") or describe clearly
        - **Geography**: Country codes (DE, US, CN) or full names
        - **Time period**: "Since 2018" or "between 2015 and 2023"
        - **What you want**: "Top 10 companies by patent count", "Filing trend over time"

        **Example requests:**
        - "Who are the main competitors in medical imaging technology in Europe since 2020?"
        - "Show patent filing trends for AI/machine learning in US, CN, and EP over the last 10 years"
        - "Which universities collaborate most with industry on battery research?"
        """)

    # Input area
    ai_request = st.text_area(
        "Describe your analysis need",
        value=st.session_state.get('ai_request', ''),
        placeholder="Show me the top 10 companies filing wind energy patents in Germany since 2018...",
        height=150,
        key="ai_request_input"
    )
    st.session_state['ai_request'] = ai_request

    col1, col2 = st.columns([1, 3])
    with col1:
        generate_clicked = st.button("Generate Query", type="primary", disabled=not ai_request.strip())

    # Generate query
    if generate_clicked and ai_request.strip():
        with st.spinner("🤖 AI is generating your query..."):
            result = generate_sql_query(ai_request)

            if result['success']:
                # Store in session state
                st.session_state['ai_generation'] = result
                # Add to version history
                if 'ai_query_versions' not in st.session_state:
                    st.session_state['ai_query_versions'] = []
                st.session_state['ai_query_versions'].append({
                    'request': ai_request,
                    'result': result,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M')
                })
            else:
                st.error(f"Generation failed: {result['error']}")

    # Display results
    generation = st.session_state.get('ai_generation')
    if generation and generation.get('success'):
        st.divider()
        st.subheader("Generated Query")

        # Explanation
        st.markdown("**📝 What this query does:**")
        st.info(generation.get('explanation', 'No explanation provided'))

        # SQL
        st.markdown("**💻 SQL Query:**")
        st.code(generation['sql'], language="sql")

        # Notes
        if generation.get('notes') and generation['notes'].lower() != 'none':
            st.markdown(f"**⚠️ Notes:** {generation['notes']}")

        # Actions
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🧪 Preview Results"):
                client = get_bigquery_client()
                if client:
                    with st.spinner("Running query..."):
                        try:
                            test_sql = generation['sql']
                            if 'LIMIT' not in test_sql.upper():
                                test_sql = test_sql.rstrip().rstrip(';') + ' LIMIT 100'
                            df, exec_time = run_query(client, test_sql)
                            st.success(f"Executed in {format_time(exec_time)} - {len(df)} rows")

                            # Show insight headline
                            query_info = {'title': 'AI Query', 'category': 'Technology'}
                            headline = generate_insight_headline(df, query_info)
                            if headline:
                                st.markdown(headline)

                            # Show chart
                            chart = render_chart(df, query_info)
                            if chart:
                                st.altair_chart(chart, use_container_width=True)

                            with st.expander("View Data"):
                                st.dataframe(df, use_container_width=True)
                        except Exception as e:
                            st.error(f"Error: {str(e)}")

        with col2:
            if st.button("⭐ Save to Favorites"):
                # Save to favorites
                if 'favorites' not in st.session_state:
                    st.session_state['favorites'] = []
                fav = {
                    'id': f"AI_{len(st.session_state['favorites']) + 1:03d}",
                    'name': ai_request[:50] + "..." if len(ai_request) > 50 else ai_request,
                    'sql': generation['sql'],
                    'explanation': generation.get('explanation', ''),
                    'source': 'ai_generated'
                }
                st.session_state['favorites'].append(fav)
                st.success("Saved to favorites!")

        # Version history
        versions = st.session_state.get('ai_query_versions', [])
        if len(versions) > 1:
            with st.expander(f"📜 Previous Versions ({len(versions) - 1})"):
                for i, v in enumerate(reversed(versions[:-1])):
                    st.markdown(f"**v{len(versions) - i - 1}** - {v['timestamp']}")
                    st.caption(v['request'][:80] + "..." if len(v['request']) > 80 else v['request'])
                    if st.button("Use this version", key=f"use_v{i}"):
                        st.session_state['ai_generation'] = v['result']
                        st.session_state['ai_request'] = v['request']
                        st.rerun()


def main():
    """Main application entry point with session-state based routing (Story 1.1).

    Routes between:
    - Landing page: Category pills + query list + common questions
    - Detail page: Query parameters + execution + results
    - Contribute page: Query contribution flow (Story 3.1)
    - AI Builder page: Natural language query generation (Story 4.1)
    """
    # Initialize session state for navigation
    init_session_state()

    client = get_bigquery_client()

    if client is None:
        st.stop()

    # Route based on current_page session state
    current_page = st.session_state.get('current_page', 'landing')

    if current_page == 'detail':
        query_id = st.session_state.get('selected_query')
        if query_id:
            render_detail_page(query_id)
        else:
            st.session_state['current_page'] = 'landing'
            render_landing_page()
    elif current_page == 'contribute':
        render_contribute_page()
    elif current_page == 'ai_builder':
        render_ai_builder_page()
    else:
        render_landing_page()

    # Footer (Story 5.3)
    render_footer()


if __name__ == "__main__":
    main()
