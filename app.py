import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import os
from dotenv import load_dotenv
import time
import json
from queries_bq import QUERIES, STAKEHOLDERS

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="PATSTAT Explorer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 PATSTAT Explorer")
st.caption("Patent Analysis Platform - EPO PATSTAT 2024 Autumn on BigQuery")


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

    # Create tabs
    tab_labels = [
        f"Alle ({len(QUERIES)})",
        f"PATLIB ({len(get_filtered_queries('PATLIB'))})",
        f"BUSINESS ({len(get_filtered_queries('BUSINESS'))})",
        f"UNIVERSITY ({len(get_filtered_queries('UNIVERSITY'))})"
    ]

    tabs = st.tabs(tab_labels)

    # Tab: Alle
    with tabs[0]:
        render_query_panel(QUERIES, client, "alle")

    # Tab: PATLIB
    with tabs[1]:
        st.caption(STAKEHOLDERS["PATLIB"])
        render_query_panel(get_filtered_queries("PATLIB"), client, "patlib")

    # Tab: BUSINESS
    with tabs[2]:
        st.caption(STAKEHOLDERS["BUSINESS"])
        render_query_panel(get_filtered_queries("BUSINESS"), client, "business")

    # Tab: UNIVERSITY
    with tabs[3]:
        st.caption(STAKEHOLDERS["UNIVERSITY"])
        render_query_panel(get_filtered_queries("UNIVERSITY"), client, "university")


if __name__ == "__main__":
    main()
