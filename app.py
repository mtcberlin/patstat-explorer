import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
import os
from dotenv import load_dotenv
import time
import json
from queries_bq import QUERIES

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="PATSTAT Explorer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 PATSTAT Explorer")
st.caption("Technology Intelligence Platform - Patent Analysis Queries")


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


def main():
    client = get_bigquery_client()

    if client is None:
        st.stop()

    # Sidebar for navigation
    st.sidebar.header("Navigation")

    # Stakeholder selection
    stakeholders = list(QUERIES.keys())
    selected_stakeholder = st.sidebar.selectbox(
        "Select Stakeholder",
        stakeholders,
        index=0 if stakeholders else None
    )

    if selected_stakeholder:
        st.header(f"📁 {selected_stakeholder}")

        # Get queries for selected stakeholder
        stakeholder_queries = QUERIES[selected_stakeholder]
        query_names = list(stakeholder_queries.keys())

        # Query selection
        selected_query = st.selectbox(
            "Select Query",
            query_names,
            index=0 if query_names else None
        )

        if selected_query:
            query_info = stakeholder_queries[selected_query]

            # Query description
            st.subheader(query_info.get("description", selected_query))

            # Show explanation in an info box
            if "explanation" in query_info:
                st.info(query_info["explanation"])

            # Show key outputs
            if "key_outputs" in query_info:
                st.markdown("**Key Outputs:**")
                for output in query_info["key_outputs"]:
                    st.markdown(f"- {output}")

            # Show estimated time (use cached estimate, show first-run estimate too if different)
            estimated_cached = query_info.get("estimated_seconds_cached", 0)
            estimated_first = query_info.get("estimated_seconds_first_run", estimated_cached)
            estimated_seconds = estimated_cached  # Use cached for comparison
            if estimated_first > 0:
                if estimated_first != estimated_cached:
                    st.markdown(f"**Estimated time:** ~{format_time(estimated_cached)} (cached) / ~{format_time(estimated_first)} (first run)")
                else:
                    st.markdown(f"**Estimated execution time:** ~{format_time(estimated_cached)}")

            st.divider()

            # Show the SQL query in an expander
            with st.expander("View SQL Query", expanded=False):
                st.code(query_info["sql"], language="sql")

            # Execute button
            col1, col2 = st.columns([1, 4])
            with col1:
                execute_button = st.button("Execute Query", type="primary")

            if execute_button:
                with st.spinner(f"Running query... (estimated ~{format_time(estimated_seconds)})"):
                    try:
                        df, execution_time = run_query(client, query_info["sql"])

                        # Show results metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Rows returned", f"{len(df):,}")
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
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"{selected_query.lower().replace(' ', '_')}.csv",
                            mime="text/csv"
                        )

                    except Exception as e:
                        st.error(f"Error executing query: {str(e)}")
    else:
        st.info("Please select a stakeholder from the sidebar.")

    # Footer
    st.sidebar.divider()
    st.sidebar.caption("PATSTAT Explorer v1.0")
    st.sidebar.caption("Data: EPO PATSTAT Database")


if __name__ == "__main__":
    main()
