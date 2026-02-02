# PATSTAT Explorer - Business Logic
# Filtering, validation, AI client, and data processing functions

import os
import streamlit as st
import pandas as pd

from queries_bq import QUERIES
from .config import PATSTAT_SYSTEM_PROMPT
from .abra_q_client import get_abraq_client, is_abraq_available


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
    provider = os.getenv("QUERY_PROVIDER", "claude").lower()

    if provider == "abra-q":
        return is_abraq_available()
    else:
        return get_claude_client() is not None


def generate_sql_query(user_request: str) -> dict:
    """Generate SQL from natural language using configured provider (Story 4.2).

    Supports multiple query generation providers:
    - claude: Anthropic Claude API (default)
    - abra-q: TTC's Abra-Q service

    Provider is selected via QUERY_PROVIDER environment variable.
    """
    provider = os.getenv("QUERY_PROVIDER", "claude").lower()

    # Route to Abra-Q provider
    if provider == "abra-q":
        abraq_client = get_abraq_client()
        if not abraq_client:
            return {'success': False, 'error': 'Abra-Q not configured. Check ABRAQ_EMAIL and ABRAQ_PASSWORD.'}

        try:
            return abraq_client.generate_query(user_request)
        except Exception as e:
            return {'success': False, 'error': f'Abra-Q error: {str(e)}'}

    # Route to Claude provider (default)
    else:
        client = get_claude_client()
        if not client:
            return {'success': False, 'error': 'Claude API not configured. Check ANTHROPIC_API_KEY.'}

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
            return {'success': False, 'error': f'Claude API error: {str(e)}'}


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
