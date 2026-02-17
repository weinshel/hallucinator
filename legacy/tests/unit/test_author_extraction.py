"""Tests for extract_authors_from_reference() function."""

import pytest
from check_hallucinated_references import extract_authors_from_reference


class TestExtractAuthorsIEEE:
    """Tests for IEEE format author extraction."""

    def test_ieee_two_authors(self, ieee_reference):
        """Test IEEE format with two authors."""
        authors = extract_authors_from_reference(ieee_reference)
        assert len(authors) == 2
        assert any("Smith" in a for a in authors)
        assert any("Jones" in a for a in authors)

    def test_ieee_multiple_authors(self):
        """Test IEEE format with multiple authors."""
        ref = 'M. Chen, B. Lee, C. Wang, and D. Kim, "Transformer Models," IEEE Trans., 2022.'
        authors = extract_authors_from_reference(ref)
        assert len(authors) == 4
        assert any("Chen" in a for a in authors)
        assert any("Lee" in a for a in authors)
        assert any("Wang" in a for a in authors)
        assert any("Kim" in a for a in authors)

    def test_ieee_single_author(self):
        """Test IEEE format with single author."""
        ref = 'A. Brown, "A Survey of Methods," in Proc. ICML, 2021.'
        authors = extract_authors_from_reference(ref)
        assert len(authors) == 1
        assert any("Brown" in a for a in authors)


class TestExtractAuthorsACM:
    """Tests for ACM format author extraction."""

    def test_acm_three_authors(self, acm_reference):
        """Test ACM format with three authors."""
        authors = extract_authors_from_reference(acm_reference)
        assert len(authors) >= 2  # May vary based on parsing
        assert any("Smith" in a for a in authors)
        assert any("Jones" in a for a in authors)

    def test_acm_two_authors(self):
        """Test ACM format with two authors."""
        ref = 'Maria Garcia and Carlos Rodriguez. 2022. Neural Networks. In CHI.'
        authors = extract_authors_from_reference(ref)
        assert len(authors) >= 2
        assert any("Garcia" in a for a in authors)
        assert any("Rodriguez" in a for a in authors)


class TestExtractAuthorsUSENIX:
    """Tests for USENIX format author extraction."""

    def test_usenix_two_authors(self, usenix_reference):
        """Test USENIX format with two authors."""
        authors = extract_authors_from_reference(usenix_reference)
        assert len(authors) >= 2
        assert any("Smith" in a for a in authors)
        assert any("Jones" in a for a in authors)

    def test_usenix_single_author(self):
        """Test USENIX format with single author."""
        ref = 'Robert Chen. Secure Systems Design. In USENIX ATC, 2022.'
        authors = extract_authors_from_reference(ref)
        assert len(authors) >= 1
        assert any("Chen" in a for a in authors)


class TestExtractAuthorsAAAI:
    """Tests for AAAI format author extraction."""

    def test_aaai_three_authors(self, aaai_reference):
        """Test AAAI format with three authors."""
        authors = extract_authors_from_reference(aaai_reference)
        assert len(authors) == 3
        assert any("Smith" in a for a in authors)
        assert any("Jones" in a for a in authors)
        assert any("Williams" in a for a in authors)

    def test_aaai_with_middle_initials(self):
        """Test AAAI format with multiple initials."""
        ref = 'Bail, C. A.; Argyle, L. P.; and Brown, T. W. 2022. Exposure to Views. PNAS.'
        authors = extract_authors_from_reference(ref)
        assert len(authors) == 3
        assert any("Bail" in a for a in authors)
        assert any("Argyle" in a for a in authors)
        assert any("Brown" in a for a in authors)


class TestExtractAuthorsCompoundSurnames:
    """Tests for compound surname handling."""

    def test_van_prefix(self):
        """Test Van prefix in surname."""
        ref = 'Van Bavel, J.; Jones, A. 2023. Social Identity. PNAS.'
        authors = extract_authors_from_reference(ref)
        # Should recognize Van Bavel as compound name
        assert any("Bavel" in a for a in authors)

    def test_hyphenated_surname(self):
        """Test hyphenated surname."""
        ref = 'Camacho-Collados, J. and Pilehvar, M. T. 2020. Text Preprocessing. ACL.'
        authors = extract_authors_from_reference(ref)
        assert any("Camacho" in a or "Collados" in a for a in authors)

    def test_del_prefix(self):
        """Test Del prefix in surname."""
        ref = 'Del Vicario, M.; Bessi, A. 2016. Misinformation. PNAS.'
        authors = extract_authors_from_reference(ref)
        assert any("Vicario" in a for a in authors)


class TestExtractAuthorsEmDash:
    """Tests for em-dash handling (same authors as previous)."""

    def test_em_dash_double(self, em_dash_reference):
        """Test double em-dash pattern."""
        authors = extract_authors_from_reference(em_dash_reference)
        assert authors == ['__SAME_AS_PREVIOUS__']

    def test_em_dash_triple(self):
        """Test triple em-dash pattern."""
        ref = '———, "Another Paper," in Proc. NeurIPS, 2022.'
        authors = extract_authors_from_reference(ref)
        assert authors == ['__SAME_AS_PREVIOUS__']

    def test_em_dash_hyphen(self):
        """Test hyphen-based em-dash pattern."""
        ref = '---, "Another Paper," in Proc. ICML, 2023.'
        authors = extract_authors_from_reference(ref)
        assert authors == ['__SAME_AS_PREVIOUS__']


class TestExtractAuthorsEtAl:
    """Tests for et al. handling."""

    def test_et_al_removed(self):
        """Test that et al. is removed from author list."""
        ref = 'Smith, J. et al. 2023. Large-Scale Analysis. Nature.'
        authors = extract_authors_from_reference(ref)
        # et al. should not be in authors list
        assert not any("et al" in a.lower() for a in authors)
        # But Smith should be there
        assert any("Smith" in a for a in authors)

    def test_et_al_with_period(self):
        """Test et al. with period."""
        ref = 'A. Jones et al., "Distributed Computing," in SOSP, 2022.'
        authors = extract_authors_from_reference(ref)
        assert not any("et al" in a.lower() for a in authors)
        assert any("Jones" in a for a in authors)


class TestExtractAuthorsEdgeCases:
    """Tests for edge cases in author extraction."""

    def test_empty_string(self):
        """Test empty string input."""
        authors = extract_authors_from_reference("")
        assert authors == []

    def test_no_authors(self):
        """Test reference with no clear authors."""
        ref = '"A Title Without Authors," 2023.'
        authors = extract_authors_from_reference(ref)
        assert isinstance(authors, list)

    def test_ampersand(self):
        """Test ampersand as author separator."""
        ref = 'J. Smith & A. Jones, "Title," in Proc., 2023.'
        authors = extract_authors_from_reference(ref)
        assert any("Smith" in a for a in authors)
        assert any("Jones" in a for a in authors)

    def test_smart_quotes(self):
        """Test with smart quotes."""
        ref = 'J. Smith, \u201cTitle with Smart Quotes,\u201d in Proc., 2023.'
        authors = extract_authors_from_reference(ref)
        assert any("Smith" in a for a in authors)

    def test_max_authors_limit(self):
        """Test that author list is capped at 15."""
        # Build a reference with many authors
        names = [f"Author{i}, A." for i in range(20)]
        ref = "; ".join(names) + ". 2023. Title. Venue."
        authors = extract_authors_from_reference(ref)
        assert len(authors) <= 15

    def test_numbers_in_text_not_authors(self):
        """Test that numbers are not extracted as authors."""
        ref = 'J. Smith, "Title," vol. 15, no. 3, 2023.'
        authors = extract_authors_from_reference(ref)
        # Numbers should not be in authors
        assert not any(a.isdigit() for a in authors)
