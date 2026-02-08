"""Tests for Story 2-1: Query Search and Filter functionality."""

import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.logic import filter_queries
from modules.config import STAKEHOLDER_TAGS, CATEGORIES


# Test data - simplified query structures
SAMPLE_QUERIES = {
    "Q01": {
        "title": "What are the overall PATSTAT database statistics?",
        "description": "Overall PATSTAT database statistics and key metrics",
        "tags": ["PATLIB"],
        "category": "Trends"
    },
    "Q06": {
        "title": "Which countries lead in patent filing activity?",
        "description": "Which countries have the highest patent application activity?",
        "tags": ["PATLIB", "BUSINESS"],
        "category": "Competitors"
    },
    "Q07": {
        "title": "What are the green technology trends by country?",
        "description": "Patent activity with green technology (CPC Y02) focus by country",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "category": "Trends"
    },
    "Q15": {
        "title": "Which German states lead in medical tech patents?",
        "description": "German Federal states patent activity in A61B (Diagnosis/Surgery)",
        "tags": ["PATLIB"],
        "category": "Regional"
    },
}


class TestFilterQueriesSearch:
    """Tests for search term filtering (AC #1)."""

    def test_filter_by_title_match(self):
        """Search term matches title - case insensitive."""
        result = filter_queries(SAMPLE_QUERIES, search_term="german")
        assert "Q15" in result
        assert len(result) == 1

    def test_filter_by_description_match(self):
        """Search term matches description."""
        result = filter_queries(SAMPLE_QUERIES, search_term="green technology")
        assert "Q07" in result
        assert len(result) == 1

    def test_filter_by_tag_match(self):
        """Search term matches tags."""
        result = filter_queries(SAMPLE_QUERIES, search_term="university")
        assert "Q07" in result
        assert len(result) == 1

    def test_filter_case_insensitive(self):
        """Search is case insensitive."""
        result_lower = filter_queries(SAMPLE_QUERIES, search_term="patstat")
        result_upper = filter_queries(SAMPLE_QUERIES, search_term="PATSTAT")
        assert result_lower == result_upper
        assert "Q01" in result_lower

    def test_filter_partial_match(self):
        """Partial word matching works."""
        result = filter_queries(SAMPLE_QUERIES, search_term="count")
        assert "Q06" in result  # "countries" contains "count"

    def test_filter_by_query_id(self):
        """Search matches query ID."""
        result = filter_queries(SAMPLE_QUERIES, search_term="q07")
        assert "Q07" in result
        assert len(result) == 1

    def test_filter_empty_search(self):
        """Empty search returns all queries."""
        result = filter_queries(SAMPLE_QUERIES, search_term="")
        assert len(result) == len(SAMPLE_QUERIES)

    def test_filter_none_search(self):
        """None search returns all queries."""
        result = filter_queries(SAMPLE_QUERIES, search_term=None)
        assert len(result) == len(SAMPLE_QUERIES)

    def test_filter_whitespace_search(self):
        """Whitespace-only search returns all queries."""
        result = filter_queries(SAMPLE_QUERIES, search_term="   ")
        assert len(result) == len(SAMPLE_QUERIES)

    def test_filter_no_match(self):
        """Search with no matches returns empty dict."""
        result = filter_queries(SAMPLE_QUERIES, search_term="xyznonexistent")
        assert len(result) == 0


class TestFilterQueriesCategory:
    """Tests for category filtering."""

    def test_filter_by_category(self):
        """Filter by single category."""
        result = filter_queries(SAMPLE_QUERIES, category="Trends")
        assert "Q01" in result
        assert "Q07" in result
        assert "Q06" not in result
        assert "Q15" not in result

    def test_filter_category_competitors(self):
        """Filter by Competitors category."""
        result = filter_queries(SAMPLE_QUERIES, category="Competitors")
        assert "Q06" in result
        assert len(result) == 1

    def test_filter_category_regional(self):
        """Filter by Regional category."""
        result = filter_queries(SAMPLE_QUERIES, category="Regional")
        assert "Q15" in result
        assert len(result) == 1

    def test_filter_none_category(self):
        """None category returns all queries."""
        result = filter_queries(SAMPLE_QUERIES, category=None)
        assert len(result) == len(SAMPLE_QUERIES)


class TestFilterQueriesStakeholder:
    """Tests for stakeholder tag filtering (AC #2)."""

    def test_filter_by_single_stakeholder(self):
        """Filter by single stakeholder tag."""
        result = filter_queries(SAMPLE_QUERIES, stakeholders=["PATLIB"])
        assert "Q01" in result
        assert "Q06" in result
        assert "Q15" in result
        assert "Q07" not in result  # Q07 has BUSINESS, UNIVERSITY but not PATLIB

    def test_filter_by_multiple_stakeholders(self):
        """Filter by multiple stakeholder tags (OR logic)."""
        result = filter_queries(SAMPLE_QUERIES, stakeholders=["PATLIB", "UNIVERSITY"])
        assert "Q01" in result  # PATLIB
        assert "Q07" in result  # UNIVERSITY
        assert "Q15" in result  # PATLIB

    def test_filter_by_business(self):
        """Filter by BUSINESS tag."""
        result = filter_queries(SAMPLE_QUERIES, stakeholders=["BUSINESS"])
        assert "Q06" in result
        assert "Q07" in result

    def test_filter_empty_stakeholders(self):
        """Empty stakeholder list returns all queries."""
        result = filter_queries(SAMPLE_QUERIES, stakeholders=[])
        assert len(result) == len(SAMPLE_QUERIES)

    def test_filter_none_stakeholders(self):
        """None stakeholders returns all queries."""
        result = filter_queries(SAMPLE_QUERIES, stakeholders=None)
        assert len(result) == len(SAMPLE_QUERIES)


class TestFilterQueriesCombined:
    """Tests for combined filtering (AC #2)."""

    def test_combined_search_and_category(self):
        """Search + category filter work together."""
        result = filter_queries(SAMPLE_QUERIES, search_term="country", category="Trends")
        assert "Q07" in result  # "country" in title, category=Trends
        assert "Q06" not in result  # "country" in title, but category=Competitors

    def test_combined_search_and_stakeholder(self):
        """Search + stakeholder filter work together."""
        result = filter_queries(SAMPLE_QUERIES, search_term="technology", stakeholders=["BUSINESS"])
        assert "Q07" in result  # "technology" in title, has BUSINESS tag
        assert len(result) == 1

    def test_combined_category_and_stakeholder(self):
        """Category + stakeholder filter work together."""
        result = filter_queries(SAMPLE_QUERIES, category="Trends", stakeholders=["BUSINESS"])
        assert "Q07" in result
        assert "Q01" not in result  # Category=Trends but no BUSINESS tag

    def test_combined_all_filters(self):
        """All three filters work together."""
        result = filter_queries(
            SAMPLE_QUERIES,
            search_term="green",
            category="Trends",
            stakeholders=["UNIVERSITY"]
        )
        assert "Q07" in result
        assert len(result) == 1

    def test_combined_filters_no_match(self):
        """Combined filters with no intersection return empty."""
        result = filter_queries(
            SAMPLE_QUERIES,
            search_term="german",
            category="Trends",  # Q15 is Regional, not Trends
            stakeholders=["PATLIB"]
        )
        assert len(result) == 0


class TestStakeholderTags:
    """Tests for stakeholder tag constants."""

    def test_stakeholder_tags_defined(self):
        """STAKEHOLDER_TAGS constant is defined."""
        assert STAKEHOLDER_TAGS is not None
        assert len(STAKEHOLDER_TAGS) == 3

    def test_stakeholder_tags_values(self):
        """STAKEHOLDER_TAGS contains expected values."""
        assert "PATLIB" in STAKEHOLDER_TAGS
        assert "BUSINESS" in STAKEHOLDER_TAGS
        assert "UNIVERSITY" in STAKEHOLDER_TAGS


class TestCategories:
    """Tests for category constants."""

    def test_categories_defined(self):
        """CATEGORIES constant is defined."""
        assert CATEGORIES is not None
        assert len(CATEGORIES) == 5

    def test_categories_values(self):
        """CATEGORIES contains expected values."""
        assert "Competitors" in CATEGORIES
        assert "Trends" in CATEGORIES
        assert "Regional" in CATEGORIES
        assert "Technology" in CATEGORIES
        assert "Classification" in CATEGORIES


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
