# PATSTAT Explorer - UI Components
# All Streamlit rendering functions

import time
import streamlit as st
import altair as alt

from .config import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_ACCENT, COLOR_PALETTE,
    DEFAULT_YEAR_START, DEFAULT_YEAR_END, DEFAULT_JURISDICTIONS, DEFAULT_TECH_FIELD,
    YEAR_MIN, YEAR_MAX,
    CATEGORIES, STAKEHOLDER_TAGS, COMMON_QUESTIONS,
    JURISDICTIONS, TECH_FIELDS,
    TIP_PLATFORM_URL, GITHUB_REPO_URL
)
from .utils import format_time, format_sql_for_tip
from .data import (
    get_bigquery_client, run_query, run_parameterized_query,
    get_all_queries, resolve_options
)
from .logic import (
    filter_queries, generate_insight_headline,
    validate_contribution_step1, submit_contribution,
    is_ai_available, generate_sql_query
)


# =============================================================================
# SESSION STATE & NAVIGATION
# =============================================================================

def init_session_state():
    """Initialize session state for page navigation and parameters.

    Sets default values only if keys don't already exist.
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
    """Navigate to landing page, preserving category selection."""
    st.session_state['current_page'] = 'landing'
    st.session_state['selected_query'] = None

    # Reset parameter state to defaults
    st.session_state['year_start'] = DEFAULT_YEAR_START
    st.session_state['year_end'] = DEFAULT_YEAR_END
    st.session_state['jurisdictions'] = DEFAULT_JURISDICTIONS.copy()
    st.session_state['tech_field'] = DEFAULT_TECH_FIELD

    st.rerun()


def go_to_detail(query_id: str):
    """Navigate to detail page for a specific query."""
    all_queries = get_all_queries()
    if query_id not in all_queries:
        return
    st.session_state['current_page'] = 'detail'
    st.session_state['selected_query'] = query_id
    st.rerun()


def go_to_contribute():
    """Navigate to contribute query page."""
    st.session_state['current_page'] = 'contribute'
    st.session_state['contribution_step'] = 1
    st.rerun()


def go_to_ai_builder():
    """Navigate to AI query builder page."""
    st.session_state['current_page'] = 'ai_builder'
    st.rerun()


# =============================================================================
# RENDERING HELPERS
# =============================================================================

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


def render_parameter_block():
    """Render the parameter block with Time -> Geography -> Technology -> Action order."""
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

        with col1:
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
            jurisdictions = st.multiselect(
                "Jurisdictions",
                options=JURISDICTIONS,
                default=st.session_state.get('jurisdictions', DEFAULT_JURISDICTIONS),
                help="Select patent offices to include"
            )
            if not jurisdictions:
                st.warning("Select at least one jurisdiction")

        with col3:
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
            st.write("")
            run_clicked = st.button("Run Analysis", type="primary", use_container_width=True)

    # Update session state
    st.session_state['year_start'] = year_start
    st.session_state['year_end'] = year_end
    st.session_state['jurisdictions'] = jurisdictions
    st.session_state['tech_field'] = tech_field

    return year_start, year_end, jurisdictions, tech_field, run_clicked


def render_single_parameter(name: str, config: dict, key_prefix: str = ""):
    """Render a single parameter control based on its type (Story 1.8)."""
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

    elif param_type == 'year_picker':
        # Two separate year pickers instead of slider - better for wide ranges (1877-present)
        default_start = config.get('default_start', DEFAULT_YEAR_START)
        default_end = config.get('default_end', DEFAULT_YEAR_END)
        col1, col2 = st.columns(2)
        with col1:
            year_start = st.number_input(
                f"{label} (from)",
                min_value=YEAR_MIN,
                max_value=YEAR_MAX,
                value=default_start,
                key=f"{key}_start"
            )
        with col2:
            year_end = st.number_input(
                f"{label} (to)",
                min_value=YEAR_MIN,
                max_value=YEAR_MAX,
                value=default_end,
                key=f"{key}_end"
            )
        return {'year_start': int(year_start), 'year_end': int(year_end)}

    elif param_type == 'multiselect':
        options = resolve_options(config.get('options', []))
        defaults = config.get('defaults', options[:3] if options else [])
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

    if param_type:
        st.warning(f"Unknown parameter type '{param_type}' for {name}")
    return None


def render_query_parameters(query_id: str) -> tuple:
    """Render parameter controls based on query's parameter configuration (Story 1.8)."""
    query = get_all_queries().get(query_id, {})
    params_config = query.get('parameters', {})

    if not params_config:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info("This query has no configurable parameters.")
            with col2:
                st.write("")
                run_clicked = st.button("Run Analysis", type="primary", use_container_width=True)
        return {}, run_clicked

    collected_params = {}
    key_prefix = f"param_{query_id}"

    with st.container(border=True):
        param_count = len(params_config)
        if param_count == 1:
            cols = st.columns([3, 1])
        elif param_count == 2:
            cols = st.columns([2, 2, 1])
        else:
            cols = st.columns([2, 2, 2, 1])

        col_idx = 0
        for param_name, param_def in params_config.items():
            with cols[col_idx % (len(cols) - 1)]:
                value = render_single_parameter(param_name, param_def, key_prefix)

                if param_def.get('type') in ('year_range', 'year_picker'):
                    collected_params['year_start'] = value['year_start']
                    collected_params['year_end'] = value['year_end']
                else:
                    collected_params[param_name] = value
            col_idx += 1

        with cols[-1]:
            st.write("")
            run_clicked = st.button("Run Analysis", type="primary", use_container_width=True)

    return collected_params, run_clicked


def render_chart(df, query_info):
    """Render an Altair chart based on query results (Story 1.4)."""
    if df.empty or len(df.columns) < 2:
        return None

    viz_config = query_info.get('visualization', {})

    # Allow disabling chart with visualization: None
    if viz_config is None:
        return None

    x_col = viz_config.get('x', df.columns[0])
    y_col = viz_config.get('y', df.columns[-1] if len(df.columns) > 1 else df.columns[0])
    color_col = viz_config.get('color')
    chart_type = viz_config.get('type')

    if color_col is None and len(df.columns) >= 3:
        potential_color = df.columns[1]
        if df[potential_color].nunique() <= 10:
            color_col = potential_color

    if chart_type is None:
        is_temporal = "year" in x_col.lower() or "date" in x_col.lower()
        chart_type = "line" if is_temporal and len(df) > 1 else "bar"

    try:
        color_encoding = (
            alt.Color(f"{color_col}:N", scale=alt.Scale(range=COLOR_PALETTE))
            if color_col else alt.value(COLOR_PRIMARY)
        )

        if chart_type == "pie":
            # Pie chart using theta encoding
            chart = alt.Chart(df).mark_arc(innerRadius=50).encode(
                theta=alt.Theta(f"{y_col}:Q"),
                color=alt.Color(f"{x_col}:N", scale=alt.Scale(range=COLOR_PALETTE),
                               legend=alt.Legend(title=x_col.replace("_", " ").title())),
                tooltip=[
                    alt.Tooltip(f"{x_col}:N", title=x_col.replace("_", " ").title()),
                    alt.Tooltip(f"{y_col}:Q", title=y_col.replace("_", " ").title(), format=",")
                ]
            ).properties(height=400)
        elif chart_type == "stacked_bar":
            # Stacked bar chart
            stacked_columns = viz_config.get('stacked_columns')

            if stacked_columns:
                # Transform wide format to long format for stacking
                import pandas as pd
                df_long = df.melt(
                    id_vars=[x_col],
                    value_vars=stacked_columns,
                    var_name='status',
                    value_name='count'
                )
                # Clean up status names (e.g., "not_granted" -> "Not Granted")
                df_long['status'] = df_long['status'].str.replace('_', ' ').str.title()

                chart = alt.Chart(df_long).mark_bar().encode(
                    x=alt.X(f"{x_col}:O", title=x_col.replace("_", " ").title()),
                    y=alt.Y("count:Q", title="Count", stack='zero'),
                    color=alt.Color("status:N", scale=alt.Scale(range=COLOR_PALETTE),
                                   legend=alt.Legend(title="Status")),
                    order=alt.Order("status:N", sort='descending'),
                    tooltip=[
                        alt.Tooltip(f"{x_col}:O", title=x_col.replace("_", " ").title()),
                        alt.Tooltip("status:N", title="Status"),
                        alt.Tooltip("count:Q", title="Count", format=",")
                    ]
                ).properties(height=400)
            else:
                # Data already in long format
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X(f"{x_col}:O", title=x_col.replace("_", " ").title()),
                    y=alt.Y(f"{y_col}:Q", title=y_col.replace("_", " ").title(), stack='zero'),
                    color=alt.Color(f"{color_col}:N", scale=alt.Scale(range=COLOR_PALETTE),
                                   legend=alt.Legend(title=color_col.replace("_", " ").title())),
                    order=alt.Order(f"{color_col}:N", sort='descending'),
                    tooltip=[
                        alt.Tooltip(f"{x_col}:O", title=x_col.replace("_", " ").title()),
                        alt.Tooltip(f"{color_col}:N", title=color_col.replace("_", " ").title()),
                        alt.Tooltip(f"{y_col}:Q", title=y_col.replace("_", " ").title(), format=",")
                    ]
                ).properties(height=400)
        elif chart_type == "line":
            chart = alt.Chart(df).mark_line(point=True).encode(
                x=alt.X(f"{x_col}:O", title=x_col.replace("_", " ").title()),
                y=alt.Y(f"{y_col}:Q", title=y_col.replace("_", " ").title()),
                color=color_encoding,
                tooltip=list(df.columns)
            ).properties(height=400)
        else:
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


# =============================================================================
# PAGE RENDERING
# =============================================================================

def render_landing_page():
    """Render the landing page with search, filters, and query list."""
    all_queries = get_all_queries()

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

    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🤖 AI Query Builder", use_container_width=True):
            go_to_ai_builder()
    with col3:
        if st.button("📝 Contribute Query", use_container_width=True):
            go_to_contribute()

    ''

    selected_category = st.pills(
        "Categories",
        options=CATEGORIES,
        default=st.session_state.get('selected_category'),
        selection_mode="single",
        key="category_pills"
    )

    if selected_category != st.session_state.get('selected_category'):
        st.session_state['selected_category'] = selected_category

    selected_stakeholders = st.pills(
        "Stakeholders",
        options=STAKEHOLDER_TAGS,
        default=st.session_state.get('selected_stakeholders', []),
        selection_mode="multi",
        key="stakeholder_pills"
    )
    st.session_state['selected_stakeholders'] = selected_stakeholders if selected_stakeholders else []

    ''

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

    favorites = st.session_state.get('favorites', [])
    if favorites:
        st.subheader("⭐ My Saved Queries")
        fav_cols = st.columns(min(len(favorites), 3))
        for i, fav in enumerate(favorites[:3]):
            with fav_cols[i % 3]:
                if st.button(f"⭐ {fav.get('name', 'Saved Query')}", key=f"fav_{i}", use_container_width=True):
                    st.session_state['selected_query'] = fav.get('id')
                    st.session_state['current_page'] = 'detail'
                    st.rerun()
        if len(favorites) > 3:
            st.caption(f"+{len(favorites) - 3} more saved queries")
        st.divider()

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

        ''
        st.divider()

    render_query_list(search_term, selected_category, selected_stakeholders)


def render_query_list(search_term: str = None, category_filter: str = None,
                      stakeholder_filter: list = None):
    """Render query list with enhanced cards and filtering."""
    all_queries = get_all_queries()

    filtered_queries = filter_queries(
        all_queries,
        search_term=search_term,
        category=category_filter,
        stakeholders=stakeholder_filter
    )

    if not filtered_queries:
        st.info("No queries match your search criteria.")
        st.markdown("**Suggestions:**")
        st.markdown("- Try different keywords")
        st.markdown("- Remove some filters")
        st.markdown("- Check spelling")
        return

    st.caption(f"Showing {len(filtered_queries)} queries")

    for query_id, query_info in filtered_queries.items():
        with st.container(border=True):
            # Row 1: Title + Time + Load button
            col_title, col_time, col_action = st.columns([5, 1, 1])

            with col_title:
                st.markdown(f"**{query_id}:** {query_info['title']}")

            with col_time:
                est_time = query_info.get('estimated_seconds_cached', 5)
                st.caption(f"~{format_time(est_time)}")
                st.caption(query_info.get('category', ''))

            with col_action:
                if st.button("Load", key=f"load_{query_id}", use_container_width=True):
                    go_to_detail(query_id)

            # Row 2: Description + Tags
            description = query_info.get('description', '')
            if len(description) > 120:
                description = description[:117] + "..."
            st.caption(description)

            tags_html = render_tags_inline(query_info.get('tags', []))
            st.markdown(tags_html, unsafe_allow_html=True)


def render_detail_page(query_id: str):
    """Render detail page for a specific query."""
    all_queries = get_all_queries()

    if st.button("← Back to Questions", key="back_to_landing"):
        go_to_landing()
        return

    if query_id not in all_queries:
        st.error(f"Query '{query_id}' not found.")
        return

    query_info = all_queries[query_id]

    st.header(f"{query_id}: {query_info['title']}")

    tag_colors = {"PATLIB": "#1f77b4", "BUSINESS": "#2ca02c", "UNIVERSITY": "#9467bd"}
    tags_html = " ".join([
        f'<span style="background-color: {tag_colors.get(t, "#666")}; '
        f'color: white; padding: 2px 10px; border-radius: 12px; font-size: 0.85em; margin-right: 6px;">{t}</span>'
        for t in query_info.get("tags", [])
    ])
    st.markdown(tags_html, unsafe_allow_html=True)
    st.markdown("")

    st.markdown(f"**{query_info.get('description', '')}**")

    ''

    collected_params, run_clicked = render_query_parameters(query_id)

    year_start = collected_params.get('year_start', DEFAULT_YEAR_START)
    year_end = collected_params.get('year_end', DEFAULT_YEAR_END)
    jurisdictions = collected_params.get('jurisdictions', DEFAULT_JURISDICTIONS)
    tech_field = collected_params.get('tech_field')

    ''

    if "explanation" in query_info:
        with st.expander("Details", expanded=False):
            st.markdown(query_info["explanation"])

            if "key_outputs" in query_info:
                st.markdown("**Key Outputs:**")
                for output in query_info["key_outputs"]:
                    st.markdown(f"- {output}")

    estimated_cached = query_info.get("estimated_seconds_cached", 0)
    estimated_first = query_info.get("estimated_seconds_first_run", estimated_cached)
    if estimated_first > 0:
        if estimated_first != estimated_cached:
            st.caption(f"Estimated: ~{format_time(estimated_cached)} (cached) / ~{format_time(estimated_first)} (first run)")
        else:
            st.caption(f"Estimated: ~{format_time(estimated_cached)}")

    with st.expander("View SQL Query", expanded=False):
        # Show sql_template if available (with parameter placeholders), otherwise static sql
        if "sql_template" in query_info:
            display_sql = query_info["sql_template"]
        else:
            display_sql = query_info["sql"]
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

    if "methodology" in query_info:
        with st.expander("Methodology", expanded=False):
            st.markdown(query_info["methodology"])

    st.divider()

    if run_clicked:
        client = get_bigquery_client()
        if client is None:
            st.error("Could not connect to BigQuery.")
            return

        spinner_msg = get_contextual_spinner_message(query_info)
        estimated_seconds = query_info.get("estimated_seconds_cached", 1)

        with st.spinner(f"{spinner_msg} (~{format_time(estimated_seconds)})"):
            try:
                if "sql_template" in query_info:
                    params = {}
                    params_config = query_info.get('parameters', {})
                    if 'year_range' in params_config:
                        params['year_start'] = year_start
                        params['year_end'] = year_end
                    if 'jurisdictions' in params_config:
                        params['jurisdictions'] = jurisdictions if jurisdictions else None
                    if 'tech_field' in params_config:
                        params['tech_field'] = tech_field
                    if 'tech_sector' in params_config:
                        params['tech_sector'] = collected_params.get('tech_sector')
                    if 'applicant_name' in params_config:
                        params['applicant_name'] = collected_params.get('applicant_name', '')
                    if 'competitors' in params_config:
                        params['competitors'] = collected_params.get('competitors')
                    if 'ipc_class' in params_config:
                        params['ipc_class'] = collected_params.get('ipc_class', '')
                    # Classification query parameters (Q54-Q58)
                    if 'classification_symbol' in params_config:
                        params['classification_symbol'] = collected_params.get('classification_symbol', '')
                    if 'keyword' in params_config:
                        params['keyword'] = collected_params.get('keyword', '')
                    if 'modification_type' in params_config:
                        params['modification_type'] = collected_params.get('modification_type')
                    if 'parent_symbol' in params_config:
                        params['parent_symbol'] = collected_params.get('parent_symbol', '')
                    if 'system' in params_config:
                        params['system'] = collected_params.get('system')
                    df, execution_time = run_parameterized_query(client, query_info["sql_template"], params)
                else:
                    df, execution_time = run_query(client, query_info["sql"])

                if df.empty:
                    st.warning("No results found for your query.")
                    st.info("**Suggestions:** Try broadening the year range or selecting different jurisdictions.")
                    return

                headline = generate_insight_headline(df, query_info)
                if headline:
                    st.markdown(headline)
                    ''

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

                ''

                display_mode = query_info.get('display_mode', 'default')
                chart = None  # Initialize chart variable for all display modes

                if display_mode == 'metrics_grid':
                    # Special mode: Display results as metric cards in a grid
                    # Works with 2-column dataframes (metric, value)
                    if len(df.columns) == 2:
                        metric_col = df.columns[0]
                        value_col = df.columns[1]

                        # Display metrics in rows of 4
                        rows = [df.iloc[i:i+4] for i in range(0, len(df), 4)]
                        for row_df in rows:
                            cols = st.columns(4)
                            for idx, (_, row) in enumerate(row_df.iterrows()):
                                with cols[idx]:
                                    label = str(row[metric_col])
                                    value = row[value_col]
                                    # Format large numbers with commas
                                    if isinstance(value, (int, float)):
                                        st.metric(label=label, value=f"{value:,.0f}")
                                    elif str(value).replace(',', '').isdigit():
                                        st.metric(label=label, value=f"{int(str(value).replace(',', '')):,}")
                                    else:
                                        st.metric(label=label, value=str(value))

                        ''

                    # Optional chart (only if visualization config exists and not disabled)
                    if query_info.get('visualization', {}).get('type'):
                        chart = render_chart(df, query_info)
                        if chart:
                            st.altair_chart(chart, use_container_width=True)

                    # Data table in expander (same as default)
                    with st.expander("View Data Table", expanded=False):
                        st.dataframe(df, use_container_width=True, height=400)

                elif display_mode == 'chart_and_table':
                    # Chart + visible table (no expander)
                    chart = render_chart(df, query_info)
                    if chart:
                        st.altair_chart(chart, use_container_width=True)

                    st.markdown("### Data")
                    st.dataframe(df, use_container_width=True, hide_index=True)

                else:
                    # Default mode
                    chart = render_chart(df, query_info)
                    if chart:
                        st.altair_chart(chart, use_container_width=True)

                    if len(df) <= 5 and len(df.columns) == 2:
                        render_metrics(df, query_info)

                    with st.expander("View Data Table", expanded=False):
                        st.dataframe(df, use_container_width=True, height=400)

                st.divider()

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
                    if chart:
                        chart_html = chart.to_html()
                        st.download_button(
                            label="📊 Download Chart (HTML)",
                            data=chart_html,
                            file_name=f"{base_filename}_{timestamp}_chart.html",
                            mime="text/html",
                            key="download_chart"
                        )

                st.divider()
                if "tip" in query_info.get("platforms", ["bigquery", "tip"]):
                    render_tip_panel(query_info, collected_params)

            except Exception as e:
                st.error(f"Error: {str(e)}")


def render_tip_panel(query_info: dict, collected_params: dict):
    """Render the Take to TIP panel (Stories 5.1, 5.2)."""
    with st.expander("🎓 Take to TIP - Use in EPO's Jupyter Environment", expanded=False):
        st.markdown("""
        **TIP (Technology & Innovation Portal)** lets you run this query in EPO's
        Jupyter environment with full PATSTAT access.
        """)

        sql = query_info.get('sql_template', query_info.get('sql', ''))
        tip_sql = format_sql_for_tip(sql, collected_params)

        st.markdown("**📋 Ready-to-run SQL Query:**")
        st.code(tip_sql, language="sql")

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


def render_contribute_page():
    """Render the contribution flow (Stories 3.1-3.4)."""
    from .utils import detect_sql_parameters

    if st.button("← Back to Questions", key="back_from_contribute"):
        go_to_landing()
        return

    st.header("Contribute a Query")
    st.markdown("Share your SQL expertise with 300 PATLIB centres!")

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
        st.subheader("Step 2: Preview Your Query")

        st.markdown("**Query Card Preview:**")
        with st.container(border=True):
            st.markdown(f"**Q??: {contrib['title']}**")
            st.caption(contrib['description'])
            tags_html = render_tags_inline(contrib.get('tags', []))
            st.markdown(tags_html, unsafe_allow_html=True)

        st.markdown("**SQL:**")
        st.code(contrib['sql'], language="sql")

        if st.button("🧪 Test Query"):
            client = get_bigquery_client()
            if client:
                with st.spinner("Testing query..."):
                    try:
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

    if generate_clicked and ai_request.strip():
        with st.spinner("🤖 AI is generating your query..."):
            result = generate_sql_query(ai_request)

            if result['success']:
                st.session_state['ai_generation'] = result
                if 'ai_query_versions' not in st.session_state:
                    st.session_state['ai_query_versions'] = []
                st.session_state['ai_query_versions'].append({
                    'request': ai_request,
                    'result': result,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M')
                })
            else:
                st.error(f"Generation failed: {result['error']}")

    generation = st.session_state.get('ai_generation')
    if generation and generation.get('success'):
        st.divider()
        st.subheader("Generated Query")

        st.markdown("**📝 What this query does:**")
        st.info(generation.get('explanation', 'No explanation provided'))

        st.markdown("**💻 SQL Query:**")
        st.code(generation['sql'], language="sql")

        if generation.get('notes') and generation['notes'].lower() != 'none':
            st.markdown(f"**⚠️ Notes:** {generation['notes']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            preview_clicked = st.button("🧪 Preview Results")

        with col2:
            if st.button("⭐ Save to Favorites"):
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

        # Render preview results full-width (outside column context)
        if preview_clicked:
            client = get_bigquery_client()
            if client:
                with st.spinner("Running query..."):
                    try:
                        test_sql = generation['sql']
                        if 'LIMIT' not in test_sql.upper():
                            test_sql = test_sql.rstrip().rstrip(';') + ' LIMIT 100'
                        df, exec_time = run_query(client, test_sql)

                        st.divider()
                        st.success(f"Executed in {format_time(exec_time)} - {len(df)} rows")

                        query_info = {'title': 'AI Query', 'category': 'Technology'}
                        headline = generate_insight_headline(df, query_info)
                        if headline:
                            st.markdown(headline)

                        chart = render_chart(df, query_info)
                        if chart:
                            st.altair_chart(chart, use_container_width=True)

                        with st.expander("View Data"):
                            st.dataframe(df, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

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
