"""Integration tests for database query functions with mocked HTTP responses."""

import pytest
import responses
import json
from unittest.mock import patch

from check_hallucinated_references import (
    query_crossref,
    query_arxiv,
    query_dblp,
    query_semantic_scholar,
    query_openalex,
    query_acl,
    query_neurips,
    normalize_title,
)

from tests.fixtures.mock_responses import (
    CROSSREF_SUCCESS,
    CROSSREF_NOT_FOUND,
    ARXIV_SUCCESS,
    ARXIV_NOT_FOUND,
    DBLP_SUCCESS,
    DBLP_NOT_FOUND,
    SEMANTIC_SCHOLAR_SUCCESS,
    SEMANTIC_SCHOLAR_NOT_FOUND,
    OPENALEX_SUCCESS,
    OPENALEX_NOT_FOUND,
    ACL_SUCCESS_HTML,
    ACL_NOT_FOUND_HTML,
    NEURIPS_INDEX_HTML,
    NEURIPS_PAPER_HTML,
    NEURIPS_NOT_FOUND_HTML,
)


class TestQueryCrossRef:
    """Tests for CrossRef API queries."""

    @responses.activate
    def test_crossref_success(self):
        """Test successful CrossRef query."""
        responses.add(
            responses.GET,
            "https://api.crossref.org/works",
            json=CROSSREF_SUCCESS,
            status=200,
        )

        title = "Deep Learning for Natural Language Processing"
        found_title, authors, url = query_crossref(title)

        assert found_title is not None
        assert len(authors) == 2
        assert any("Smith" in a for a in authors)
        assert url is not None
        assert "doi.org" in url

    @responses.activate
    def test_crossref_not_found(self):
        """Test CrossRef query with no results."""
        responses.add(
            responses.GET,
            "https://api.crossref.org/works",
            json=CROSSREF_NOT_FOUND,
            status=200,
        )

        title = "This Paper Does Not Exist At All"
        found_title, authors, url = query_crossref(title)

        assert found_title is None
        assert authors == []
        assert url is None

    @responses.activate
    def test_crossref_rate_limit(self):
        """Test CrossRef rate limiting (429)."""
        responses.add(
            responses.GET,
            "https://api.crossref.org/works",
            status=429,
        )

        title = "Some Paper Title"
        with pytest.raises(Exception) as exc_info:
            query_crossref(title)
        assert "429" in str(exc_info.value) or "Rate limited" in str(exc_info.value)

    @responses.activate
    def test_crossref_server_error(self):
        """Test CrossRef server error."""
        responses.add(
            responses.GET,
            "https://api.crossref.org/works",
            status=500,
        )

        title = "Some Paper Title"
        with pytest.raises(Exception):
            query_crossref(title)


class TestQueryArXiv:
    """Tests for arXiv API queries."""

    @responses.activate
    def test_arxiv_success(self):
        """Test successful arXiv query."""
        responses.add(
            responses.GET,
            "http://export.arxiv.org/api/query",
            body=ARXIV_SUCCESS,
            status=200,
        )

        title = "Deep Learning for Natural Language Processing"
        found_title, authors, url = query_arxiv(title)

        assert found_title is not None
        assert len(authors) == 2
        assert any("Smith" in a for a in authors)
        assert url is not None
        assert "arxiv.org" in url

    @responses.activate
    def test_arxiv_not_found(self):
        """Test arXiv query with no results."""
        responses.add(
            responses.GET,
            "http://export.arxiv.org/api/query",
            body=ARXIV_NOT_FOUND,
            status=200,
        )

        title = "This Paper Does Not Exist"
        found_title, authors, url = query_arxiv(title)

        assert found_title is None
        assert authors == []


class TestQueryDBLP:
    """Tests for DBLP API queries."""

    @responses.activate
    def test_dblp_success(self):
        """Test successful DBLP query."""
        responses.add(
            responses.GET,
            "https://dblp.org/search/publ/api",
            json=DBLP_SUCCESS,
            status=200,
        )

        title = "Deep Learning for Natural Language Processing"
        found_title, authors, url = query_dblp(title)

        assert found_title is not None
        assert len(authors) == 2
        assert any("Smith" in a for a in authors)
        assert url is not None

    @responses.activate
    def test_dblp_not_found(self):
        """Test DBLP query with no results."""
        responses.add(
            responses.GET,
            "https://dblp.org/search/publ/api",
            json=DBLP_NOT_FOUND,
            status=200,
        )

        title = "Nonexistent Paper Title"
        found_title, authors, url = query_dblp(title)

        assert found_title is None
        assert authors == []

    @responses.activate
    def test_dblp_rate_limit(self):
        """Test DBLP rate limiting."""
        responses.add(
            responses.GET,
            "https://dblp.org/search/publ/api",
            status=429,
        )

        title = "Some Paper"
        with pytest.raises(Exception):
            query_dblp(title)


class TestQuerySemanticScholar:
    """Tests for Semantic Scholar API queries."""

    @responses.activate
    def test_semantic_scholar_success(self):
        """Test successful Semantic Scholar query."""
        responses.add(
            responses.GET,
            "https://api.semanticscholar.org/graph/v1/paper/search",
            json=SEMANTIC_SCHOLAR_SUCCESS,
            status=200,
        )

        title = "Deep Learning for Natural Language Processing"
        found_title, authors, url = query_semantic_scholar(title)

        assert found_title is not None
        assert len(authors) == 2
        assert any("Smith" in a for a in authors)
        assert url is not None

    @responses.activate
    def test_semantic_scholar_not_found(self):
        """Test Semantic Scholar query with no results."""
        responses.add(
            responses.GET,
            "https://api.semanticscholar.org/graph/v1/paper/search",
            json=SEMANTIC_SCHOLAR_NOT_FOUND,
            status=200,
        )

        title = "Nonexistent Paper"
        found_title, authors, url = query_semantic_scholar(title)

        assert found_title is None
        assert authors == []

    @responses.activate
    def test_semantic_scholar_with_api_key(self):
        """Test Semantic Scholar with API key."""
        responses.add(
            responses.GET,
            "https://api.semanticscholar.org/graph/v1/paper/search",
            json=SEMANTIC_SCHOLAR_SUCCESS,
            status=200,
        )

        title = "Deep Learning for Natural Language Processing"
        found_title, authors, url = query_semantic_scholar(title, api_key="test-key")

        assert found_title is not None
        # Verify API key was used
        assert responses.calls[0].request.headers.get("x-api-key") == "test-key"


class TestQueryOpenAlex:
    """Tests for OpenAlex API queries."""

    @responses.activate
    def test_openalex_success(self):
        """Test successful OpenAlex query."""
        responses.add(
            responses.GET,
            "https://api.openalex.org/works",
            json=OPENALEX_SUCCESS,
            status=200,
        )

        title = "Deep Learning for Natural Language Processing"
        found_title, authors, url = query_openalex(title, api_key="test-key")

        assert found_title is not None
        assert len(authors) == 2
        assert any("Smith" in a for a in authors)

    @responses.activate
    def test_openalex_not_found(self):
        """Test OpenAlex query with no results."""
        responses.add(
            responses.GET,
            "https://api.openalex.org/works",
            json=OPENALEX_NOT_FOUND,
            status=200,
        )

        title = "Nonexistent Paper"
        found_title, authors, url = query_openalex(title, api_key="test-key")

        assert found_title is None
        assert authors == []


class TestQueryACL:
    """Tests for ACL Anthology queries."""

    @responses.activate
    def test_acl_success(self):
        """Test successful ACL Anthology query."""
        responses.add(
            responses.GET,
            "https://aclanthology.org/search/",
            body=ACL_SUCCESS_HTML,
            status=200,
        )

        title = "Deep Learning for Natural Language Processing"
        found_title, authors, url = query_acl(title)

        assert found_title is not None
        assert len(authors) == 2

    @responses.activate
    def test_acl_not_found(self):
        """Test ACL Anthology query with no results."""
        responses.add(
            responses.GET,
            "https://aclanthology.org/search/",
            body=ACL_NOT_FOUND_HTML,
            status=200,
        )

        title = "Nonexistent Paper"
        found_title, authors, url = query_acl(title)

        assert found_title is None


class TestQueryNeurIPS:
    """Tests for NeurIPS papers queries."""

    @responses.activate
    def test_neurips_success(self):
        """Test successful NeurIPS query."""
        # Mock the index page
        responses.add(
            responses.GET,
            "https://papers.nips.cc/paper_files/paper/2023/hash/index.html",
            body=NEURIPS_INDEX_HTML,
            status=200,
        )
        # Mock the paper page
        responses.add(
            responses.GET,
            "https://papers.nips.cc/paper_files/paper/2023/hash/abc123-Abstract.html",
            body=NEURIPS_PAPER_HTML,
            status=200,
        )

        title = "Deep Learning for Natural Language Processing"
        found_title, authors, url = query_neurips(title)

        assert found_title is not None
        assert len(authors) == 2

    @responses.activate
    def test_neurips_not_found(self):
        """Test NeurIPS query with no results."""
        # Mock empty index pages for all years
        for year in [2023, 2022, 2021, 2020, 2019, 2018]:
            responses.add(
                responses.GET,
                f"https://papers.nips.cc/paper_files/paper/{year}/hash/index.html",
                body=NEURIPS_NOT_FOUND_HTML,
                status=200,
            )

        title = "Nonexistent Paper"
        found_title, authors, url = query_neurips(title)

        assert found_title is None


class TestFuzzyMatching:
    """Tests for fuzzy title matching in queries."""

    @responses.activate
    def test_fuzzy_match_minor_difference(self):
        """Test that minor title differences still match."""
        # Return title with slightly different formatting
        response = {
            "status": "ok",
            "message": {
                "items": [
                    {
                        "title": ["Deep Learning for Natural-Language Processing"],  # Hyphenated
                        "author": [{"given": "John", "family": "Smith"}],
                        "DOI": "10.1234/test",
                    }
                ]
            }
        }
        responses.add(
            responses.GET,
            "https://api.crossref.org/works",
            json=response,
            status=200,
        )

        title = "Deep Learning for Natural Language Processing"  # No hyphen
        found_title, authors, url = query_crossref(title)

        # Should match due to 95% fuzzy threshold
        assert found_title is not None

    def test_normalize_title_for_comparison(self):
        """Test title normalization removes differences."""
        title1 = "Deep Learning for NLP"
        title2 = "Deep learning for NLP"  # Different case
        title3 = "Deep Learning for NLP!"  # With punctuation

        assert normalize_title(title1) == normalize_title(title2)
        assert normalize_title(title1) == normalize_title(title3)


class TestTimeoutHandling:
    """Tests for timeout handling in queries."""

    @responses.activate
    def test_timeout_raises_exception(self):
        """Test that timeout raises exception for tracking."""
        import requests

        responses.add(
            responses.GET,
            "https://api.crossref.org/works",
            body=requests.exceptions.Timeout("Connection timed out"),
        )

        title = "Some Paper"
        with pytest.raises(requests.exceptions.Timeout):
            query_crossref(title)
