import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import os
from dotenv import load_dotenv
import time
import json
from queries_bq import QUERIES, STAKEHOLDERS, DYNAMIC_QUERIES, REFERENCE_QUERIES

# Load environment variables
load_dotenv()

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


def run_query(client: bigquery.Client, query: str) -> tuple[pd.DataFrame, float]:
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


def get_filtered_queries(stakeholder_filter: str) -> dict:
    """Filter queries by stakeholder tag."""
    if stakeholder_filter == "Alle":
        return QUERIES
    return {
        qid: qinfo for qid, qinfo in QUERIES.items()
        if stakeholder_filter in qinfo.get("tags", [])
    }


@st.cache_data(ttl=3600)
def load_reference_data(_client: bigquery.Client, ref_type: str) -> pd.DataFrame:
    """Load reference data for dynamic query dropdowns."""
    if ref_type not in REFERENCE_QUERIES:
        return pd.DataFrame()

    project = os.getenv("BIGQUERY_PROJECT", "patstat-mtc")
    dataset = os.getenv("BIGQUERY_DATASET", "patstat")

    job_config = bigquery.QueryJobConfig(
        default_dataset=f"{project}.{dataset}"
    )

    try:
        return _client.query(REFERENCE_QUERIES[ref_type], job_config=job_config).to_dataframe()
    except Exception as e:
        st.error(f"Error loading reference data: {e}")
        return pd.DataFrame()


def run_dynamic_query(client: bigquery.Client, query_id: str, params: dict) -> tuple[pd.DataFrame, float]:
    """Execute a dynamic query with user-provided parameters."""
    if query_id not in DYNAMIC_QUERIES:
        return pd.DataFrame(), 0.0

    query_info = DYNAMIC_QUERIES[query_id]
    sql_template = query_info["sql_template"]

    project = os.getenv("BIGQUERY_PROJECT", "patstat-mtc")
    dataset = os.getenv("BIGQUERY_DATASET", "patstat")

    # Build query parameters for BigQuery
    query_params = [
        bigquery.ScalarQueryParameter("jurisdiction", "STRING", params.get("jurisdiction", "EP")),
        bigquery.ScalarQueryParameter("tech_field", "INT64", params.get("tech_field", 13)),
        bigquery.ScalarQueryParameter("year_start", "INT64", params.get("year_start", 2015)),
        bigquery.ScalarQueryParameter("year_end", "INT64", params.get("year_end", 2023)),
    ]

    job_config = bigquery.QueryJobConfig(
        default_dataset=f"{project}.{dataset}",
        query_parameters=query_params
    )

    start_time = time.time()
    result = client.query(sql_template, job_config=job_config).to_dataframe()
    execution_time = time.time() - start_time
    return result, execution_time


def render_interactive_panel(client: bigquery.Client):
    """Render the interactive analysis panel with dynamic parameters."""

    # Load reference data
    jurisdictions_df = load_reference_data(client, "JURISDICTIONS")
    tech_fields_df = load_reference_data(client, "TECH_FIELDS")

    if jurisdictions_df.empty or tech_fields_df.empty:
        st.warning("Could not load reference data. Please try again.")
        return

    # Get query info
    query_info = DYNAMIC_QUERIES["DQ01"]

    # Header
    st.header(f"🔍 {query_info['title']}")
    st.markdown(f"**{query_info['description']}**")

    # Parameter widgets in columns
    col1, col2 = st.columns(2)

    with col1:
        # Jurisdiction dropdown
        jurisdiction_options = {
            f"{row['name']} ({row['code']})": row['code']
            for _, row in jurisdictions_df.iterrows()
        }
        selected_jurisdiction_label = st.selectbox(
            "📍 Filing Jurisdiction",
            options=list(jurisdiction_options.keys()),
            index=list(jurisdiction_options.values()).index("EP") if "EP" in jurisdiction_options.values() else 0,
            help=query_info["parameters"]["jurisdiction"]["description"]
        )
        selected_jurisdiction = jurisdiction_options[selected_jurisdiction_label]

    with col2:
        # Tech field dropdown - grouped by sector
        tech_field_options = {
            f"{row['name']} ({row['sector']})": row['code']
            for _, row in tech_fields_df.iterrows()
        }
        # Find default (Medical technology = 13)
        default_idx = 0
        for i, code in enumerate(tech_field_options.values()):
            if code == 13:
                default_idx = i
                break

        selected_tech_label = st.selectbox(
            "🔬 Technology Field",
            options=list(tech_field_options.keys()),
            index=default_idx,
            help=query_info["parameters"]["tech_field"]["description"]
        )
        selected_tech_field = tech_field_options[selected_tech_label]

    # Year range slider
    year_params = query_info["parameters"]["year_range"]
    year_start, year_end = st.slider(
        "📅 Filing Years",
        min_value=year_params["min"],
        max_value=year_params["max"],
        value=tuple(year_params["default"]),
        help=year_params["description"]
    )

    # Show explanation
    with st.expander("ℹ️ About this analysis", expanded=False):
        st.markdown(query_info["explanation"])
        if "key_outputs" in query_info:
            st.markdown("**Key Outputs:**")
            for output in query_info["key_outputs"]:
                st.markdown(f"- {output}")

    st.divider()

    # Execute button
    col1, col2 = st.columns([1, 5])
    with col1:
        execute_button = st.button("▶️ Run Analysis", type="primary", key="run_interactive")

    # Show estimated time
    with col2:
        estimated = query_info.get("estimated_seconds_cached", 2)
        st.caption(f"Estimated: ~{format_time(estimated)}")

    if execute_button:
        params = {
            "jurisdiction": selected_jurisdiction,
            "tech_field": selected_tech_field,
            "year_start": year_start,
            "year_end": year_end
        }

        with st.spinner(f"Analyzing {selected_jurisdiction} patents in {selected_tech_label.split(' (')[0]}..."):
            try:
                df, execution_time = run_dynamic_query(client, "DQ01", params)

                if df.empty:
                    st.warning("No data found for the selected parameters.")
                    return

                # Metrics row
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Applications", f"{df['application_count'].sum():,}")
                with col2:
                    st.metric("Unique Inventions", f"{df['invention_count'].sum():,}")
                with col3:
                    st.metric("Execution Time", format_time(execution_time))

                st.divider()

                # Line chart
                st.subheader("📈 Trend Over Time")
                st.line_chart(
                    df,
                    x="year",
                    y=["application_count", "invention_count"],
                    color=["#1f77b4", "#2ca02c"]
                )

                # Data table
                st.subheader("📊 Data")
                st.dataframe(df, use_container_width=True)

                # Download button
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"trend_{selected_jurisdiction}_{selected_tech_field}_{year_start}-{year_end}.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error(f"Error executing query: {str(e)}")


def render_query_panel(filtered_queries: dict, client, tab_key: str):
    """Render the query selection and execution panel."""
    if not filtered_queries:
        st.info("No queries in this category.")
        return

    # Query selection
    query_options = {
        qid: f"{qid} - {qinfo['title']}"
        for qid, qinfo in filtered_queries.items()
    }

    selected_query_id = st.selectbox(
        "Select Query",
        options=list(query_options.keys()),
        format_func=lambda x: query_options[x],
        key=f"query_select_{tab_key}"
    )

    if selected_query_id:
        query_info = QUERIES[selected_query_id]

        st.divider()

        # Header with ID and title
        st.header(f"{selected_query_id}: {query_info['title']}")

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
        estimated_seconds = estimated_cached
        if estimated_first > 0:
            if estimated_first != estimated_cached:
                st.caption(f"Estimated: ~{format_time(estimated_cached)} (cached) / ~{format_time(estimated_first)} (first run)")
            else:
                st.caption(f"Estimated: ~{format_time(estimated_cached)}")

        # Show the SQL query in an expander
        with st.expander("View SQL Query", expanded=False):
            st.code(query_info["sql"], language="sql")

        st.divider()

        # Execute button
        col1, col2 = st.columns([1, 5])
        with col1:
            execute_button = st.button("Run Query", type="primary", key=f"exec_{tab_key}")

        if execute_button:
            with st.spinner(f"Running query... (~{format_time(estimated_seconds)})"):
                try:
                    df, execution_time = run_query(client, query_info["sql"])

                    # Show results metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Rows", f"{len(df):,}")
                    with col2:
                        st.metric("Execution time", format_time(execution_time))
                    with col3:
                        if estimated_seconds > 0:
                            diff = execution_time - estimated_seconds
                            delta_str = f"{'+' if diff > 0 else ''}{format_time(abs(diff))}"
                            st.metric("vs. Estimate", delta_str,
                                     delta=f"{'slower' if diff > 0 else 'faster'}",
                                     delta_color="inverse")

                    st.divider()

                    # Display dataframe
                    st.dataframe(df, use_container_width=True, height=400)

                    # Download button
                    csv = df.to_csv(index=False)
                    filename = f"{selected_query_id}_{query_info['title'].lower().replace(' ', '_').replace('-', '_')}.csv"
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=filename,
                        mime="text/csv",
                        key=f"download_{tab_key}"
                    )

                except Exception as e:
                    st.error(f"Error: {str(e)}")


def main():
    client = get_bigquery_client()

    if client is None:
        st.stop()

    # Create tabs - Interactive Analysis first for visibility
    tab_labels = [
        "🔍 Interactive",
        f"Alle ({len(QUERIES)})",
        f"PATLIB ({len(get_filtered_queries('PATLIB'))})",
        f"BUSINESS ({len(get_filtered_queries('BUSINESS'))})",
        f"UNIVERSITY ({len(get_filtered_queries('UNIVERSITY'))})"
    ]

    tabs = st.tabs(tab_labels)

    # Tab: Interactive Analysis (NEW)
    with tabs[0]:
        st.caption("Dynamic patent analysis with customizable parameters")
        render_interactive_panel(client)

    # Tab: Alle
    with tabs[1]:
        render_query_panel(QUERIES, client, "alle")

    # Tab: PATLIB
    with tabs[2]:
        st.caption(STAKEHOLDERS["PATLIB"])
        render_query_panel(get_filtered_queries("PATLIB"), client, "patlib")

    # Tab: BUSINESS
    with tabs[3]:
        st.caption(STAKEHOLDERS["BUSINESS"])
        render_query_panel(get_filtered_queries("BUSINESS"), client, "business")

    # Tab: UNIVERSITY
    with tabs[4]:
        st.caption(STAKEHOLDERS["UNIVERSITY"])
        render_query_panel(get_filtered_queries("UNIVERSITY"), client, "university")


if __name__ == "__main__":
    main()
