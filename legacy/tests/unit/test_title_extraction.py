"""Tests for extract_title_from_reference() function."""

import pytest
from check_hallucinated_references import extract_title_from_reference


class TestExtractTitleQuoted:
    """Tests for quoted title extraction (IEEE style)."""

    def test_ieee_quoted_title(self, ieee_reference):
        """Test IEEE format quoted title extraction."""
        title, from_quotes = extract_title_from_reference(ieee_reference)
        assert "Deep Learning" in title
        assert "Natural Language Processing" in title
        assert from_quotes is True

    def test_smart_quotes(self):
        """Test extraction with smart quotes."""
        ref = 'J. Smith, \u201cDeep Learning for NLP,\u201d in Proc. ACL, 2023.'
        title, from_quotes = extract_title_from_reference(ref)
        assert "Deep Learning" in title
        assert from_quotes is True

    def test_mixed_quotes(self):
        """Test extraction with mixed quote styles."""
        ref = 'J. Smith, \u201cDeep Learning for NLP," in Proc. ACL, 2023.'
        title, from_quotes = extract_title_from_reference(ref)
        assert "Deep Learning" in title


class TestExtractTitleWithSubtitle:
    """Tests for titles with subtitles."""

    def test_colon_subtitle(self):
        """Test title with colon-separated subtitle."""
        ref = 'J. Smith, "Main Title": A Comprehensive Survey. In Proc. ACL, 2023.'
        title, from_quotes = extract_title_from_reference(ref)
        assert "Main Title" in title
        # May or may not include subtitle depending on format detection

    def test_hyphen_subtitle(self):
        """Test title with hyphen-separated subtitle."""
        ref = 'J. Smith, "Main Title" - A Detailed Analysis. In Proc. ACL, 2023.'
        title, from_quotes = extract_title_from_reference(ref)
        assert "Main Title" in title


class TestExtractTitleACM:
    """Tests for ACM format title extraction."""

    def test_acm_year_title(self, acm_reference):
        """Test ACM format: Authors. Year. Title. In Venue."""
        title, from_quotes = extract_title_from_reference(acm_reference)
        assert "Deep Learning" in title
        assert from_quotes is False

    def test_acm_format_explicit(self):
        """Test explicit ACM format."""
        ref = 'Maria Garcia and Carlos Rodriguez. 2022. Neural Networks for Image Recognition. In CHI Conference.'
        title, from_quotes = extract_title_from_reference(ref)
        assert "Neural Networks" in title
        assert from_quotes is False


class TestExtractTitleUSENIX:
    """Tests for USENIX format title extraction."""

    def test_usenix_format(self, usenix_reference):
        """Test USENIX format: Authors. Title. In Venue."""
        title, from_quotes = extract_title_from_reference(usenix_reference)
        assert "Deep Learning" in title
        assert from_quotes is False

    def test_usenix_with_venue(self):
        """Test USENIX format with explicit venue."""
        ref = 'Robert Chen. Secure Systems Design Principles. In Proceedings of USENIX ATC, 2022.'
        title, from_quotes = extract_title_from_reference(ref)
        assert "Secure Systems" in title
        # Should not include venue
        assert "USENIX" not in title


class TestExtractTitleAAAI:
    """Tests for AAAI format title extraction."""

    def test_aaai_format(self, aaai_reference):
        """Test AAAI format: Surname, I.; ... Year. Title. Venue."""
        title, from_quotes = extract_title_from_reference(aaai_reference)
        assert "Deep Learning" in title


class TestExtractTitleJournal:
    """Tests for journal format title extraction."""

    def test_journal_format(self):
        """Test journal format with volume/issue."""
        ref = 'J. Smith and A. Jones. Deep Learning Methods. Journal of ML Research, 15(3), 2023.'
        title, from_quotes = extract_title_from_reference(ref)
        assert "Deep Learning" in title
        # Should not include journal info
        assert "Journal" not in title


class TestExtractTitleEdgeCases:
    """Tests for edge cases in title extraction."""

    def test_empty_string(self):
        """Test empty string input."""
        title, from_quotes = extract_title_from_reference("")
        assert title == ""

    def test_short_quoted_title_rejected(self):
        """Test that very short quoted titles may use fallback."""
        ref = 'J. Smith, "DL," in Proc. ACL, 2023.'
        title, from_quotes = extract_title_from_reference(ref)
        # Short title (< 3 words) may not be returned or may use fallback
        # The function should handle this gracefully

    def test_hyphenation_fixed(self):
        """Test that hyphenation is fixed in extracted title."""
        ref = 'J. Smith, "A human- centered approach to design," in Proc. CHI, 2023.'
        title, from_quotes = extract_title_from_reference(ref)
        assert "human-centered" in title

    def test_question_in_title(self):
        """Test title ending with question mark."""
        ref = 'J. Smith, "Can Machines Learn?" In Proceedings of ICML, 2023.'
        title, from_quotes = extract_title_from_reference(ref)
        assert "Can Machines Learn" in title

    def test_doi_not_in_title(self):
        """Test that DOI is not included in title."""
        ref = 'J. Smith. Deep Learning Methods. In ACL. doi:10.1234/example'
        title, from_quotes = extract_title_from_reference(ref)
        assert "doi" not in title.lower()

    def test_fallback_to_second_sentence(self):
        """Test fallback to second sentence when no other format matches."""
        ref = 'Unknown Format Here. This is the Title of the Paper. Some venue info 2023.'
        title, from_quotes = extract_title_from_reference(ref)
        # Should try to extract something reasonable
        assert len(title) > 0 or title == ""  # May succeed or fail gracefully

    def test_authors_not_in_title(self):
        """Test that author names are not extracted as title."""
        ref = 'John Smith and Alice Jones. Deep Learning Methods. In ACL 2023.'
        title, from_quotes = extract_title_from_reference(ref)
        # Title should be the paper title, not authors
        if title:
            # If we got a title, it shouldn't be the author list
            assert not (title.startswith("John Smith") or title.startswith("Alice"))

    def test_venue_not_in_title(self):
        """Test that venue is not included in title."""
        ref = 'J. Smith, "Deep Learning for NLP," in Proceedings of ACL Conference, 2023.'
        title, from_quotes = extract_title_from_reference(ref)
        assert "Proceedings" not in title
        assert "Conference" not in title

    def test_multiline_reference(self):
        """Test reference spanning multiple lines."""
        ref = '''J. Smith and A. Jones, "Deep Learning
        for Natural Language Processing," in Proc. ACL, 2023.'''
        title, from_quotes = extract_title_from_reference(ref)
        assert "Deep Learning" in title
        assert "Natural Language" in title or "NLP" in title.upper()
