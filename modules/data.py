# PATSTAT Explorer - Data Access Layer
# BigQuery client, query execution, and data access functions

import os
import json
import time
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

from queries_bq import QUERIES
from .config import JURISDICTIONS, TECH_FIELDS


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

    # Classification query parameters (Q54-Q58)
    if "classification_symbol" in params and params["classification_symbol"] is not None:
        query_params.append(bigquery.ScalarQueryParameter("classification_symbol", "STRING", params["classification_symbol"]))

    if "keyword" in params and params["keyword"] is not None:
        query_params.append(bigquery.ScalarQueryParameter("keyword", "STRING", params["keyword"]))

    if "modification_type" in params and params["modification_type"] is not None:
        query_params.append(bigquery.ScalarQueryParameter("modification_type", "STRING", params["modification_type"]))

    if "parent_symbol" in params and params["parent_symbol"] is not None:
        query_params.append(bigquery.ScalarQueryParameter("parent_symbol", "STRING", params["parent_symbol"]))

    if "system" in params and params["system"] is not None:
        query_params.append(bigquery.ScalarQueryParameter("system", "STRING", params["system"]))

    # Set job config with parameters
    job_config = bigquery.QueryJobConfig(
        default_dataset=f"{project}.{dataset}",
        query_parameters=query_params
    )

    start_time = time.time()
    result = client.query(sql_template, job_config=job_config).to_dataframe()
    execution_time = time.time() - start_time
    return result, execution_time


def get_all_queries() -> dict:
    """Get all queries including contributed ones (Story 3.4)."""
    all_queries = QUERIES.copy()
    # Add contributed queries from session
    contributed = st.session_state.get('contributed_queries', {})
    all_queries.update(contributed)
    return all_queries


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
