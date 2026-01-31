# PATSTAT Explorer - Main Entry Point
# Refactored modular structure (Story 6.2)

import streamlit as st

from modules.ui import (
    init_session_state,
    render_landing_page,
    render_detail_page,
    render_contribute_page,
    render_ai_builder_page,
    render_footer
)
from modules.data import get_bigquery_client


# Page config - must be first Streamlit command
st.set_page_config(
    page_title="PATSTAT Explorer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 PATSTAT Explorer")
st.caption("Patent Analysis Platform - EPO PATSTAT 2025 Autumn on BigQuery by mtc")


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
