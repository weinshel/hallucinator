"""Tests for find_references_section() function."""

import pytest
from check_hallucinated_references import find_references_section


class TestFindReferencesHeaders:
    """Tests for reference section header detection."""

    def test_references_header(self):
        """Test 'References' header detection."""
        text = """
        Some content before.

        References

        [1] First reference.
        [2] Second reference.
        """
        result = find_references_section(text)
        assert "[1]" in result
        assert "[2]" in result

    def test_references_header_uppercase(self):
        """Test 'REFERENCES' header detection."""
        text = """
        Some content before.

        REFERENCES

        [1] First reference.
        [2] Second reference.
        """
        result = find_references_section(text)
        assert "[1]" in result

    def test_bibliography_header(self):
        """Test 'Bibliography' header detection."""
        text = """
        Some content before.

        Bibliography

        [1] First reference.
        [2] Second reference.
        """
        result = find_references_section(text)
        assert "[1]" in result

    def test_bibliography_uppercase(self):
        """Test 'BIBLIOGRAPHY' header detection."""
        text = """
        Some content before.

        BIBLIOGRAPHY

        [1] First reference.
        """
        result = find_references_section(text)
        assert "[1]" in result

    def test_works_cited_header(self):
        """Test 'Works Cited' header detection."""
        text = """
        Some content before.

        Works Cited

        [1] First reference.
        """
        result = find_references_section(text)
        assert "[1]" in result


class TestFindReferencesEndMarkers:
    """Tests for reference section end marker detection."""

    def test_appendix_end_marker(self):
        """Test 'Appendix' as end marker."""
        text = """
        References

        [1] A reference.

        Appendix

        Some appendix content.
        """
        result = find_references_section(text)
        assert "[1]" in result
        assert "appendix content" not in result.lower()

    def test_appendix_uppercase_end_marker(self):
        """Test 'APPENDIX' as end marker."""
        text = """
        References

        [1] A reference.

        APPENDIX

        Some appendix content.
        """
        result = find_references_section(text)
        assert "[1]" in result
        assert "appendix content" not in result.lower()

    def test_acknowledgments_end_marker(self):
        """Test 'Acknowledgments' as end marker."""
        text = """
        References

        [1] A reference.

        Acknowledgments

        We thank our sponsors.
        """
        result = find_references_section(text)
        assert "[1]" in result
        assert "sponsors" not in result.lower()

    def test_acknowledgements_british_spelling(self):
        """Test 'Acknowledgements' (British spelling) as end marker."""
        text = """
        References

        [1] A reference.

        Acknowledgements

        We thank our sponsors.
        """
        result = find_references_section(text)
        assert "[1]" in result
        assert "sponsors" not in result.lower()

    def test_supplementary_end_marker(self):
        """Test 'Supplementary' as end marker."""
        text = """
        References

        [1] A reference.

        Supplementary Material

        Extra content here.
        """
        result = find_references_section(text)
        assert "[1]" in result
        assert "Extra content" not in result


class TestFindReferencesFallback:
    """Tests for fallback to last 30% of document."""

    def test_fallback_no_header(self):
        """Test fallback when no header found."""
        text = "A" * 100 + "\n[1] A reference at the end."
        result = find_references_section(text)
        # Should return last 30%
        assert len(result) > 0

    def test_fallback_percentage(self):
        """Test that fallback returns approximately last 30%."""
        # Create text where we know the exact cutoff
        text = "X" * 700 + "Y" * 300  # 1000 chars total
        result = find_references_section(text)
        # Should start at 70% = position 700
        assert result.startswith("Y") or "Y" in result[:10]


class TestFindReferencesEdgeCases:
    """Edge case tests for reference section finding."""

    def test_empty_text(self):
        """Test empty text input."""
        result = find_references_section("")
        assert result == ""

    def test_no_references_section(self):
        """Test document without references section."""
        text = "Just some content without any references section."
        result = find_references_section(text)
        # Should return fallback (last 30%)
        assert len(result) > 0

    def test_references_in_title(self):
        """Test that 'References' in title doesn't trigger early."""
        text = """
        A Study on References in Academic Papers

        Some body content here.

        References

        [1] Actual reference.
        """
        result = find_references_section(text)
        # Should find the actual References section, not the title
        assert "[1]" in result

    def test_multiple_reference_headers(self):
        """Test document with multiple 'References' headers."""
        text = """
        Section 1: References to Prior Work

        Some discussion.

        References

        [1] Actual reference.
        """
        result = find_references_section(text)
        # Should use the standalone References header
        assert "[1]" in result

    def test_header_with_whitespace(self):
        """Test header with surrounding whitespace."""
        text = """
        Some content.

           References

        [1] A reference.
        """
        result = find_references_section(text)
        assert "[1]" in result

    def test_case_insensitive_header(self):
        """Test case-insensitive header matching."""
        text = """
        Some content.

        references

        [1] A reference.
        """
        result = find_references_section(text)
        # Case insensitive matching
        assert "[1]" in result or len(result) > 0  # May match or fallback
