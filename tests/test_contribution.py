"""Tests for Stories 3.1-3.4: Query Contribution System."""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.logic import validate_contribution_step1, submit_contribution
from modules.utils import detect_sql_parameters
from modules.config import CATEGORIES, STAKEHOLDER_TAGS


class TestValidateContribution:
    """Tests for contribution validation (Story 3.3)."""

    def test_valid_contribution(self, monkeypatch):
        """Valid contribution passes validation."""
        # Mock session state - must patch where it's used, not where it's defined
        mock_state = {
            'contribution': {
                'title': 'Test Query Title?',
                'description': 'Test description',
                'sql': 'SELECT * FROM tls201_appln LIMIT 10',
                'tags': ['PATLIB'],
                'category': 'Technology'
            }
        }
        from modules import logic
        monkeypatch.setattr(logic.st, 'session_state', mock_state)

        errors = validate_contribution_step1()
        assert len(errors) == 0

    def test_missing_title(self, monkeypatch):
        """Missing title fails validation."""
        mock_state = {
            'contribution': {
                'title': '',
                'description': 'Test description',
                'sql': 'SELECT * FROM tls201_appln',
                'tags': ['PATLIB'],
                'category': 'Technology'
            }
        }
        from modules import logic
        monkeypatch.setattr(logic.st, 'session_state', mock_state)

        errors = validate_contribution_step1()
        assert "Title is required" in errors

    def test_missing_description(self, monkeypatch):
        """Missing description fails validation."""
        mock_state = {
            'contribution': {
                'title': 'Test Title',
                'description': '',
                'sql': 'SELECT * FROM tls201_appln',
                'tags': ['PATLIB'],
                'category': 'Technology'
            }
        }
        from modules import logic
        monkeypatch.setattr(logic.st, 'session_state', mock_state)

        errors = validate_contribution_step1()
        assert "Description is required" in errors

    def test_missing_sql(self, monkeypatch):
        """Missing SQL fails validation."""
        mock_state = {
            'contribution': {
                'title': 'Test Title',
                'description': 'Test description',
                'sql': '',
                'tags': ['PATLIB'],
                'category': 'Technology'
            }
        }
        from modules import logic
        monkeypatch.setattr(logic.st, 'session_state', mock_state)

        errors = validate_contribution_step1()
        assert "SQL query is required" in errors

    def test_missing_tags(self, monkeypatch):
        """Missing tags fails validation."""
        mock_state = {
            'contribution': {
                'title': 'Test Title',
                'description': 'Test description',
                'sql': 'SELECT * FROM tls201_appln',
                'tags': [],
                'category': 'Technology'
            }
        }
        from modules import logic
        monkeypatch.setattr(logic.st, 'session_state', mock_state)

        errors = validate_contribution_step1()
        assert "Select at least one stakeholder tag" in errors

    def test_missing_category(self, monkeypatch):
        """Missing category fails validation."""
        mock_state = {
            'contribution': {
                'title': 'Test Title',
                'description': 'Test description',
                'sql': 'SELECT * FROM tls201_appln',
                'tags': ['PATLIB'],
                'category': ''
            }
        }
        from modules import logic
        monkeypatch.setattr(logic.st, 'session_state', mock_state)

        errors = validate_contribution_step1()
        assert "Select a category" in errors


class TestDetectSqlParameters:
    """Tests for SQL parameter detection (Story 3.2)."""

    def test_detect_year_parameters(self):
        """Detects year_start and year_end parameters."""
        sql = "SELECT * FROM tls201_appln WHERE appln_filing_year BETWEEN @year_start AND @year_end"
        params = detect_sql_parameters(sql)
        assert "year_start" in params
        assert "year_end" in params

    def test_detect_jurisdictions_parameter(self):
        """Detects jurisdictions array parameter."""
        sql = "SELECT * FROM tls201_appln WHERE appln_auth IN UNNEST(@jurisdictions)"
        params = detect_sql_parameters(sql)
        assert "jurisdictions" in params

    def test_detect_tech_field_parameter(self):
        """Detects tech_field parameter."""
        sql = "SELECT * FROM tls230_appln_techn_field WHERE techn_field_nr = @tech_field"
        params = detect_sql_parameters(sql)
        assert "tech_field" in params

    def test_detect_multiple_parameters(self):
        """Detects all parameters in complex query."""
        sql = """
        SELECT * FROM tls201_appln a
        WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
          AND a.appln_auth IN UNNEST(@jurisdictions)
        """
        params = detect_sql_parameters(sql)
        assert len(params) == 3
        assert "year_start" in params
        assert "year_end" in params
        assert "jurisdictions" in params

    def test_no_parameters(self):
        """Returns empty list when no parameters."""
        sql = "SELECT * FROM tls201_appln LIMIT 10"
        params = detect_sql_parameters(sql)
        assert len(params) == 0

    def test_duplicate_parameters_deduplicated(self):
        """Duplicate parameters are deduplicated."""
        sql = """
        SELECT * FROM tls201_appln
        WHERE appln_filing_year >= @year_start
          AND appln_filing_year >= @year_start
        """
        params = detect_sql_parameters(sql)
        assert params.count("year_start") == 1


class TestSubmitContribution:
    """Tests for contribution submission (Story 3.4)."""

    def test_submit_generates_query_id(self, monkeypatch):
        """Submission generates new query ID."""
        # Mock session state - must patch where it's used
        mock_state = {'contributed_queries': {}}
        from modules import logic
        monkeypatch.setattr(logic.st, 'session_state', mock_state)

        contribution = {
            'title': 'Test Query',
            'description': 'Test description',
            'sql': 'SELECT * FROM tls201_appln',
            'tags': ['PATLIB'],
            'category': 'Technology'
        }

        query_id = submit_contribution(contribution)

        assert query_id.startswith('Q')
        assert query_id[1:].isdigit()

    def test_submit_adds_to_contributed_queries(self, monkeypatch):
        """Submission adds query to contributed_queries in session state."""
        mock_state = {'contributed_queries': {}}
        from modules import logic
        monkeypatch.setattr(logic.st, 'session_state', mock_state)

        contribution = {
            'title': 'Test Query',
            'description': 'Test description',
            'sql': 'SELECT * FROM tls201_appln',
            'tags': ['PATLIB'],
            'category': 'Technology'
        }

        query_id = submit_contribution(contribution)

        assert query_id in mock_state['contributed_queries']
        stored = mock_state['contributed_queries'][query_id]
        assert stored['title'] == 'Test Query'
        assert stored['contributed'] == True


class TestContributionConstants:
    """Tests for contribution-related constants."""

    def test_categories_available(self):
        """CATEGORIES is available for contribution form."""
        assert len(CATEGORIES) >= 4
        assert "Competitors" in CATEGORIES
        assert "Trends" in CATEGORIES

    def test_stakeholder_tags_available(self):
        """STAKEHOLDER_TAGS is available for contribution form."""
        assert len(STAKEHOLDER_TAGS) >= 3
        assert "PATLIB" in STAKEHOLDER_TAGS
        assert "BUSINESS" in STAKEHOLDER_TAGS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
