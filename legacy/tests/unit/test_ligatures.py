"""Tests for expand_ligatures() function."""

import pytest
from check_hallucinated_references import expand_ligatures


class TestExpandLigatures:
    """Tests for typographic ligature expansion."""

    def test_fi_ligature(self):
        """Test ﬁ (fi) ligature expansion."""
        assert expand_ligatures("ﬁle") == "file"
        assert expand_ligatures("ﬁne") == "fine"
        assert expand_ligatures("deﬁnition") == "definition"

    def test_fl_ligature(self):
        """Test ﬂ (fl) ligature expansion."""
        assert expand_ligatures("ﬂow") == "flow"
        assert expand_ligatures("ﬂuid") == "fluid"
        assert expand_ligatures("inﬂuence") == "influence"

    def test_ff_ligature(self):
        """Test ﬀ (ff) ligature expansion."""
        assert expand_ligatures("eﬀect") == "effect"
        assert expand_ligatures("aﬀord") == "afford"
        assert expand_ligatures("diﬀerent") == "different"

    def test_ffi_ligature(self):
        """Test ﬃ (ffi) ligature expansion."""
        assert expand_ligatures("eﬃcient") == "efficient"
        assert expand_ligatures("oﬃce") == "office"
        assert expand_ligatures("suﬃx") == "suffix"

    def test_ffl_ligature(self):
        """Test ﬄ (ffl) ligature expansion."""
        assert expand_ligatures("aﬄuent") == "affluent"
        assert expand_ligatures("eﬄuent") == "effluent"
        assert expand_ligatures("raﬄe") == "raffle"

    def test_st_ligature_long_s(self):
        """Test ﬅ (long s + t) ligature expansion."""
        assert expand_ligatures("ﬅrange") == "strange"
        assert expand_ligatures("faﬅ") == "fast"

    def test_st_ligature(self):
        """Test ﬆ (st) ligature expansion."""
        assert expand_ligatures("teﬆ") == "test"
        assert expand_ligatures("laﬆ") == "last"

    def test_mixed_ligatures(self, ligature_text):
        """Test text with multiple different ligatures."""
        result = expand_ligatures(ligature_text)
        assert "fine" in result
        assert "file" in result
        assert "fluid" in result
        # Note: ﬀ ligature produces "ff" not "eff" prefix
        assert "ffects" in result  # from ﬀects
        assert "efficient" in result
        assert "effluent" in result
        assert "strange" in result
        assert "stuff" in result
        # No ligatures should remain
        assert "\ufb00" not in result  # ff
        assert "\ufb01" not in result  # fi
        assert "\ufb02" not in result  # fl
        assert "\ufb03" not in result  # ffi
        assert "\ufb04" not in result  # ffl
        assert "\ufb05" not in result  # st (long s)
        assert "\ufb06" not in result  # st

    def test_no_ligatures(self):
        """Test text without any ligatures (should be unchanged)."""
        text = "This is normal text without ligatures."
        assert expand_ligatures(text) == text

    def test_empty_string(self):
        """Test empty string input."""
        assert expand_ligatures("") == ""

    def test_ligature_at_word_boundary(self):
        """Test ligatures at start/end of words."""
        assert expand_ligatures("ﬁ") == "fi"
        assert expand_ligatures("ﬂ") == "fl"

    def test_multiple_same_ligatures(self):
        """Test multiple occurrences of the same ligature."""
        assert expand_ligatures("ﬁle and ﬁne and ﬁnish") == "file and fine and finish"

    def test_adjacent_ligatures(self):
        """Test adjacent ligatures in text."""
        # Unusual but possible
        assert expand_ligatures("ﬁﬂ") == "fifl"
