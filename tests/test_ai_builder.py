"""Tests for Stories 4.1-4.4: AI Query Builder."""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.logic import parse_ai_response, is_ai_available
from modules.config import PATSTAT_SYSTEM_PROMPT


class TestParseAiResponse:
    """Tests for AI response parsing (Story 4.2)."""

    def test_parse_valid_response(self):
        """Parse valid structured response."""
        response = """EXPLANATION:
This query finds the top 10 patent filers in Germany since 2018.

SQL:
```sql
SELECT person_name, COUNT(*) AS patent_count
FROM tls206_person p
JOIN tls207_pers_appln pa ON p.person_id = pa.person_id
WHERE p.person_ctry_code = 'DE'
GROUP BY person_name
ORDER BY patent_count DESC
LIMIT 10
```

NOTES:
None"""

        result = parse_ai_response(response)

        assert result['success'] == True
        assert "top 10 patent filers" in result['explanation']
        assert "SELECT" in result['sql']
        assert "LIMIT 10" in result['sql']

    def test_parse_response_with_warnings(self):
        """Parse response with notes/warnings."""
        response = """EXPLANATION:
This query analyzes citation networks.

SQL:
```sql
SELECT * FROM tls212_citation LIMIT 100
```

NOTES:
This query may be slow due to large table size. Consider adding filters."""

        result = parse_ai_response(response)

        assert result['success'] == True
        assert "may be slow" in result['notes']

    def test_parse_response_missing_sql(self):
        """Parse response with missing SQL fails."""
        response = """EXPLANATION:
I cannot generate this query because the request is unclear.

NOTES:
Please provide more specific technology or time period."""

        result = parse_ai_response(response)

        assert result['success'] == False
        assert result['error'] is not None

    def test_parse_response_extracts_sql_without_language_marker(self):
        """Parse response with code block without sql marker."""
        response = """EXPLANATION:
Simple query.

SQL:
```
SELECT * FROM tls201_appln LIMIT 10
```

NOTES:
None"""

        result = parse_ai_response(response)

        assert result['success'] == True
        assert "SELECT" in result['sql']


class TestSystemPrompt:
    """Tests for PATSTAT system prompt (Story 4.1)."""

    def test_system_prompt_includes_tables(self):
        """System prompt includes key PATSTAT tables."""
        assert "tls201_appln" in PATSTAT_SYSTEM_PROMPT
        assert "tls206_person" in PATSTAT_SYSTEM_PROMPT
        assert "tls207_pers_appln" in PATSTAT_SYSTEM_PROMPT

    def test_system_prompt_includes_column_info(self):
        """System prompt includes key column information."""
        assert "appln_id" in PATSTAT_SYSTEM_PROMPT
        assert "person_name" in PATSTAT_SYSTEM_PROMPT
        assert "appln_filing_year" in PATSTAT_SYSTEM_PROMPT

    def test_system_prompt_includes_format_instructions(self):
        """System prompt includes response format instructions."""
        assert "EXPLANATION:" in PATSTAT_SYSTEM_PROMPT
        assert "SQL:" in PATSTAT_SYSTEM_PROMPT
        assert "NOTES:" in PATSTAT_SYSTEM_PROMPT

    def test_system_prompt_includes_bigquery_guidance(self):
        """System prompt includes BigQuery guidance."""
        assert "BigQuery" in PATSTAT_SYSTEM_PROMPT
        assert "LIMIT" in PATSTAT_SYSTEM_PROMPT


class TestAiAvailability:
    """Tests for AI availability check (Story 4.1)."""

    def test_ai_available_returns_boolean(self):
        """is_ai_available returns a boolean."""
        result = is_ai_available()
        assert isinstance(result, bool)


class TestAiResponseErrors:
    """Tests for AI error handling (Story 4.2)."""

    def test_parse_empty_response(self):
        """Empty response fails gracefully."""
        result = parse_ai_response("")
        assert result['success'] == False

    def test_parse_malformed_response(self):
        """Malformed response fails gracefully."""
        result = parse_ai_response("This is not a structured response")
        assert result['success'] == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
