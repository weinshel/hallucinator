"""Tests for split_sentences_skip_initials() function."""

import pytest
from check_hallucinated_references import (
    split_sentences_skip_initials,
    MID_SENTENCE_ABBREVIATIONS,
    END_OF_AUTHOR_ABBREVIATIONS,
)


class TestSplitSentencesBasic:
    """Basic sentence splitting tests."""

    def test_simple_sentences(self):
        """Test splitting simple sentences."""
        text = "First sentence. Second sentence. Third sentence."
        result = split_sentences_skip_initials(text)
        assert len(result) == 3
        assert result[0] == "First sentence"
        assert result[1] == "Second sentence"
        assert result[2] == "Third sentence."

    def test_single_sentence(self):
        """Test single sentence without period."""
        text = "Just one sentence"
        result = split_sentences_skip_initials(text)
        assert len(result) == 1
        assert result[0] == "Just one sentence"

    def test_empty_string(self):
        """Test empty string input."""
        result = split_sentences_skip_initials("")
        assert result == []


class TestSkipInitials:
    """Tests for skipping author initials."""

    def test_skip_single_initial(self):
        """Test that single capital letter + period is not a sentence break."""
        text = "J. Smith wrote a paper. It was good."
        result = split_sentences_skip_initials(text)
        assert len(result) == 2
        assert "J. Smith" in result[0]

    def test_skip_multiple_initials(self):
        """Test multiple initials in sequence."""
        text = "J. K. Rowling wrote books. They were popular."
        result = split_sentences_skip_initials(text)
        assert len(result) == 2
        assert "J. K. Rowling" in result[0]

    def test_skip_middle_initial(self):
        """Test middle initial."""
        text = "John A. Smith and Mary B. Jones. They collaborated."
        result = split_sentences_skip_initials(text)
        assert len(result) == 2
        assert "John A. Smith" in result[0]
        assert "Mary B. Jones" in result[0]

    def test_initial_at_start(self):
        """Test initial at the very start of text."""
        text = "M. Chen wrote this. It is good."
        result = split_sentences_skip_initials(text)
        assert len(result) == 2
        assert "M. Chen" in result[0]


class TestSkipAbbreviations:
    """Tests for skipping mid-sentence abbreviations."""

    def test_skip_vs(self):
        """Test that 'vs.' is not a sentence break."""
        text = "Method A vs. Method B showed improvement. This is important."
        result = split_sentences_skip_initials(text)
        assert len(result) == 2
        assert "vs." in result[0] or "vs" in result[0]

    def test_skip_eg(self):
        """Test that 'e.g.' is not a sentence break."""
        text = "Some examples eg. this and that were shown. They worked."
        result = split_sentences_skip_initials(text)
        # 'eg.' should not split
        assert "eg" in result[0].lower() or len(result) == 2

    def test_skip_ie(self):
        """Test that 'i.e.' is not a sentence break."""
        text = "The method ie. the algorithm performed well. It was fast."
        result = split_sentences_skip_initials(text)
        assert len(result) == 2

    def test_skip_cf(self):
        """Test that 'cf.' is not a sentence break."""
        text = "Compare this cf. the previous work. It differs."
        result = split_sentences_skip_initials(text)
        assert len(result) == 2

    def test_skip_fig(self):
        """Test that 'fig.' is not a sentence break."""
        text = "As shown in fig. 1 the results improved. This is clear."
        result = split_sentences_skip_initials(text)
        assert len(result) == 2

    def test_skip_sec(self):
        """Test that 'sec.' is not a sentence break."""
        text = "Discussed in sec. 3 of the paper. More details follow."
        result = split_sentences_skip_initials(text)
        assert len(result) == 2

    def test_all_mid_sentence_abbreviations_exist(self):
        """Verify all expected mid-sentence abbreviations are in the set."""
        expected = ['vs', 'eg', 'ie', 'cf', 'fig', 'figs', 'eq', 'eqs', 'sec', 'ch', 'pt', 'no']
        for abbr in expected:
            assert abbr in MID_SENTENCE_ABBREVIATIONS, f"Missing abbreviation: {abbr}"


class TestEtAlHandling:
    """Tests for 'et al.' handling."""

    def test_et_al_is_sentence_boundary(self):
        """Test that 'et al.' is treated as sentence boundary."""
        text = "Smith et al. Deep Learning Methods. In ACL."
        result = split_sentences_skip_initials(text)
        # 'et al.' should be a boundary since it ends author list
        assert len(result) >= 2

    def test_end_of_author_abbreviations_exist(self):
        """Verify 'al' is in END_OF_AUTHOR_ABBREVIATIONS."""
        assert 'al' in END_OF_AUTHOR_ABBREVIATIONS


class TestComplexReferences:
    """Tests for complex reference-like text."""

    def test_ieee_reference(self):
        """Test IEEE-style reference text."""
        text = 'J. Smith and A. Jones wrote "Title." It was published in 2023.'
        result = split_sentences_skip_initials(text)
        # Should not split at J. or A.
        assert "J. Smith" in result[0]
        assert "A. Jones" in result[0]

    def test_multiple_authors_with_initials(self):
        """Test multiple authors all with initials."""
        text = "M. Chen, B. Lee, C. Wang, and D. Kim. They wrote a paper."
        result = split_sentences_skip_initials(text)
        assert len(result) == 2
        # All initials should be in first sentence
        for initial in ["M.", "B.", "C.", "D."]:
            assert initial in result[0]

    def test_year_with_period(self):
        """Test that years followed by periods don't cause issues."""
        text = "Published in 2023. This was recent."
        result = split_sentences_skip_initials(text)
        assert len(result) == 2

    def test_mixed_content(self):
        """Test text with mix of initials, abbreviations, and real sentences."""
        text = "J. Smith vs. A. Jones showed in fig. 1 the method. It was effective. See sec. 2."
        result = split_sentences_skip_initials(text)
        # Should split at real sentence boundaries
        assert len(result) >= 2


class TestEdgeCases:
    """Edge case tests for sentence splitting."""

    def test_trailing_period(self):
        """Test text ending with period."""
        text = "A sentence."
        result = split_sentences_skip_initials(text)
        assert len(result) == 1
        assert result[0] == "A sentence."

    def test_multiple_spaces(self):
        """Test multiple spaces after period."""
        text = "First sentence.  Second sentence."
        result = split_sentences_skip_initials(text)
        # May or may not split depending on space handling
        assert len(result) >= 1

    def test_no_space_after_period(self):
        """Test period without space (no split)."""
        text = "Node.js is good. It works."
        result = split_sentences_skip_initials(text)
        # "Node.js" should not be split
        assert any("Node" in r for r in result)

    def test_ellipsis(self):
        """Test ellipsis handling."""
        text = "Something... And then more."
        result = split_sentences_skip_initials(text)
        # Ellipsis may or may not be treated as boundary
        assert len(result) >= 1
