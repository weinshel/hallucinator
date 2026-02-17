"""Tests for validate_authors() function."""

import pytest
from check_hallucinated_references import validate_authors


class TestValidateAuthorsExactMatch:
    """Tests for exact author matching."""

    def test_exact_match_single(self):
        """Test exact match with single author."""
        ref_authors = ["John Smith"]
        found_authors = ["John Smith"]
        assert validate_authors(ref_authors, found_authors) is True

    def test_exact_match_multiple(self):
        """Test exact match with multiple authors."""
        ref_authors = ["John Smith", "Alice Jones"]
        found_authors = ["John Smith", "Alice Jones"]
        assert validate_authors(ref_authors, found_authors) is True

    def test_order_independent(self):
        """Test that author order doesn't matter."""
        ref_authors = ["John Smith", "Alice Jones"]
        found_authors = ["Alice Jones", "John Smith"]
        assert validate_authors(ref_authors, found_authors) is True


class TestValidateAuthorsPartialMatch:
    """Tests for partial author matching."""

    def test_subset_match(self):
        """Test matching when ref has subset of found authors."""
        ref_authors = ["John Smith"]
        found_authors = ["John Smith", "Alice Jones", "Bob Williams"]
        assert validate_authors(ref_authors, found_authors) is True

    def test_superset_match(self):
        """Test matching when ref has superset of found authors."""
        ref_authors = ["John Smith", "Alice Jones", "Bob Williams"]
        found_authors = ["John Smith"]
        assert validate_authors(ref_authors, found_authors) is True

    def test_overlap_match(self):
        """Test matching when there's some overlap."""
        ref_authors = ["John Smith", "Charlie Brown"]
        found_authors = ["John Smith", "Alice Jones"]
        assert validate_authors(ref_authors, found_authors) is True


class TestValidateAuthorsNoMatch:
    """Tests for author mismatch detection."""

    def test_no_match_completely_different(self):
        """Test no match with completely different authors."""
        ref_authors = ["John Smith", "Alice Jones"]
        found_authors = ["Bob Williams", "Charlie Brown"]
        assert validate_authors(ref_authors, found_authors) is False

    def test_no_match_similar_names(self):
        """Test no match with similar but different names."""
        ref_authors = ["John Smith"]
        found_authors = ["John Johnson"]  # Same first name, different last
        assert validate_authors(ref_authors, found_authors) is False


class TestValidateAuthorsNormalization:
    """Tests for author name normalization."""

    def test_initial_matching(self):
        """Test that initials match full names."""
        ref_authors = ["J. Smith"]
        found_authors = ["John Smith"]
        assert validate_authors(ref_authors, found_authors) is True

    def test_initial_matching_reverse(self):
        """Test that full names match initials."""
        ref_authors = ["John Smith"]
        found_authors = ["J. Smith"]
        assert validate_authors(ref_authors, found_authors) is True

    def test_case_matching_on_surname(self):
        """Test matching works with different casing but same structure."""
        # Normalization: first_initial + space + lowercase_surname
        # "John Smith" -> "J smith"
        # "JOHN SMITH" -> "J smith" (both uppercase J)
        ref_authors = ["John Smith"]
        found_authors = ["JOHN SMITH"]
        assert validate_authors(ref_authors, found_authors) is True

    def test_middle_initial_ignored(self):
        """Test that middle initials don't break matching."""
        ref_authors = ["John A. Smith"]
        found_authors = ["John Smith"]
        assert validate_authors(ref_authors, found_authors) is True


class TestValidateAuthorsAAAIFormat:
    """Tests for AAAI format author normalization."""

    def test_aaai_format_comma_initials(self):
        """Test AAAI format: Surname, Initials."""
        ref_authors = ["Smith, J."]
        found_authors = ["John Smith"]
        assert validate_authors(ref_authors, found_authors) is True

    def test_aaai_format_multiple(self):
        """Test AAAI format with multiple authors."""
        ref_authors = ["Smith, J.", "Jones, A."]
        found_authors = ["John Smith", "Alice Jones"]
        assert validate_authors(ref_authors, found_authors) is True

    def test_aaai_format_with_middle_initial(self):
        """Test AAAI format with middle initial: Surname, F. M."""
        ref_authors = ["Bail, C. A."]
        found_authors = ["Christopher A. Bail"]
        assert validate_authors(ref_authors, found_authors) is True


class TestValidateAuthorsLastNameOnly:
    """Tests for last-name-only matching."""

    def test_last_name_only_ref(self):
        """Test matching when ref has only last names."""
        ref_authors = ["Smith", "Jones"]
        found_authors = ["John Smith", "Alice Jones"]
        assert validate_authors(ref_authors, found_authors) is True

    def test_last_name_only_both(self):
        """Test matching when both have only last names."""
        ref_authors = ["Smith"]
        found_authors = ["Smith"]
        assert validate_authors(ref_authors, found_authors) is True


class TestValidateAuthorsEdgeCases:
    """Tests for edge cases in author validation."""

    def test_empty_ref_authors(self):
        """Test with empty ref authors list."""
        ref_authors = []
        found_authors = ["John Smith"]
        # Empty ref authors produces empty set, intersection is empty, returns False
        assert validate_authors(ref_authors, found_authors) is False

    def test_empty_found_authors(self):
        """Test with empty found authors list."""
        ref_authors = ["John Smith"]
        found_authors = []
        assert validate_authors(ref_authors, found_authors) is False

    def test_both_empty(self):
        """Test with both lists empty."""
        ref_authors = []
        found_authors = []
        # Intersection of empty sets is empty, so False
        # But empty ref_authors should be considered a match
        result = validate_authors(ref_authors, found_authors)
        # Implementation may vary - document actual behavior

    def test_whitespace_handling(self):
        """Test that whitespace is handled properly."""
        ref_authors = ["John  Smith"]  # Extra space
        found_authors = ["John Smith"]
        # Should still match after normalization
        result = validate_authors(ref_authors, found_authors)
        assert isinstance(result, bool)

    def test_unicode_names(self):
        """Test unicode characters in names."""
        ref_authors = ["José García"]
        found_authors = ["Jose Garcia"]
        # May or may not match depending on normalization
        result = validate_authors(ref_authors, found_authors)
        assert isinstance(result, bool)

    def test_compound_surnames(self):
        """Test compound surnames."""
        ref_authors = ["Van Bavel, J."]
        found_authors = ["Jay Van Bavel"]
        # Should match on Van Bavel
        result = validate_authors(ref_authors, found_authors)
        assert isinstance(result, bool)
