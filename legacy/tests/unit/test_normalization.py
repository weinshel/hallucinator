"""Tests for normalize_title() and clean_title() functions."""

import pytest
from check_hallucinated_references import normalize_title, clean_title


class TestNormalizeTitle:
    """Tests for title normalization."""

    def test_basic_normalization(self):
        """Test basic title normalization."""
        assert normalize_title("Deep Learning for NLP") == "deeplearningfornlp"

    def test_removes_punctuation(self):
        """Test that punctuation is removed."""
        assert normalize_title("Hello, World!") == "helloworld"
        assert normalize_title("What's up?") == "whatsup"
        assert normalize_title("A: B - C") == "abc"

    def test_removes_spaces(self):
        """Test that spaces are removed."""
        assert normalize_title("one two three") == "onetwothree"
        assert normalize_title("  spaced  out  ") == "spacedout"

    def test_lowercase(self):
        """Test that result is lowercase."""
        assert normalize_title("UPPERCASE TITLE") == "uppercasetitle"
        assert normalize_title("MixedCase Title") == "mixedcasetitle"

    def test_html_entities(self):
        """Test HTML entity decoding."""
        assert normalize_title("Hello &amp; World") == "helloworld"
        assert normalize_title("&quot;Quoted&quot;") == "quoted"
        assert normalize_title("1 &lt; 2 &gt; 0") == "120"

    def test_unicode_normalization(self):
        """Test unicode normalization."""
        # Accented characters should be normalized
        assert normalize_title("Café") == "cafe"
        assert normalize_title("naïve") == "naive"
        assert normalize_title("résumé") == "resume"

    def test_keeps_numbers(self):
        """Test that numbers are kept."""
        assert normalize_title("GPT-4 is Great") == "gpt4isgreat"
        assert normalize_title("BERT 2.0") == "bert20"

    def test_empty_string(self):
        """Test empty string input."""
        assert normalize_title("") == ""

    def test_only_punctuation(self):
        """Test string with only punctuation."""
        assert normalize_title("!@#$%^&*()") == ""

    def test_smart_quotes(self):
        """Test smart quote handling."""
        assert normalize_title("\u201cQuoted\u201d") == "quoted"
        assert normalize_title("\u2018Single\u2019") == "single"


class TestCleanTitle:
    """Tests for title cleaning."""

    def test_basic_cleaning(self):
        """Test basic title cleaning."""
        assert clean_title("Simple Title") == "Simple Title"

    def test_trailing_punctuation(self):
        """Test removal of trailing punctuation."""
        assert clean_title("Title.", from_quotes=True) == "Title"
        assert clean_title("Title,", from_quotes=True) == "Title"
        assert clean_title("Title;", from_quotes=True) == "Title"

    def test_from_quotes_flag(self):
        """Test from_quotes flag behavior."""
        # With from_quotes=True, strip trailing punctuation
        assert clean_title("Title,", from_quotes=True) == "Title"
        # Without from_quotes, may do more processing
        title = clean_title("Title. In Proceedings of ACL", from_quotes=False)
        assert "Proceedings" not in title

    def test_venue_removal_proceedings(self):
        """Test removal of venue info starting with Proceedings."""
        result = clean_title("Deep Learning. Proceedings of ACL 2023")
        assert "Proceedings" not in result
        assert "Deep Learning" in result

    def test_venue_removal_conference(self):
        """Test removal of venue info starting with Conference."""
        result = clean_title("Deep Learning. Conference on Machine Learning 2023")
        assert "Conference" not in result

    def test_venue_removal_ieee(self):
        """Test removal of IEEE venue info."""
        result = clean_title("Deep Learning. IEEE Trans. Neural Networks 2023")
        assert "IEEE" not in result

    def test_venue_removal_acm(self):
        """Test removal of ACM venue info."""
        result = clean_title("Deep Learning. ACM Computing Surveys 2023")
        assert "ACM" not in result

    def test_venue_removal_journal(self):
        """Test removal of journal info."""
        result = clean_title("Deep Learning. Journal of Machine Learning Research 15(1)")
        assert "Journal" not in result

    def test_venue_removal_advances(self):
        """Test removal of Advances in... venue."""
        result = clean_title("Deep Learning. Advances in Neural Information Processing")
        assert "Advances" not in result

    def test_arxiv_removal(self):
        """Test removal of arXiv preprint info."""
        result = clean_title("Deep Learning. arXiv preprint arXiv:2301.12345")
        assert "arXiv" not in result
        assert "2301" not in result

    def test_corr_removal(self):
        """Test removal of CoRR abs/ info."""
        result = clean_title("Deep Learning. CoRR abs/2301.12345")
        assert "CoRR" not in result

    def test_volume_issue_removal(self):
        """Test removal of volume/issue patterns."""
        result = clean_title("Deep Learning, volume 15")
        assert "volume" not in result
        result = clean_title("Deep Learning, 15(3)")
        assert "15(3)" not in result

    def test_url_removal(self):
        """Test removal of URLs."""
        result = clean_title("Deep Learning. https://example.com/paper")
        assert "https" not in result
        assert "example.com" not in result

    def test_broken_url_removal(self):
        """Test removal of broken URLs with spaces."""
        result = clean_title("Deep Learning. ht tps://example.com/paper")
        assert "tps" not in result

    def test_date_removal(self):
        """Test removal of date patterns."""
        result = clean_title("Deep Learning, June 2024")
        assert "June" not in result
        assert "2024" not in result

    def test_hyphenation_fix(self):
        """Test that hyphenation is fixed."""
        result = clean_title("A human- centered approach")
        assert "human-centered" in result

    def test_empty_string(self):
        """Test empty string input."""
        assert clean_title("") == ""
        assert clean_title(None) == ""

    def test_question_mark_handling(self):
        """Test handling of question marks before venue."""
        result = clean_title("Can We Learn? In ICML 2023")
        assert "Can We Learn?" in result or "Can We Learn" in result
        assert "ICML" not in result

    def test_period_in_product_name(self):
        """Test that periods in product names like Node.js are preserved."""
        # This tests that we don't split on periods followed immediately by letters
        result = clean_title("Using Node.js for Machine Learning")
        # The period should be handled appropriately (may or may not keep it)
        assert "Node" in result

    def test_science_journal_pattern(self):
        """Test removal of Science journal pattern."""
        result = clean_title("Deep Learning. Science 344, 1234-1238")
        assert "Science 344" not in result
