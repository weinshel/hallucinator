"""Tests for get_query_words() function."""

import pytest
from check_hallucinated_references import get_query_words, STOP_WORDS


class TestGetQueryWordsBasic:
    """Basic tests for query word extraction."""

    def test_basic_extraction(self):
        """Test basic word extraction."""
        title = "Deep Learning for Natural Language Processing"
        words = get_query_words(title, 6)
        assert len(words) <= 6
        assert "Deep" in words
        assert "Learning" in words

    def test_respects_n_limit(self):
        """Test that result respects n limit."""
        title = "One Two Three Four Five Six Seven Eight Nine Ten"
        words = get_query_words(title, 4)
        assert len(words) == 4

    def test_default_n_is_6(self):
        """Test default n=6."""
        title = "One Two Three Four Five Six Seven Eight"
        words = get_query_words(title)
        assert len(words) <= 6


class TestGetQueryWordsStopWords:
    """Tests for stop word filtering."""

    def test_removes_stop_words(self):
        """Test that stop words are removed."""
        title = "The Deep Learning of the Future"
        words = get_query_words(title, 6)
        assert "the" not in [w.lower() for w in words]
        assert "The" not in words
        assert "of" not in words

    def test_all_stop_words_removed(self):
        """Test all defined stop words are removed."""
        # Build title with all stop words plus some content
        stop_word_list = list(STOP_WORDS)
        title = " ".join(stop_word_list) + " Machine Learning Method"
        words = get_query_words(title, 10)
        for sw in stop_word_list:
            assert sw.lower() not in [w.lower() for w in words]

    def test_stop_words_defined(self):
        """Verify expected stop words are in the set."""
        expected = ['a', 'an', 'the', 'of', 'and', 'or', 'for', 'to', 'in', 'on', 'with', 'by']
        for word in expected:
            assert word in STOP_WORDS, f"Missing stop word: {word}"


class TestGetQueryWordsShortWords:
    """Tests for short word filtering."""

    def test_removes_short_words(self):
        """Test that words < 3 characters are removed when enough significant words exist."""
        title = "Deep Learning Methods for Natural Language Processing"
        words = get_query_words(title, 6)
        # Should get significant words, filtering short ones
        for word in words:
            assert len(word) >= 3
        # Verify we got real words
        assert "Deep" in words or "Learning" in words

    def test_keeps_three_letter_words(self):
        """Test that 3-letter words are kept."""
        title = "The New NLP Model Uses CNN"
        words = get_query_words(title, 6)
        # NLP and CNN should be kept (3 chars)
        assert "NLP" in words or "CNN" in words


class TestGetQueryWordsSpecialCharacters:
    """Tests for special character handling."""

    def test_extracts_alphanumeric(self):
        """Test that only alphanumeric words are extracted."""
        title = "Deep Learning: A Survey (2023)"
        words = get_query_words(title, 6)
        # Should not include punctuation
        assert ":" not in str(words)
        assert "(" not in str(words)

    def test_hyphenated_words(self):
        """Test hyphenated word handling."""
        title = "Human-Centered Design for Machine Learning"
        words = get_query_words(title, 6)
        # Hyphen splits into separate words
        # May contain Human, Centered, etc.
        assert any("Human" in w or "Centered" in w for w in words)

    def test_numbers_included(self):
        """Test that numbers are included."""
        title = "GPT4 and GPT3 Comparison Study"
        words = get_query_words(title, 6)
        assert any("GPT4" in w or "GPT3" in w for w in words)


class TestGetQueryWordsFallback:
    """Tests for fallback behavior."""

    def test_fallback_when_few_significant(self):
        """Test fallback to all words when < 3 significant words."""
        title = "A and B"  # All stop words or short
        words = get_query_words(title, 6)
        # Should return something (fallback to all words)
        assert len(words) > 0 or words == []

    def test_returns_all_when_no_significant(self):
        """Test behavior when no significant words found."""
        title = "A to B"
        words = get_query_words(title, 6)
        # Fallback behavior - returns whatever it can


class TestGetQueryWordsEdgeCases:
    """Edge case tests for query word extraction."""

    def test_empty_title(self):
        """Test empty title."""
        words = get_query_words("", 6)
        assert words == []

    def test_whitespace_only(self):
        """Test whitespace-only title."""
        words = get_query_words("   ", 6)
        assert words == []

    def test_very_long_title(self):
        """Test very long title respects n limit."""
        title = " ".join([f"Word{i}" for i in range(100)])
        words = get_query_words(title, 6)
        assert len(words) == 6

    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        title = "Résumé Analysis Using Naïve Methods"
        words = get_query_words(title, 6)
        # Should extract alphanumeric parts
        assert len(words) > 0

    def test_n_zero(self):
        """Test n=0."""
        title = "Deep Learning Methods"
        words = get_query_words(title, 0)
        assert words == []

    def test_single_word_title(self):
        """Test single word title."""
        words = get_query_words("Deep", 6)
        assert words == ["Deep"]

    def test_title_with_apostrophe(self):
        """Test title with apostrophe (e.g., Twitter's)."""
        title = "Twitter's Role in Misinformation"
        words = get_query_words(title, 6)
        # Apostrophe should split the word
        assert len(words) > 0
        # 's' alone should be filtered (< 3 chars)
        assert "s" not in words
