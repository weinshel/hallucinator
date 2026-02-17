"""Tests for fix_hyphenation() function."""

import pytest
from check_hallucinated_references import fix_hyphenation, COMPOUND_SUFFIXES


class TestFixHyphenation:
    """Tests for PDF hyphenation fixing."""

    def test_syllable_break_with_space(self):
        """Test syllable break hyphen removal (hyphen + space)."""
        assert fix_hyphenation("detec- tion") == "detection"
        assert fix_hyphenation("infor- mation") == "information"
        assert fix_hyphenation("compu- tation") == "computation"

    def test_syllable_break_with_newline(self):
        """Test syllable break hyphen removal (hyphen + newline)."""
        assert fix_hyphenation("detec-\ntion") == "detection"
        assert fix_hyphenation("infor-\nmation") == "information"

    def test_compound_word_preserved(self):
        """Test that compound words with hyphens are preserved."""
        # All COMPOUND_SUFFIXES should be preserved
        assert fix_hyphenation("human- centered") == "human-centered"
        assert fix_hyphenation("data- driven") == "data-driven"
        assert fix_hyphenation("task- specific") == "task-specific"
        assert fix_hyphenation("domain- agnostic") == "domain-agnostic"
        assert fix_hyphenation("language- independent") == "language-independent"
        assert fix_hyphenation("fine- grained") == "fine-grained"

    def test_compound_based(self):
        """Test -based compounds are preserved."""
        assert fix_hyphenation("learning- based") == "learning-based"
        assert fix_hyphenation("rule- based") == "rule-based"
        assert fix_hyphenation("model- based") == "model-based"

    def test_compound_aware(self):
        """Test -aware compounds are preserved."""
        assert fix_hyphenation("context- aware") == "context-aware"
        assert fix_hyphenation("privacy- aware") == "privacy-aware"

    def test_compound_oriented(self):
        """Test -oriented compounds are preserved."""
        assert fix_hyphenation("object- oriented") == "object-oriented"
        assert fix_hyphenation("user- oriented") == "user-oriented"

    def test_compound_free(self):
        """Test -free compounds are preserved."""
        assert fix_hyphenation("error- free") == "error-free"
        assert fix_hyphenation("noise- free") == "noise-free"

    def test_compound_scale_level(self):
        """Test -scale and -level compounds are preserved."""
        assert fix_hyphenation("large- scale") == "large-scale"
        assert fix_hyphenation("sentence- level") == "sentence-level"

    def test_compound_shot(self):
        """Test -shot compounds are preserved."""
        assert fix_hyphenation("zero- shot") == "zero-shot"
        assert fix_hyphenation("few- shot") == "few-shot"

    def test_compound_step_time(self):
        """Test -step and -time compounds are preserved."""
        assert fix_hyphenation("multi- step") == "multi-step"
        assert fix_hyphenation("real- time") == "real-time"

    def test_compound_modal_agent(self):
        """Test -modal and -agent compounds are preserved."""
        assert fix_hyphenation("multi- modal") == "multi-modal"
        assert fix_hyphenation("multi- agent") == "multi-agent"

    def test_compound_source_domain(self):
        """Test -source and -domain compounds are preserved."""
        assert fix_hyphenation("open- source") == "open-source"
        assert fix_hyphenation("cross- domain") == "cross-domain"

    def test_mixed_text(self, hyphenated_text):
        """Test mixed text with both syllable breaks and compound words."""
        result = fix_hyphenation(hyphenated_text)
        # Syllable breaks should be joined
        assert "detection" in result
        assert "techniques" in result
        # Compound words should be preserved
        assert "human-centered" in result

    def test_no_hyphenation(self):
        """Test text without hyphenation (should be unchanged)."""
        text = "This is normal text without any hyphenation."
        assert fix_hyphenation(text) == text

    def test_empty_string(self):
        """Test empty string input."""
        assert fix_hyphenation("") == ""

    def test_multiple_hyphens_in_text(self):
        """Test text with multiple hyphenation issues."""
        text = "A human- centered detec- tion method for multi- agent systems."
        result = fix_hyphenation(text)
        assert "human-centered" in result
        assert "detection" in result
        assert "multi-agent" in result

    def test_all_compound_suffixes_exist(self):
        """Verify all expected compound suffixes are in the set."""
        expected = [
            'centered', 'based', 'driven', 'aware', 'oriented', 'specific',
            'related', 'dependent', 'independent', 'like', 'free', 'friendly',
            'rich', 'poor', 'scale', 'level', 'order', 'class', 'type', 'style',
            'wise', 'fold', 'shot', 'step', 'time', 'world', 'source', 'domain',
            'task', 'modal', 'intensive', 'efficient', 'agnostic', 'invariant',
            'sensitive', 'grained', 'agent', 'site',
        ]
        for suffix in expected:
            assert suffix in COMPOUND_SUFFIXES, f"Missing compound suffix: {suffix}"

    def test_compound_with_punctuation(self):
        """Test compound words followed by punctuation."""
        assert fix_hyphenation("human- centered,") == "human-centered,"
        assert fix_hyphenation("data- driven.") == "data-driven."
        assert fix_hyphenation("task- specific;") == "task-specific;"

    def test_case_sensitivity(self):
        """Test that compound detection is case-insensitive."""
        assert fix_hyphenation("Human- Centered") == "Human-Centered"
        assert fix_hyphenation("DATA- DRIVEN") == "DATA-DRIVEN"
