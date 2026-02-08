"""Tests for Story 2-2: Query Metadata Display functionality."""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.ui import render_tags_inline
from modules.utils import format_time
from queries_bq import QUERIES, STAKEHOLDERS


class TestRenderTagsInline:
    """Tests for tag pill rendering (AC #1)."""

    def test_render_single_tag(self):
        """Single tag renders correctly."""
        result = render_tags_inline(["PATLIB"])
        assert "PATLIB" in result
        assert "background-color" in result
        assert "border-radius" in result

    def test_render_multiple_tags(self):
        """Multiple tags render correctly."""
        result = render_tags_inline(["PATLIB", "BUSINESS"])
        assert "PATLIB" in result
        assert "BUSINESS" in result

    def test_render_patlib_color(self):
        """PATLIB tag has correct color (blue)."""
        result = render_tags_inline(["PATLIB"])
        assert "#1f77b4" in result  # Blue

    def test_render_business_color(self):
        """BUSINESS tag has correct color (green)."""
        result = render_tags_inline(["BUSINESS"])
        assert "#2ca02c" in result  # Green

    def test_render_university_color(self):
        """UNIVERSITY tag has correct color (purple)."""
        result = render_tags_inline(["UNIVERSITY"])
        assert "#9467bd" in result  # Purple

    def test_render_empty_tags(self):
        """Empty tag list returns empty string."""
        result = render_tags_inline([])
        assert result == ""

    def test_render_unknown_tag_uses_default_color(self):
        """Unknown tags use default color."""
        result = render_tags_inline(["UNKNOWN"])
        assert "#666" in result


class TestFormatTime:
    """Tests for time formatting."""

    def test_format_milliseconds(self):
        """Sub-second times formatted as milliseconds."""
        assert format_time(0.5) == "500ms"
        assert format_time(0.1) == "100ms"
        assert format_time(0.05) == "50ms"

    def test_format_seconds(self):
        """Times between 1-60s formatted as seconds."""
        assert format_time(1.5) == "1.5s"
        assert format_time(30) == "30.0s"
        assert format_time(59.9) == "59.9s"

    def test_format_minutes(self):
        """Times over 60s formatted as minutes."""
        assert format_time(60) == "1m 0s"
        assert format_time(90) == "1m 30s"
        assert format_time(125) == "2m 5s"


class TestQueryMetadataStructure:
    """Tests for query metadata completeness (AC #1, #3)."""

    def test_all_queries_have_title(self):
        """Every query has a title."""
        for qid, query in QUERIES.items():
            assert 'title' in query, f"{qid} missing title"
            assert query['title'], f"{qid} has empty title"

    def test_all_queries_have_description(self):
        """Every query has a description."""
        for qid, query in QUERIES.items():
            assert 'description' in query, f"{qid} missing description"
            assert query['description'], f"{qid} has empty description"

    def test_all_queries_have_tags(self):
        """Every query has stakeholder tags."""
        for qid, query in QUERIES.items():
            assert 'tags' in query, f"{qid} missing tags"
            assert len(query['tags']) > 0, f"{qid} has no tags"

    def test_all_queries_have_category(self):
        """Every query has a category."""
        valid_categories = ["Competitors", "Trends", "Regional", "Technology", "Classification"]
        for qid, query in QUERIES.items():
            assert 'category' in query, f"{qid} missing category"
            assert query['category'] in valid_categories, f"{qid} has invalid category: {query['category']}"

    def test_all_queries_have_platforms(self):
        """Every query has a platforms field with valid values."""
        valid_platforms = {"bigquery", "tip"}
        for qid, query in QUERIES.items():
            assert 'platforms' in query, f"{qid} missing platforms"
            assert isinstance(query['platforms'], list), f"{qid} platforms is not a list"
            assert len(query['platforms']) > 0, f"{qid} has empty platforms"
            for p in query['platforms']:
                assert p in valid_platforms, f"{qid} has invalid platform: {p}"

    def test_all_queries_have_estimated_time(self):
        """Every query has estimated execution time."""
        for qid, query in QUERIES.items():
            assert 'estimated_seconds_cached' in query, f"{qid} missing estimated_seconds_cached"
            assert query['estimated_seconds_cached'] > 0, f"{qid} has invalid estimated time"

    def test_all_queries_have_sql(self):
        """Every query has SQL."""
        for qid, query in QUERIES.items():
            assert 'sql' in query, f"{qid} missing sql"
            assert query['sql'].strip(), f"{qid} has empty sql"

    def test_all_tags_are_valid_stakeholders(self):
        """All query tags are valid stakeholder types."""
        valid_stakeholders = set(STAKEHOLDERS.keys())
        for qid, query in QUERIES.items():
            for tag in query.get('tags', []):
                assert tag in valid_stakeholders, f"{qid} has invalid tag: {tag}"


class TestQueryTitles:
    """Tests for question-style titles (AC #1)."""

    def test_titles_are_questions_or_descriptive(self):
        """Titles should be question-style or descriptive statements."""
        for qid, query in QUERIES.items():
            title = query.get('title', '')
            # Titles should either end with ? or be descriptive
            # At minimum, they should be meaningful (>10 chars)
            assert len(title) > 10, f"{qid} title too short: {title}"


class TestQueryExplanations:
    """Tests for query explanations (AC #2)."""

    def test_queries_have_explanations(self):
        """Most queries should have explanations."""
        queries_with_explanations = sum(1 for q in QUERIES.values() if q.get('explanation'))
        total_queries = len(QUERIES)
        # At least 80% should have explanations
        assert queries_with_explanations >= total_queries * 0.8


class TestStakeholderDefinitions:
    """Tests for stakeholder definitions."""

    def test_stakeholders_defined(self):
        """STAKEHOLDERS dict is defined with descriptions."""
        assert STAKEHOLDERS is not None
        assert len(STAKEHOLDERS) == 3

    def test_stakeholder_has_descriptions(self):
        """Each stakeholder has a description."""
        assert STAKEHOLDERS["PATLIB"]
        assert STAKEHOLDERS["BUSINESS"]
        assert STAKEHOLDERS["UNIVERSITY"]


class TestQueryCount:
    """Tests for query library size."""

    def test_minimum_query_count(self):
        """Library has minimum required queries (18 from Epic 1)."""
        assert len(QUERIES) >= 18

    def test_queries_across_categories(self):
        """Queries are distributed across categories."""
        categories = {}
        for query in QUERIES.values():
            cat = query.get('category', 'Unknown')
            categories[cat] = categories.get(cat, 0) + 1

        # Each category should have at least 2 queries
        for cat, count in categories.items():
            assert count >= 2, f"Category {cat} has only {count} queries"


class TestQueryParameters:
    """Tests for Story 1.8: Query-specific parameter system."""

    def test_all_queries_have_parameters_key(self):
        """Every query has a 'parameters' key (AC #1)."""
        for qid, query in QUERIES.items():
            assert 'parameters' in query, f"{qid} missing 'parameters' key"

    def test_parameters_is_dict(self):
        """Parameters must be a dict."""
        for qid, query in QUERIES.items():
            assert isinstance(query.get('parameters'), dict), f"{qid} parameters is not a dict"

    def test_parameter_types_are_valid(self):
        """All parameter types are valid (AC #1)."""
        valid_types = {'year_range', 'multiselect', 'select', 'text'}
        for qid, query in QUERIES.items():
            for param_name, param_config in query.get('parameters', {}).items():
                param_type = param_config.get('type')
                assert param_type in valid_types, \
                    f"{qid}.{param_name} has invalid type: {param_type}"

    def test_year_range_has_defaults(self):
        """year_range parameters have default_start and default_end."""
        for qid, query in QUERIES.items():
            for param_name, param_config in query.get('parameters', {}).items():
                if param_config.get('type') == 'year_range':
                    assert 'default_start' in param_config, \
                        f"{qid}.{param_name} missing default_start"
                    assert 'default_end' in param_config, \
                        f"{qid}.{param_name} missing default_end"

    def test_multiselect_has_options(self):
        """multiselect parameters have options defined."""
        for qid, query in QUERIES.items():
            for param_name, param_config in query.get('parameters', {}).items():
                if param_config.get('type') == 'multiselect':
                    options = param_config.get('options')
                    assert options is not None, \
                        f"{qid}.{param_name} missing options"
                    # Options can be a list or a reference string
                    valid_refs = {'jurisdictions', 'wipo_fields', 'tech_sectors', 'medtech_competitors'}
                    assert isinstance(options, list) or options in valid_refs, \
                        f"{qid}.{param_name} has invalid options: {options}"

    def test_select_has_options(self):
        """select parameters have options defined."""
        for qid, query in QUERIES.items():
            for param_name, param_config in query.get('parameters', {}).items():
                if param_config.get('type') == 'select':
                    options = param_config.get('options')
                    assert options is not None, \
                        f"{qid}.{param_name} missing options"
                    # Options can be a list or a reference string
                    valid_refs = {'jurisdictions', 'wipo_fields', 'tech_sectors', 'medtech_competitors'}
                    assert isinstance(options, list) or options in valid_refs, \
                        f"{qid}.{param_name} has invalid options: {options}"

    def test_q05_has_no_parameters(self):
        """Q05 (Sample Patents) should have empty parameters (AC #3)."""
        assert QUERIES['Q05']['parameters'] == {}, \
            "Q05 should have no parameters (empty dict)"

    def test_parameters_match_sql_template(self):
        """Queries with parameters must use them in sql_template (AC #4)."""
        for qid, query in QUERIES.items():
            params = query.get('parameters', {})
            sql_template = query.get('sql_template', '')

            if 'year_range' in params:
                assert '@year_start' in sql_template or '@year_end' in sql_template, \
                    f"{qid} has year_range param but sql_template doesn't use it"

            if 'jurisdictions' in params:
                assert '@jurisdictions' in sql_template, \
                    f"{qid} has jurisdictions param but sql_template doesn't use it"

            if 'tech_sector' in params:
                assert '@tech_sector' in sql_template, \
                    f"{qid} has tech_sector param but sql_template doesn't use it"

            if 'applicant_name' in params:
                assert '@applicant_name' in sql_template, \
                    f"{qid} has applicant_name param but sql_template doesn't use it"

            if 'competitors' in params:
                assert '@competitors' in sql_template, \
                    f"{qid} has competitors param but sql_template doesn't use it"

            if 'ipc_class' in params:
                assert '@ipc_class' in sql_template, \
                    f"{qid} has ipc_class param but sql_template doesn't use it"

    def test_parameter_count_reasonable(self):
        """Each query has 0-4 parameters typically (AC #5)."""
        for qid, query in QUERIES.items():
            param_count = len(query.get('parameters', {}))
            assert param_count <= 5, \
                f"{qid} has {param_count} parameters (typically 0-4)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
